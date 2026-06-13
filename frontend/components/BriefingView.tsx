"use client";

import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

import { cn } from "@/lib/utils";
import type { Briefing, BriefingSection, Indicator } from "@/lib/api";
import { AssetImg } from "./AssetImg";

const SECTION_ACCENT: Record<string, string> = {
  insurance: "bg-sky-500",
  alt_pf: "bg-violet-500",
  regulation: "bg-amber-500",
  markets: "bg-emerald-500",
};

function issueLabel(b: Briefing): string {
  const d = new Date(b.issue_date + "T00:00:00");
  const day = ["일", "월", "화", "수", "목", "금", "토"][d.getDay()];
  return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일 (${day})`;
}

export function BriefingView({ briefing }: { briefing: Briefing }) {
  return (
    <article className="space-y-10">
      <Insight briefing={briefing} />
      {briefing.indicators.length > 0 && (
        <IndicatorStrip indicators={briefing.indicators} />
      )}
      <div className="grid gap-5 sm:grid-cols-2">
        {briefing.sections.map((s) => (
          <SectionCard key={s.key} section={s} indicators={briefing.indicators} />
        ))}
      </div>
    </article>
  );
}

function Insight({ briefing }: { briefing: Briefing }) {
  return (
    <header className="space-y-4 border-b pb-8">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-muted-foreground">
        <span className="font-medium uppercase tracking-[0.14em] text-foreground/70">
          오늘의 인사이트
        </span>
        <span aria-hidden>·</span>
        <time dateTime={briefing.issue_date}>{issueLabel(briefing)}</time>
      </div>
      <p className="text-pretty text-2xl sm:text-[28px] font-semibold leading-snug tracking-tight">
        “{briefing.insight}”
      </p>
      <p className="text-[12px] text-muted-foreground">
        헤드라인 {briefing.source_count}건 분석 ·{" "}
        {briefing.model && briefing.model !== "fallback"
          ? `${briefing.model}가 편집`
          : "자동 편집"}
      </p>
    </header>
  );
}

function IndicatorStrip({ indicators }: { indicators: Indicator[] }) {
  return (
    <section
      aria-label="금융지표"
      className="flex gap-3 overflow-x-auto pb-1 -mx-1 px-1"
    >
      {indicators.map((ind) => (
        <Metric key={ind.label} ind={ind} />
      ))}
    </section>
  );
}

// Korean market convention: rises are red, falls are blue.
function dirColor(direction: Indicator["direction"]): string {
  if (direction === "up") return "text-rose-600 dark:text-rose-400";
  if (direction === "down") return "text-blue-600 dark:text-blue-400";
  return "text-muted-foreground";
}

function DirIcon({ direction }: { direction: Indicator["direction"] }) {
  const cls = "size-3.5";
  if (direction === "up") return <ArrowUpRight className={cls} />;
  if (direction === "down") return <ArrowDownRight className={cls} />;
  return <Minus className={cls} />;
}

function Metric({ ind }: { ind: Indicator }) {
  return (
    <div className="min-w-[8.5rem] shrink-0 rounded-lg ring-1 ring-foreground/10 bg-card px-3.5 py-2.5">
      <div className="text-[11px] text-muted-foreground truncate">{ind.label}</div>
      <div className="mt-1 text-[17px] font-semibold tabular-nums tracking-tight">
        {ind.value}
      </div>
      <div
        className={cn(
          "mt-0.5 flex items-center gap-0.5 text-[12px] tabular-nums",
          dirColor(ind.direction)
        )}
      >
        <DirIcon direction={ind.direction} />
        <span>{ind.change_pct}</span>
      </div>
    </div>
  );
}

function SectionCard({
  section,
  indicators,
}: {
  section: BriefingSection;
  indicators: Indicator[];
}) {
  const isMarkets = section.key === "markets";
  return (
    <section className="flex flex-col rounded-xl ring-1 ring-foreground/10 bg-card overflow-hidden">
      <div className="flex items-center gap-2.5 px-5 pt-5">
        <span
          aria-hidden
          className={cn(
            "h-4 w-1 rounded-full",
            SECTION_ACCENT[section.key] ?? "bg-foreground/30"
          )}
        />
        <AssetImg
          src={`/sections/${section.key}.png`}
          alt=""
          className="h-7 w-7 rounded-md bg-white object-contain p-0.5 ring-1 ring-foreground/10"
          fallback={null}
        />
        <div>
          <h2 className="text-[15px] font-semibold tracking-tight">
            {section.title}
          </h2>
          <p className="text-[12px] text-muted-foreground">{section.subtitle}</p>
        </div>
      </div>

      <div className="px-5 pb-5 pt-4">
        {isMarkets ? (
          <MarketsBody note={section.note} indicators={indicators} />
        ) : section.items.length === 0 ? (
          <p className="text-[13px] text-muted-foreground py-4">
            오늘은 수집된 주요 기사가 없습니다.
          </p>
        ) : (
          <ul className="space-y-4">
            {section.items.map((it, i) => (
              <li key={i} className="group">
                <a
                  href={it.url || undefined}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(
                    "block text-[14px] font-medium leading-snug",
                    it.url && "underline-offset-4 group-hover:underline"
                  )}
                >
                  {it.headline}
                </a>
                {it.summary && (
                  <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
                    {it.summary}
                  </p>
                )}
                {it.source && (
                  <p className="mt-1 text-[11px] uppercase tracking-wide text-muted-foreground/70">
                    {it.source}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

function MarketsBody({
  note,
  indicators,
}: {
  note?: string;
  indicators: Indicator[];
}) {
  return (
    <div className="space-y-4">
      {indicators.length > 0 ? (
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2.5">
          {indicators.map((ind) => (
            <div
              key={ind.label}
              className="flex items-baseline justify-between gap-2 border-b border-dashed pb-2"
            >
              <dt className="text-[12px] text-muted-foreground">{ind.label}</dt>
              <dd className="flex items-baseline gap-1.5">
                <span className="text-[13px] font-semibold tabular-nums">
                  {ind.value}
                </span>
                <span className={cn("text-[11px] tabular-nums", dirColor(ind.direction))}>
                  {ind.change_pct}
                </span>
              </dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="text-[13px] text-muted-foreground">지표를 불러오지 못했습니다.</p>
      )}
      {note && (
        <p className="text-[13px] leading-relaxed text-muted-foreground border-l-2 border-emerald-500/60 pl-3">
          {note}
        </p>
      )}
    </div>
  );
}
