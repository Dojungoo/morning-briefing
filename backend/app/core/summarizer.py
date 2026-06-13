"""Turn raw headlines + indicators into an edited briefing.

The persona + `#` delimiter + TOPFEC prompt asks the managed LLM (coders.kr
`type: llm` proxy) to dedupe, rank and rewrite the crawled headlines into a
consistent analyst voice, add a per-section read, and coin the single
'오늘의 인사이트 한 줄'. The model's identity-bearing call is billed to the
visitor's pool, so we forward `x-coders-user` (PLATFORM.md §8).

If the platform LLM isn't configured (local dev) or the call fails, a
deterministic composer assembles a serviceable briefing from the same raw
items, so the product never shows a blank page.
"""

from __future__ import annotations

import json
import logging
import re
from uuid import UUID

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

PERSONA = (
    "당신은 보험중개·리스크 평가 실무 15년 차 애널리스트입니다. "
    "보험사 CFO와 대체투자 심사역이 출근길 3분 안에 읽을 수 있도록, "
    "과장 없이 핵심만 짚는 '딜북(Dealbook)' 스타일의 절제된 문체로 씁니다."
)

# TOPFEC = Task / Output / Persona / Format / Example / Constraint.
PROMPT_TEMPLATE = """\
# Persona
{persona}

# Task
아래 #INPUT 의 분류별 헤드라인과 시장지표를 바탕으로, 보험·대체투자(PF) 실무자용
'오늘의 모닝 브리핑'을 편집한다. 중복·홍보성 기사는 제거하고, 같은 사안은 하나로
묶어 사실 중심으로 재서술한다.

# Output
- 각 섹션마다 가장 중요한 항목 3~4개를 선정한다.
- 각 항목은 입력 항목의 id(정수)를 그대로 싣고, headline(원문을 다듬은 한 줄)과
  summary(1~2문장, 실무적 함의 포함)만 작성한다. source·url 은 출력하지 않는다
  (서버가 id 로 원본을 연결한다).
- 모든 섹션을 관통하는 '오늘의 인사이트 한 줄'(insight)을 한 문장으로 작성한다.
- 시장지표는 한 줄 코멘트(market_note)로 해석한다.

# Format
반드시 아래 JSON 스키마만 출력한다. 코드블록·설명·서론 금지.
{{
  "insight": "문자열 한 문장",
  "market_note": "지표 해석 한 문장",
  "sections": [
    {{"key":"insurance","items":[{{"id":0,"headline":"","summary":""}}]}},
    {{"key":"alt_pf","items":[...]}},
    {{"key":"regulation","items":[...]}}
  ]
}}

# Constraint
- 한국어. 추측·과장·투자권유 금지. 입력에 없는 사실을 지어내지 않는다.
- id 는 반드시 입력 #INPUT 에 존재하는 정수만 사용한다(새 id 를 만들지 않는다).
- 헤드라인이 부족한 섹션은 있는 만큼만 채운다.

#INPUT
{payload}
"""


def _payload(sections: list[dict], indicators: list[dict]) -> str:
    # Give every item a per-section id; the model echoes ids, not URLs, so the
    # output stays small (no 200-char Google-News links to copy = no truncation
    # and no link corruption). source + url are rejoined from the id in _merge.
    compact_sections = [
        {
            "key": s["key"],
            "title": s["title"],
            "items": [
                {
                    "id": i,
                    "headline": it["headline"],
                    "desc": (it.get("summary") or "")[:160],
                    "source": it.get("source", ""),
                }
                for i, it in enumerate(s["items"])
            ],
        }
        for s in sections
    ]
    return json.dumps(
        {"headlines": compact_sections, "indicators": indicators},
        ensure_ascii=False,
        indent=2,
    )


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    # Strip a ```json … ``` fence if the model added one despite instructions.
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    start = text.find("{")
    if start == -1:
        return None
    # Try the greedy outer span first, then walk the closing braces inward so a
    # bit of trailing prose after the JSON object doesn't break parsing.
    candidates = [text.rfind("}")]
    candidates += [m.start() for m in re.finditer(r"\}", text)][::-1]
    for end in candidates:
        if end is None or end <= start:
            continue
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            continue
    return None


async def _call_llm(prompt: str, coders_user: UUID | None) -> dict | None:
    base = (settings.anthropic_base_url or "").rstrip("/")
    headers = {
        "x-api-key": settings.anthropic_api_key or "",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    # Forward identity so the call bills the visitor's pool, not anonymous.
    if coders_user:
        headers["x-coders-user"] = str(coders_user)
    body = {
        "model": settings.llm_model,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}],
    }
    # Runs inside a detached background task (not the request path), so it's not
    # bound by the gate's ~50s cap — give the model room to finish.
    async with httpx.AsyncClient(timeout=150.0) as client:
        r = await client.post(f"{base}/v1/messages", headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
    if data.get("stop_reason") == "max_tokens":
        logger.warning("LLM hit max_tokens — output may be truncated")
    parts = data.get("content") or []
    text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
    return _extract_json(text)


def _merge(raw_sections: list[dict], edited: dict) -> tuple[list[dict], str]:
    """Overlay the model's edited items onto our section scaffold.

    The model returns each item's input id + the rewritten headline/summary; we
    rejoin source + url from the original raw item by that id (the model never
    handles the long URLs, so they can't be corrupted or truncated).
    """
    by_key = {s["key"]: s.get("items", []) for s in edited.get("sections", [])}
    out: list[dict] = []
    for s in raw_sections:
        raw_items = s["items"]
        items = by_key.get(s["key"]) or []
        norm = []
        for it in items:
            headline = (it.get("headline") or "").strip()
            if not headline:
                continue
            idx = it.get("id")
            orig = (
                raw_items[idx]
                if isinstance(idx, int) and 0 <= idx < len(raw_items)
                else {}
            )
            norm.append(
                {
                    "headline": headline,
                    "summary": (it.get("summary") or "").strip(),
                    "source": (orig.get("source") or "").strip(),
                    "url": (orig.get("url") or "").strip(),
                }
            )
        # If the model dropped a section, fall back to its raw headlines.
        if not norm:
            norm = _fallback_items(s["items"])
        out.append(
            {
                "key": s["key"],
                "title": s["title"],
                "subtitle": s["subtitle"],
                "items": norm,
            }
        )
    note = (edited.get("market_note") or "").strip()
    return out, note


def _fallback_items(raw_items: list[dict], limit: int = 4) -> list[dict]:
    out = []
    for it in raw_items[:limit]:
        out.append(
            {
                "headline": it.get("headline", "").strip(),
                "summary": (it.get("summary") or "").strip()[:200],
                "source": it.get("source", "").strip(),
                "url": it.get("url", "").strip(),
            }
        )
    return out


def _fallback_insight(sections: list[dict], indicators: list[dict]) -> str:
    lead = ""
    for s in sections:
        if s["items"]:
            lead = s["items"][0].get("headline", "")
            break
    if indicators:
        ind = indicators[0]
        market = f"{ind['label']} {ind['value']}({ind['change_pct']})"
    else:
        market = "시장지표"
    if lead:
        return f"{market} 흐름 속, '{lead}'에 주목할 만한 하루."
    return f"오늘의 {market}를 중심으로 보험·대체투자 동향을 점검하세요."


def compose_fallback(
    raw_sections: list[dict], indicators: list[dict]
) -> dict:
    sections = [
        {
            "key": s["key"],
            "title": s["title"],
            "subtitle": s["subtitle"],
            "items": _fallback_items(s["items"]),
        }
        for s in raw_sections
    ]
    return {
        "insight": _fallback_insight(sections, indicators),
        "market_note": "",
        "sections": sections,
        "model": "fallback",
    }


async def summarize(
    raw_sections: list[dict],
    indicators: list[dict],
    coders_user: UUID | None,
) -> dict:
    """Return {insight, market_note, sections, model}."""
    if not settings.llm_enabled:
        logger.warning(
            "LLM disabled (base_url_set=%s api_key_set=%s) — using fallback",
            bool(settings.anthropic_base_url),
            bool(settings.anthropic_api_key),
        )
        return compose_fallback(raw_sections, indicators)

    prompt = PROMPT_TEMPLATE.format(
        persona=PERSONA, payload=_payload(raw_sections, indicators)
    )
    try:
        edited = await _call_llm(prompt, coders_user)
    except httpx.HTTPStatusError as exc:
        body = exc.response.text[:500] if exc.response is not None else ""
        logger.warning(
            "LLM call HTTP %s using model=%s — %s",
            exc.response.status_code if exc.response is not None else "?",
            settings.llm_model,
            body,
        )
        edited = None
    except Exception:
        logger.exception("LLM call failed (model=%s) — using fallback", settings.llm_model)
        edited = None
    if not edited:
        logger.warning("LLM returned no usable JSON — using fallback")
        return compose_fallback(raw_sections, indicators)

    sections, note = _merge(raw_sections, edited)
    insight = (edited.get("insight") or "").strip() or _fallback_insight(
        sections, indicators
    )
    return {
        "insight": insight,
        "market_note": note,
        "sections": sections,
        "model": settings.llm_model,
    }
