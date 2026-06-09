"use client";

/**
 * Browser-side API helpers. All calls hit /api/* on this same origin;
 * the nginx in front of us proxies that to the backend.
 *
 * Every fetch is wrapped in `tracked()` so the global WarmingBar can
 * react when any of them spends more than ~5s in flight (lib/warming) —
 * briefing generation, in particular, crawls + calls the LLM and can run
 * for many seconds.
 */

import { tracked } from "./warming";

export type BriefingItem = {
  headline: string;
  summary: string;
  source: string;
  url: string;
};

export type BriefingSection = {
  key: string;
  title: string;
  subtitle: string;
  items: BriefingItem[];
  note?: string;
};

export type Indicator = {
  label: string;
  value: string;
  change: string;
  change_pct: string;
  direction: "up" | "down" | "flat";
};

export type Briefing = {
  id: string;
  issue_date: string;
  insight: string;
  sections: BriefingSection[];
  indicators: Indicator[];
  source_count: number;
  model: string;
  author_name: string;
  created_at: string;
};

export type BriefingSummary = {
  id: string;
  issue_date: string;
  insight: string;
  created_at: string;
};

export async function fetchLatest(): Promise<Briefing | null> {
  return tracked(async () => {
    const r = await fetch("/api/briefing/latest", { credentials: "include" });
    if (!r.ok) return null;
    return r.json();
  });
}

export async function fetchHistory(): Promise<BriefingSummary[]> {
  return tracked(async () => {
    const r = await fetch("/api/briefing/history", { credentials: "include" });
    if (!r.ok) return [];
    return r.json();
  });
}

export async function fetchBriefing(id: string): Promise<Briefing | null> {
  return tracked(async () => {
    const r = await fetch(`/api/briefing/${id}`, { credentials: "include" });
    if (!r.ok) return null;
    return r.json();
  });
}

export async function generateBriefing(): Promise<Briefing> {
  return tracked(async () => {
    const r = await fetch("/api/briefing/generate", {
      method: "POST",
      credentials: "include",
    });
    if (!r.ok) {
      let detail = `브리핑 생성 실패 (${r.status})`;
      try {
        const j = await r.json();
        if (j?.detail)
          detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
      } catch {
        /* non-JSON */
      }
      throw new Error(detail);
    }
    return r.json();
  });
}
