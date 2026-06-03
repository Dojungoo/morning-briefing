"use client";

import { Snowflake } from "lucide-react";

import { useWarming } from "@/lib/warming";

/**
 * Full-width heads-up at the top of every page. Activates after any
 * tracked fetch has been in flight for ~5s (lib/warming.ts) — covers
 * the cold-start path where the api KSvc is waking up.
 *
 * Stays inert at SSR / first paint; only the client-mounted effect
 * decides to show anything.
 */
export function WarmingBar() {
  const warming = useWarming();
  if (!warming) return null;
  return (
    <div
      role="status"
      aria-live="polite"
      className="border-b bg-muted/60 px-6 sm:px-8 py-2.5 text-[13px] text-foreground/80"
    >
      <div className="mx-auto flex max-w-3xl items-center gap-2">
        <Snowflake className="size-4 shrink-0 text-muted-foreground" />
        <span>
          <span className="font-medium">Warming up the server.</span>{" "}
          <span className="text-muted-foreground">
            This site idles between visits — first request takes ~30s while
            the backend wakes up.
          </span>
        </span>
      </div>
    </div>
  );
}
