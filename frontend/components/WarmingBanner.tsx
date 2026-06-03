import { Snowflake } from "lucide-react";

/**
 * Friendly heads-up shown while a tenant API request is in flight for
 * more than ~5s. The api KSvc scales to zero when idle, and the first
 * request after a quiet period spins up a fresh pod (alembic + uvicorn
 * boot, ~30-60s). The SPA fetch will eventually succeed — this banner
 * is purely so the visitor knows they're not stuck.
 */
export function WarmingBanner() {
  return (
    <div className="flex items-start gap-3 rounded-md border border-dashed bg-muted/40 px-4 py-3 text-[13px]">
      <Snowflake className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      <div>
        <div className="font-medium">Warming up the server</div>
        <p className="mt-0.5 text-muted-foreground">
          This site idles between visits to save power. The first request
          after a quiet period takes ~30s while the backend wakes up —
          it&apos;ll finish loading on its own.
        </p>
      </div>
    </div>
  );
}
