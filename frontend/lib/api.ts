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
  status: "pending" | "ready" | "failed";
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

/**
 * Kick off generation. The backend returns a *pending* briefing immediately
 * (202) — the crawl + LLM work runs detached server-side because it can
 * exceed the platform's ~50s request cap. Poll {@link pollBriefing} on the
 * returned id to get the finished issue.
 */
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

/**
 * Poll a pending briefing until it leaves "pending". The recurring GETs also
 * keep the (scale-to-zero) backend pod warm while it works. Resolves with the
 * "ready" briefing, or throws on "failed" / timeout.
 */
export async function pollBriefing(
  id: string,
  { intervalMs = 2500, timeoutMs = 180_000 }: { intervalMs?: number; timeoutMs?: number } = {},
): Promise<Briefing> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
    const b = await fetchBriefing(id);
    if (b && b.status !== "pending") {
      if (b.status === "failed")
        throw new Error("브리핑 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.");
      return b;
    }
  }
  throw new Error("브리핑 생성이 지연되고 있습니다. 잠시 후 새로고침해 주세요.");
}
