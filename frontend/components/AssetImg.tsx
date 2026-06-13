"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

/**
 * Renders an image from /public, staying invisible until it actually loads —
 * so a missing file (404, or the SPA's index.html served in its place) never
 * flashes a broken-image box. While loading or on error we show `fallback`
 * (an emoji for the logo, nothing for the hero/icons).
 *
 * Because the <img> is server-rendered (static export), it can finish loading
 * BEFORE React hydrates and attaches onLoad — in which case the event never
 * fires and the image would stay hidden forever. The mount effect handles that
 * by checking `img.complete`/`naturalWidth` once on hydration.
 */
export function AssetImg({
  src,
  alt = "",
  className,
  fallback = null,
}: {
  src: string;
  alt?: string;
  className?: string;
  fallback?: ReactNode;
}) {
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const ref = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const img = ref.current;
    if (img && img.complete) {
      setState(img.naturalWidth > 0 ? "ok" : "error");
    }
  }, []);

  return (
    <>
      {state !== "ok" && fallback}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        ref={ref}
        src={src}
        alt={alt}
        className={state === "ok" ? className : "hidden"}
        onLoad={() => setState("ok")}
        onError={() => setState("error")}
      />
    </>
  );
}
