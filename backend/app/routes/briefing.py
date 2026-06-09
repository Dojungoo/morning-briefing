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

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.collectors import fetch_headlines, fetch_indicators
from app.core.database import get_session
from app.core.identity import require_identity
from app.core.summarizer import summarize
from app.models import Briefing
from app.routes.users import upsert_local_user

router = APIRouter(prefix="/api/briefing", tags=["briefing"])

KST = timezone(timedelta(hours=9))


class BriefingOut(BaseModel):
    id: str
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
        select(Briefing).order_by(desc(Briefing.created_at)).limit(30)
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


@router.post("/generate", response_model=BriefingOut, status_code=201)
async def generate(
    coders_id: UUID = Depends(require_identity),
    session: AsyncSession = Depends(get_session),
) -> BriefingOut:
    user = await upsert_local_user(session, coders_id)

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

    briefing = Briefing(
        author_id=user.id,
        issue_date=datetime.now(KST).date(),
        insight=edited["insight"],
        sections=sections,
        indicators=indicators,
        source_count=source_count,
        model=edited.get("model", ""),
    )
    session.add(briefing)
    await session.flush()

    res = await session.execute(
        select(Briefing)
        .options(selectinload(Briefing.author))
        .where(Briefing.id == briefing.id)
    )
    return _to_out(res.scalar_one())


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
