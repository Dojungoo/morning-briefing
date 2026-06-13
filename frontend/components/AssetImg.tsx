"use client";

import { useState, type ReactNode } from "react";

/**
 * Renders an image from /public, but stays invisible until it actually loads —
 * so a missing file (404, or the SPA's index.html served in its place) never
 * flashes a broken-image box. While loading or on error we show `fallback`
 * (an emoji for the logo, nothing for the hero/icons). This lets us wire the
 * brand/logo, section-icon and hero slots ahead of time: drop the generated
 * (DALL·E / Midjourney / Nano-Banana) PNGs into /public and they light up
 * automatically, while the page stays clean until then.
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
  return (
    <>
      {state !== "ok" && fallback}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={alt}
        className={state === "ok" ? className : "hidden"}
        onLoad={() => setState("ok")}
        onError={() => setState("error")}
      />
    </>
  );
}
