"use client";

import { useState, type ReactNode } from "react";

/**
 * Renders an image from /public, falling back gracefully if the file is
 * missing (404) so the UI never shows a broken-image icon. This lets us wire
 * the brand/logo, section-icon and hero slots ahead of time — the generated
 * (DALL·E/Midjourney) PNGs can be dropped into /public later and they light up
 * automatically, while the deterministic fallback keeps the page intact until
 * then.
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
  const [failed, setFailed] = useState(false);
  if (failed) return <>{fallback}</>;
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={alt}
      className={className}
      onError={() => setFailed(true)}
    />
  );
}
