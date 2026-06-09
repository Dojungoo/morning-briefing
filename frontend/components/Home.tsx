"use client";

import { useEffect, useState } from "react";
import { Newspaper, RefreshCw, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchLatest, generateBriefing, pollBriefing, type Briefing } from "@/lib/api";
import { useMe } from "@/lib/identity";
import { BriefingView } from "./BriefingView";
import { SignInLink } from "./SignIn";

export function Home() {
  const me = useMe();
  const [briefing, setBriefing] = useState<Briefing | null | undefined>(undefined);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLatest().then((b) => setBriefing(b));
  }, []);

  async function onGenerate() {
    if (generating) return;
    setError(null);
    setGenerating(true);
    try {
      // Generation is async server-side: POST returns a pending row, then we
      // poll until it's filled in (crawl + LLM can run past the ~50s gateway
      // cap, so it can't be a single blocking request).
      const pending = await generateBriefing();
      const fresh = await pollBriefing(pending.id);
      setBriefing(fresh);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-end justify-between gap-4 pt-2">
        <div>
          <h1 className="text-[26px] sm:text-3xl font-semibold tracking-tight">
            AI 보험·대체투자 모닝 브리핑
          </h1>
          <p className="mt-2 max-w-xl text-[14px] text-muted-foreground leading-relaxed">
            보험·대체투자·프로젝트금융(PF) 실무자를 위한 마켓 인텔리전스. 헤드라인과
            금융지표를 자동 수집하고 AI가 한 화면으로 요약합니다.
          </p>
        </div>
        <GenerateControl
          me={me}
          hasBriefing={briefing != null}
          generating={generating}
          onGenerate={onGenerate}
        />
      </div>

      {error && (
        <p className="rounded-md border border-destructive/40 bg-destructive/5 px-4 py-3 text-[13px] text-destructive">
          {error}
        </p>
      )}

      {briefing === undefined ? (
        <LoadingState />
      ) : briefing === null ? (
        <EmptyState me={me} generating={generating} onGenerate={onGenerate} />
      ) : (
        <BriefingView briefing={briefing} />
      )}
    </div>
  );
}

function GenerateControl({
  me,
  hasBriefing,
  generating,
  onGenerate,
}: {
  me: ReturnType<typeof useMe>;
  hasBriefing: boolean;
  generating: boolean;
  onGenerate: () => void;
}) {
  if (me === undefined) return null;
  if (!me) {
    if (hasBriefing) return null;
    return <SignInLink size="sm" />;
  }
  return (
    <Button size="sm" onClick={onGenerate} disabled={generating}>
      <RefreshCw className={generating ? "size-4 animate-spin" : "size-4"} />
      {generating ? "생성 중…" : hasBriefing ? "새 브리핑 생성" : "브리핑 생성"}
    </Button>
  );
}

function LoadingState() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-24 w-full" />
      <div className="flex gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-36 shrink-0" />
        ))}
      </div>
      <div className="grid gap-5 sm:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-48 w-full" />
        ))}
      </div>
    </div>
  );
}

function EmptyState({
  me,
  generating,
  onGenerate,
}: {
  me: ReturnType<typeof useMe>;
  generating: boolean;
  onGenerate: () => void;
}) {
  return (
    <div className="rounded-xl border border-dashed bg-muted/30 px-6 py-14 text-center">
      <Newspaper className="mx-auto size-7 text-muted-foreground" />
      <p className="mt-4 text-[15px] font-medium">아직 발행된 브리핑이 없습니다</p>
      <p className="mx-auto mt-1.5 max-w-sm text-[13px] text-muted-foreground leading-relaxed">
        오늘의 보험·대체투자 헤드라인과 금융지표를 수집해 첫 브리핑을 만들어 보세요.
      </p>
      <div className="mt-5 flex justify-center">
        {me ? (
          <Button onClick={onGenerate} disabled={generating}>
            <Sparkles className={generating ? "size-4 animate-spin" : "size-4"} />
            {generating ? "생성 중… (최대 1분)" : "첫 브리핑 생성"}
          </Button>
        ) : (
          <SignInLink />
        )}
      </div>
    </div>
  );
}
