# 생성형 이미지(7부) 프롬프트 팩 — AI 보험·대체투자 모닝 브리핑

브랜드 톤: 딥 머룬(#7A2E3A) + 네이비, 절제된 편집·"딜북(Dealbook)" 인텔리전스.
모든 아이콘은 **같은 스타일/색/선 굵기**로 만들어 세트로 보이게 한다.

## 배경 가이드 (중요)
- **로고·섹션 아이콘**: 투명배경이 안 되면 **흰 배경으로 생성해도 됩니다.** UI 슬롯에 흰 타일 배경을 깔아 라이트/다크 양쪽에서 깔끔한 칩으로 보입니다.
- **히어로 배너**: 흰 배경 대신 **딥 네이비/머룬 어두운 배경**으로 요청하세요(다크 모드에서 흰 밴드가 튀는 것 방지).

생성 후 파일을 아래 경로에 넣으면 사이트에 자동 반영(없으면 폴백):
- 로고 → `frontend/public/brand/logo.png` (256×256, 투명배경)
- 히어로 → `frontend/public/brand/hero.png` (1600×400)
- 섹션 아이콘 → `frontend/public/sections/{insurance,alt_pf,regulation,markets}.png` (128×128)

---

## 1) 로고 (256×256, 투명배경, 정사각)

**DALL·E**
> A minimalist flat vector logo mark for a financial morning-briefing service.
> A clean monoline rising line-chart that subtly forms a sunrise over a horizon,
> combined with a small shield silhouette suggesting insurance and trust.
> Two-tone deep maroon (#7A2E3A) and navy, geometric, balanced, no text,
> centered, generous padding, transparent background, crisp edges, app-icon style.

**Midjourney**
> minimalist flat vector logo, monoline rising line chart forming a sunrise over a
> shield silhouette, insurance + finance, deep maroon and navy, geometric, no text,
> transparent background, app icon --ar 1:1 --style raw --v 6

---

## 2) 히어로 배너 (1600×400, 와이드)

**DALL·E**
> A wide, editorial hero banner for an insurance & alternative-investment market
> intelligence briefing. Abstract Seoul financial-district skyline at dawn,
> soft morning light, with subtle translucent line-chart and data-grid overlays.
> Muted deep maroon and navy palette, calm and premium, lots of clean negative
> space on the left for headline text, no words, no logos, cinematic but minimal.

**Midjourney**
> editorial wide hero banner, abstract Seoul financial district skyline at dawn,
> translucent line chart and data grid overlay, muted deep maroon and navy,
> premium minimal, large clean negative space on left, no text --ar 4:1 --style raw --v 6

---

## 3) 섹션 아이콘 4종 (각 128×128) — 동일 세트 스타일

공통 접두(모든 아이콘에 붙여 일관성 유지):
> flat two-tone line icon, deep maroon (#7A2E3A) and navy, 2px rounded strokes,
> centered on transparent background, simple, modern, consistent icon-set style, no text —

- **보험업계 (insurance.png)**: `… a shield with a small umbrella inside, representing insurance protection`
- **대체투자·PF (alt_pf.png)**: `… a construction crane beside a stack of coins and a building, representing infrastructure & project finance`
- **규제·리스크 (regulation.png)**: `… a balanced scale of justice over a document, representing financial regulation and risk`
- **금융지표 (markets.png)**: `… an upward candlestick chart with a trend line, representing market indicators`

> 팁: 미드저니는 4종을 만들 때 같은 시드/스타일 레퍼런스(`--sref`)를 재사용하면 세트 통일감↑.
> 투명배경이 어려우면 흰 배경으로 생성 후 remove.bg 등으로 배경 제거.

---

## 4) 파비콘(선택)
로고(1)를 32×32로 축소해 `frontend/app/favicon.ico`로 저장(또는 favicon 변환 사이트 사용).

---

---

## 나노 바나나(Gemini 2.5 Flash Image)용 — 대화형, 세트 일관성 강점

**0) 스타일 앵커 (대화 처음 1회)**
> I'm designing a visual identity for a financial "morning briefing" web service about
> insurance and alternative investment. Brand style: minimal, premium, editorial
> "dealbook" feel. Palette: deep maroon (#7A2E3A) and navy, on clean white or
> transparent. Flat vector, thin rounded strokes, lots of negative space, no text.
> Keep this style consistent for every asset I ask for next.

**1) 로고** — `square 1:1 logo mark, transparent PNG`: monoline rising line-chart forming a sunrise over a shield silhouette (insurance + trust), maroon+navy, no text.

**2) 히어로** — `wide 4:1 banner ~1600×400`: abstract Seoul financial skyline at dawn + translucent chart/data-grid overlay, maroon+navy, big clean negative space on the LEFT, no text.

**3) 아이콘 4종 (연속 대화)** — 1번 생성 후 2~4번은 "same line weight/color/style as that icon":
- insurance: shield with a small umbrella inside
- alt_pf: construction crane + building + stack of coins
- regulation: balanced scale of justice over a document
- markets: upward candlestick chart with a trend line

팁: 투명배경 안 나오면 "make the background fully transparent (PNG with alpha)"; 첫 아이콘을 업로드해 "match this exact style"; 색 흐리면 "#7A2E3A" 헥스 직접 지정.

---

## 보고서용 캡션(레포트에 그대로 인용 가능)
"서비스 로고·히어로 배너·4개 섹션 아이콘을 생성형 이미지 도구(DALL·E/Midjourney, 7부)로
브랜드 톤(딥 머룬·네이비)에 맞춰 일괄 생성하여 UI에 적용, 시각적 완성도와 브랜드 일관성을 확보."
