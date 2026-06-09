"""Source collectors for the morning briefing.

Two keyless, reliable feeds so the app works the moment it deploys:

* **Headlines** — Google News RSS, one query per editorial section. Google
  News is far more robust than scraping individual outlets (stable URL,
  Korean support, per-topic queries, source name embedded in each title).
* **Indicators** — Stooq's CSV quote endpoint (`/q/l/`), no API key, one
  request for the whole symbol list.

Everything is best-effort: a feed that 404s or times out is skipped, never
fatal. The summariser runs on whatever came back.
"""

from __future__ import annotations

import asyncio
from urllib.parse import quote
from xml.etree import ElementTree as ET

import httpx

# --- editorial sections fed by news -------------------------------------

# key, human title, subtitle, and the Google News query that fills it.
NEWS_SECTIONS: list[dict] = [
    {
        "key": "insurance",
        "title": "보험업계",
        "subtitle": "손해·생명보험 영업과 건전성 동향",
        "query": "보험사 OR 손해보험 OR 생명보험 OR IFRS17 OR K-ICS",
    },
    {
        "key": "alt_pf",
        "title": "대체투자·PF",
        "subtitle": "부동산PF·사모·인프라 대체투자 흐름",
        "query": "대체투자 OR 부동산PF OR 프로젝트파이낸싱 OR 사모펀드 OR 인프라투자",
    },
    {
        "key": "regulation",
        "title": "규제·리스크",
        "subtitle": "금융당국 정책과 감독 리스크",
        "query": "금융위원회 보험 OR 금융감독원 OR 보험 건전성 규제 OR 자본규제",
    },
]

# label, Yahoo Finance symbol, kind — order is the display order.
# kind ∈ {"index","fx","rate"} drives number formatting only.
INDICATOR_SYMBOLS: list[tuple[str, str, str]] = [
    ("코스피", "^KS11", "index"),
    ("코스닥", "^KQ11", "index"),
    ("나스닥", "^IXIC", "index"),
    ("S&P 500", "^GSPC", "index"),
    ("원/달러 환율", "KRW=X", "fx"),
    ("미 국채 10년", "^TNX", "rate"),
]

_UA = "Mozilla/5.0 (compatible; coders-briefing-bot/1.0)"
_GNEWS = "https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
_YF_HOSTS = ("query1.finance.yahoo.com", "query2.finance.yahoo.com")
_YF_PATH = "/v8/finance/chart/{sym}?range=5d&interval=1d"


def _clean(text: str | None) -> str:
    if not text:
        return ""
    # RSS descriptions arrive as escaped HTML; strip the most common tags.
    import re

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    return re.sub(r"\s+", " ", text).strip()


def _split_source(title: str) -> tuple[str, str]:
    """Google News titles end with ' - <source>'. Pull the source out."""
    if " - " in title:
        head, _, src = title.rpartition(" - ")
        if head and len(src) <= 40:
            return head.strip(), src.strip()
    return title.strip(), ""


async def _fetch_section_news(
    client: httpx.AsyncClient, section: dict, limit: int
) -> dict:
    url = _GNEWS.format(q=quote(section["query"]))
    items: list[dict] = []
    try:
        r = await client.get(url)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        for item in root.iter("item"):
            raw_title = (item.findtext("title") or "").strip()
            if not raw_title:
                continue
            headline, source = _split_source(raw_title)
            items.append(
                {
                    "headline": headline,
                    "summary": _clean(item.findtext("description"))[:400],
                    "source": source,
                    "url": (item.findtext("link") or "").strip(),
                    "published": (item.findtext("pubDate") or "").strip(),
                }
            )
            if len(items) >= limit:
                break
    except Exception:
        # Best-effort: an unreachable feed just yields an empty section.
        items = []
    return {
        "key": section["key"],
        "title": section["title"],
        "subtitle": section["subtitle"],
        "items": items,
    }


async def fetch_headlines(limit_per_section: int = 8) -> list[dict]:
    """Return the three news-fed sections, each with up to N raw headlines."""
    async with httpx.AsyncClient(
        timeout=12.0, headers={"User-Agent": _UA}, follow_redirects=True
    ) as client:
        return await asyncio.gather(
            *(
                _fetch_section_news(client, s, limit_per_section)
                for s in NEWS_SECTIONS
            )
        )


def _fmt_indicator(label: str, kind: str, price: float, prev: float) -> dict:
    change = price - prev
    pct = (change / prev * 100) if prev else 0.0
    direction = "up" if change > 0 else "down" if change < 0 else "flat"
    if kind == "fx":
        value = f"{price:,.1f}"
        change_txt = f"{change:+,.1f}"
    elif kind == "rate":
        value = f"{price:.3f}%"
        change_txt = f"{change:+.3f}%p"
    else:
        value = f"{price:,.2f}"
        change_txt = f"{change:+,.2f}"
    return {
        "label": label,
        "value": value,
        "change": change_txt,
        "change_pct": f"{pct:+.2f}%",
        "direction": direction,
    }


async def _fetch_one_indicator(
    client: httpx.AsyncClient, label: str, sym: str, kind: str
) -> dict | None:
    for host in _YF_HOSTS:
        url = f"https://{host}{_YF_PATH.format(sym=quote(sym, safe='^='))}"
        try:
            r = await client.get(url)
            if r.status_code != 200:
                continue
            meta = r.json()["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice")
            prev = meta.get("chartPreviousClose") or meta.get("previousClose")
            if price is None or prev is None:
                continue
            return _fmt_indicator(label, kind, float(price), float(prev))
        except Exception:
            continue
    return None


async def fetch_indicators() -> list[dict]:
    """Market indicators from Yahoo Finance (skips any that don't resolve)."""
    async with httpx.AsyncClient(
        timeout=12.0, headers={"User-Agent": _UA}, follow_redirects=True
    ) as client:
        results = await asyncio.gather(
            *(
                _fetch_one_indicator(client, label, sym, kind)
                for label, sym, kind in INDICATOR_SYMBOLS
            )
        )
    return [r for r in results if r]
