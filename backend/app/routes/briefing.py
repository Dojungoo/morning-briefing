"""Morning-briefing endpoints.

GET  /api/briefing/latest   — public; the most recent issue (or null).
GET  /api/briefing/history  — public; lightweight list of past issues.
GET  /api/briefing/{id}     — public; one issue by id.
POST /api/briefing/generate — auth-required; crawl → summarise → store.

Reads are cheap DB hits served to everyone. Only generation does the
expensive crawl + LLM work, and it's a POST, so the platform gate already
requires a signed-in visitor (PLATFORM.md §2) — whose pool the LLM call is
billed against.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.collectors import fetch_headlines, fetch_indicators
from app.core.database import AsyncSessionLocal, get_session
from app.core.identity import require_identity
from app.core.summarizer import selftest as llm_selftest
from app.core.summarizer import summarize
from app.models import Briefing
from app.routes.users import upsert_local_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/briefing", tags=["briefing"])

KST = timezone(timedelta(hours=9))

# Hold strong refs to detached generation tasks so the event loop doesn't
# garbage-collect them mid-flight (asyncio only keeps weak refs).
_background_tasks: set[asyncio.Task] = set()


class BriefingOut(BaseModel):
    id: str
    status: str
    issue_date: str
    insight: str
    sections: list
    indicators: list
    source_count: int
    model: str
    author_name: str
    created_at: str


class BriefingSummary(BaseModel):
    id: str
    issue_date: str
    insight: str
    created_at: str


def _to_out(b: Briefing) -> BriefingOut:
    return BriefingOut(
        id=str(b.id),
        status=b.status,
        issue_date=b.issue_date.isoformat(),
        insight=b.insight,
        sections=b.sections,
        indicators=b.indicators,
        source_count=b.source_count,
        model=b.model,
        author_name=b.author.display_name if b.author else "",
        created_at=b.created_at.isoformat(),
    )


@router.get("/latest", response_model=BriefingOut | None)
async def latest(session: AsyncSession = Depends(get_session)) -> BriefingOut | None:
    res = await session.execute(
        select(Briefing)
        .options(selectinload(Briefing.author))
        .where(Briefing.status == "ready")
        .order_by(desc(Briefing.created_at))
        .limit(1)
    )
    b = res.scalar_one_or_none()
    return _to_out(b) if b else None


@router.get("/history", response_model=list[BriefingSummary])
async def history(
    session: AsyncSession = Depends(get_session),
) -> list[BriefingSummary]:
    res = await session.execute(
        select(Briefing)
        .where(Briefing.status == "ready")
        .order_by(desc(Briefing.created_at))
        .limit(30)
    )
    return [
        BriefingSummary(
            id=str(b.id),
            issue_date=b.issue_date.isoformat(),
            insight=b.insight,
            created_at=b.created_at.isoformat(),
        )
        for b in res.scalars().all()
    ]


async def _run_generation(briefing_id: UUID, coders_id: UUID) -> None:
    """Crawl → summarise → fill in the pending briefing, detached from the
    request that created it.

    The crawl + LLM call can run well past the platform's ~50s request cap
    (PLATFORM.md §5d), so this runs as a background task with its own DB
    session. The browser's polling of GET /briefing/{id} keeps the pod warm
    until it finishes (PLATFORM.md §6). Any failure flips the row to
    "failed" so the client stops polling and shows an error.
    """
    try:
        raw_sections = await fetch_headlines()
        indicators = await fetch_indicators()
        source_count = sum(len(s["items"]) for s in raw_sections)

        edited = await summarize(raw_sections, indicators, coders_id)

        sections = list(edited["sections"])
        # 4th editorial section: the markets read sits alongside the indicators.
        sections.append(
            {
                "key": "markets",
                "title": "금융지표",
                "subtitle": "국내외 금리·환율·증시",
                "note": edited.get("market_note", ""),
                "items": [],
            }
        )

        async with AsyncSessionLocal() as session:
            async with session.begin():
                b = await session.get(Briefing, briefing_id)
                if b is None:
                    return
                b.insight = edited["insight"]
                b.sections = sections
                b.indicators = indicators
                b.source_count = source_count
                b.model = edited.get("model", "")
                b.status = "ready"
    except Exception:
        logger.exception("briefing generation failed for %s", briefing_id)
        async with AsyncSessionLocal() as session:
            async with session.begin():
                b = await session.get(Briefing, briefing_id)
                if b is not None:
                    b.status = "failed"


@router.post("/generate", response_model=BriefingOut, status_code=202)
async def generate(coders_id: UUID = Depends(require_identity)) -> BriefingOut:
    """Persist a 'pending' briefing, kick off generation, return immediately.

    Generation (crawl + LLM) can exceed the platform's ~50s request cap
    (PLATFORM.md §5d), so we don't do it inline. We commit a pending row,
    spawn a detached task to fill it in, and hand the client an id to poll
    via GET /briefing/{id}.
    """
    # Own session, committed before we return, so the detached task (and the
    # client's first poll) are guaranteed to see the pending row.
    async with AsyncSessionLocal() as session:
        async with session.begin():
            user = await upsert_local_user(session, coders_id)
            briefing = Briefing(
                author_id=user.id,
                issue_date=datetime.now(KST).date(),
                insight="",
                sections=[],
                indicators=[],
                source_count=0,
                model="",
                status="pending",
            )
            session.add(briefing)
            await session.flush()
            briefing_id = briefing.id
        async with session.begin():
            res = await session.execute(
                select(Briefing)
                .options(selectinload(Briefing.author))
                .where(Briefing.id == briefing_id)
            )
            out = _to_out(res.scalar_one())

    task = asyncio.create_task(_run_generation(briefing_id, coders_id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return out


@router.get("/_llm-selftest")
async def llm_selftest_route() -> dict:
    """Temporary public diagnostic — one live LLM probe. Remove after fix."""
    return await llm_selftest()


@router.get("/{briefing_id}", response_model=BriefingOut)
async def get_one(
    briefing_id: UUID, session: AsyncSession = Depends(get_session)
) -> BriefingOut:
    res = await session.execute(
        select(Briefing)
        .options(selectinload(Briefing.author))
        .where(Briefing.id == briefing_id)
    )
    b = res.scalar_one_or_none()
    if b is None:
        raise HTTPException(404, "briefing not found")
    return _to_out(b)
