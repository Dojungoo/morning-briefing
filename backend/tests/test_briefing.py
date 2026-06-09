"""Tests for the briefing API + the offline fallback composer.

Network-free: generation hits live feeds (Google News / Stooq) so it is
exercised manually, not in CI. Here we cover the platform contract
(anonymous reads OK, anonymous generate 401, /api/me upsert) and the
deterministic fallback that runs when the managed LLM isn't configured.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.summarizer import compose_fallback

RAW_SECTIONS = [
    {
        "key": "insurance",
        "title": "보험업계",
        "subtitle": "손해·생명보험 동향",
        "items": [
            {
                "headline": "손보사 3분기 실적 개선",
                "summary": "주요 손보사 합산비율이 하락했다.",
                "source": "테스트뉴스",
                "url": "https://example.com/1",
            }
        ],
    },
    {
        "key": "alt_pf",
        "title": "대체투자·PF",
        "subtitle": "PF 동향",
        "items": [],
    },
    {
        "key": "regulation",
        "title": "규제·리스크",
        "subtitle": "감독 동향",
        "items": [],
    },
]
INDICATORS = [
    {
        "label": "코스피",
        "value": "2,700.00",
        "change": "+10.00",
        "change_pct": "+0.37%",
        "direction": "up",
        "date": "2026-06-09",
    }
]


def test_fallback_composer_shape() -> None:
    out = compose_fallback(RAW_SECTIONS, INDICATORS)
    assert out["model"] == "fallback"
    assert out["insight"]
    assert len(out["sections"]) == 3
    insurance = next(s for s in out["sections"] if s["key"] == "insurance")
    assert insurance["items"][0]["headline"] == "손보사 3분기 실적 개선"


@pytest.mark.asyncio
async def test_latest_is_null_for_fresh_db(client: AsyncClient) -> None:
    r = await client.get("/api/briefing/latest")
    assert r.status_code == 200
    assert r.json() is None


@pytest.mark.asyncio
async def test_history_empty_for_fresh_db(client: AsyncClient) -> None:
    r = await client.get("/api/briefing/history")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_anonymous_cannot_generate(client: AsyncClient) -> None:
    r = await client.post("/api/briefing/generate")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_lazily_creates_local_user(
    client: AsyncClient, signed_in_headers: dict[str, str]
) -> None:
    r = await client.get("/api/me", headers=signed_in_headers)
    assert r.status_code == 200
    me = r.json()
    assert me["coders_id"] == signed_in_headers["X-Coders-User"]
    assert me["display_name"].startswith("user-")
