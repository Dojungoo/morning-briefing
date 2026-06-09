# AI 보험·대체투자 모닝 브리핑

보험·대체투자·프로젝트금융(PF) 실무자를 위한 **AI 마켓 인텔리전스 브리핑**.
일반 종합뉴스의 정보 과잉을 피해, 보험·대체투자라는 특정 수직 영역의 헤드라인과
금융지표를 자동으로 수집·요약해 **한 화면**으로 제공한다. 수집 → 요약 → 편집 →
출력의 전 과정을 자동화한 것이 핵심이다.

[coders.kr](https://coders.kr) 플랫폼 위에서 동작하며, 로그인/세션은 플랫폼 게이트가
처리한다(앱은 OAuth를 구현하지 않는다).

## 무엇을 하나

- **수집** — 섹션별 헤드라인을 Google News RSS에서, 국내외 금리·환율·증시
  지표를 Yahoo Finance에서 가져온다(둘 다 키 불필요, 실패해도 비치명적).
- **요약·편집** — 페르소나 + `#` 구분자 + TOPFEC 구조의 프롬프트로 플랫폼
  관리형 LLM(Claude)에 보내, 중복을 제거하고 일관된 '딜북' 톤으로 재서술한다.
- **출력** — 4개 섹션(보험업계 / 대체투자·PF / 규제·리스크 / 금융지표)과
  '오늘의 인사이트 한 줄'을 카드형 웹페이지로 렌더링한다.
- **보관** — 생성된 브리핑은 Postgres에 저장되어 공개 읽기는 값싼 DB 조회로
  처리되고, '지난 브리핑'에서 다시 볼 수 있다.

## 플랫폼 계약

요청이 앱에 도달하기 전에 플랫폼 게이트가 처리하는 것:

1. 방문자의 `coders_session` 쿠키 검증.
2. 유효하면 `X-Coders-User: <uuid>` 헤더를 찍어 전달.
3. 익명 사용자의 변경 요청(POST/PUT/PATCH/DELETE)은 앱에 닿기 전에 로그인으로 302.
4. 요청을 적절한 미터링 버킷에 기록.

따라서 앱 코드에서는:

- **`X-Coders-User`를 신뢰**한다(게이트가 위조 헤더를 제거함).
- **로그인 플로우를 만들지 않는다.** `mcp.coders.kr/sso/login`으로 링크.
- 신원이 필요한 동작은 **POST**로 둔다 — 브리핑 생성(`POST /api/briefing/generate`)이
  그 예로, 게이트가 자동으로 로그인을 요구한다.
- LLM 호출 시 `X-Coders-User`를 **전달**해 비용이 방문자 풀에 청구되게 한다
  (`backend/app/core/summarizer.py`, PLATFORM.md §8).

## 코드 구조

```
backend/
  app/
    core/
      collectors.py     Google News RSS + Yahoo Finance 지표 수집
      summarizer.py     페르소나 + TOPFEC 프롬프트로 LLM 편집(+오프라인 폴백)
      identity.py       require_identity / optional_identity
      config.py         DB + 관리형 LLM 설정
    routes/
      briefing.py       latest / history / generate / {id}
      users.py          /api/me — 최초 방문 시 로컬 유저 생성
    models.py           User + Briefing
frontend/
  components/
    Home.tsx            최신 브리핑 + 생성 버튼
    BriefingView.tsx    인사이트 + 지표 스트립 + 4개 섹션 카드
    Archive.tsx         지난 브리핑(펼침형)
  lib/api.ts            /api/briefing/* 클라이언트
coders.yaml             web + api + postgres + llm; mode: native
```

## API

| Method | Path | 설명 |
|---|---|---|
| GET  | `/api/briefing/latest`   | 최신 브리핑(없으면 null) — 공개 |
| GET  | `/api/briefing/history`  | 지난 브리핑 목록(최대 30) — 공개 |
| GET  | `/api/briefing/{id}`     | 특정 브리핑 — 공개 |
| POST | `/api/briefing/generate` | 수집→요약→저장(로그인 필요) |
| GET  | `/api/me`                | 로그인 방문자의 로컬 유저 |

## 로컬 개발

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://app:app@localhost:5432/app
DEV_FAKE_USER=00000000-0000-0000-0000-000000000001
# (ANTHROPIC_* 를 비워두면 요약은 결정적 폴백으로 동작)

docker compose up
```

`ANTHROPIC_BASE_URL` / `ANTHROPIC_API_KEY`를 비워두면 LLM 편집 없이 수집된
헤드라인·지표가 그대로 렌더링된다(폴백). 실제 AI 편집을 보려면 두 값을
Anthropic 호환 엔드포인트로 지정한다(`.env.example` 참고).

## 배포

이 저장소의 [`.mcp.json`](./.mcp.json)이 Claude Code를 coders.kr MCP 서버
(`https://mcp.coders.kr/mcp`)에 연결한다. 프로젝트를 처음 열면 Claude Code가
서버 승인과 1회 브라우저 로그인을 안내한다. 이후 Claude Code에서:

```
deploy https://github.com/<you>/<your-fork>
```

플랫폼이 `coders.yaml`을 읽어 web/api 이미지를 병렬 빌드하고, Postgres와 LLM
프록시를 테넌트 네임스페이스에 띄운 뒤 `<name>.coders.kr`에 게이트를 붙여 URL을
반환한다.

## 플랫폼 정책

[**PLATFORM.md**](./PLATFORM.md)에 런타임 동작(신원, 비용 모델, 쿼터 풀, 콜드
스타트, 관리형 LLM)이 정리되어 있다. LLM 토큰이 가장 비싼 축이므로(§8), 생성은
로그인 뒤로 게이트되고 프롬프트/출력은 간결하게 유지한다.

---

> 본 서비스는 정보 제공용이며 투자 권유가 아니다. 헤드라인 출처는 Google News,
> 금융지표 출처는 Yahoo Finance다.
