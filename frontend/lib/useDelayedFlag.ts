"use client";

import { useEffect, useState } from "react";

/**
 * Returns `false` immediately, then `true` after `ms`. Used to delay
 * showing "Warming up the server…" hints so we don't flash them on
 * fast hits — fires only when the request really is taking a while.
 *
 *   const warming = useDelayedFlag(5000, !!isLoading);
 */
export function useDelayedFlag(ms: number, active: boolean): boolean {
  const [flag, setFlag] = useState(false);
  useEffect(() => {
    if (!active) {
      setFlag(false);
      return;
    }
    const t = setTimeout(() => setFlag(true), ms);
    return () => clearTimeout(t);
  }, [ms, active]);
  return flag;
}
