"use client";

import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import {
  fetchBriefing,
  fetchHistory,
  type Briefing,
  type BriefingSummary,
} from "@/lib/api";
import { BriefingView } from "./BriefingView";

function issueLabel(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  const day = ["일", "월", "화", "수", "목", "금", "토"][d.getDay()];
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(
    d.getDate()
  ).padStart(2, "0")} (${day})`;
}

export function Archive() {
  const [items, setItems] = useState<BriefingSummary[] | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);

  useEffect(() => {
    fetchHistory().then(setItems);
  }, []);

  return (
    <div className="space-y-8 pt-2">
      <header>
        <h1 className="text-[26px] sm:text-3xl font-semibold tracking-tight">
          지난 브리핑
        </h1>
        <p className="mt-2 text-[14px] text-muted-foreground">
          발행된 모닝 브리핑 기록입니다. 항목을 펼쳐 전체 내용을 확인하세요.
        </p>
      </header>

      <ul className="divide-y rounded-xl ring-1 ring-foreground/10 bg-card overflow-hidden">
        {items === null && (
          <li className="p-5">
            <Skeleton className="h-12 w-full" />
          </li>
        )}
        {items && items.length === 0 && (
          <li className="p-8 text-center text-[13px] text-muted-foreground">
            아직 발행된 브리핑이 없습니다.
          </li>
        )}
        {items?.map((it) => (
          <ArchiveRow
            key={it.id}
            item={it}
            open={openId === it.id}
            onToggle={() => setOpenId((cur) => (cur === it.id ? null : it.id))}
          />
        ))}
      </ul>
    </div>
  );
}

function ArchiveRow({
  item,
  open,
  onToggle,
}: {
  item: BriefingSummary;
  open: boolean;
  onToggle: () => void;
}) {
  const [briefing, setBriefing] = useState<Briefing | null | undefined>(undefined);

  useEffect(() => {
    if (open && briefing === undefined) {
      fetchBriefing(item.id).then(setBriefing);
    }
  }, [open, briefing, item.id]);

  return (
    <li>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="flex w-full items-center gap-4 px-5 py-4 text-left transition-colors hover:bg-muted/50"
      >
        <time className="w-28 shrink-0 text-[12px] tabular-nums text-muted-foreground">
          {issueLabel(item.issue_date)}
        </time>
        <span className="flex-1 text-[14px] leading-snug">{item.insight}</span>
        {open ? (
          <ChevronDown className="size-4 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
        )}
      </button>
      {open && (
        <div className={cn("border-t bg-background px-5 py-6")}>
          {briefing === undefined ? (
            <Skeleton className="h-48 w-full" />
          ) : briefing === null ? (
            <p className="text-[13px] text-muted-foreground">
              내용을 불러오지 못했습니다.
            </p>
          ) : (
            <BriefingView briefing={briefing} />
          )}
        </div>
      )}
    </li>
  );
}
