"use client";

import Link from "next/link";

import { useMe } from "@/lib/identity";
import { AssetImg } from "./AssetImg";
import { SignInLink, SignOutLink } from "./SignIn";

export function Header() {
  const me = useMe();

  return (
    <header className="flex items-center justify-between py-5">
      <Link
        href="/"
        className="flex items-center gap-2 text-[15px] font-semibold tracking-tight transition-colors hover:text-muted-foreground"
      >
        <AssetImg
          src="/brand/logo.png?v=1"
          alt=""
          className="h-6 w-6 rounded bg-white object-contain p-0.5 ring-1 ring-foreground/10"
          fallback={<span aria-hidden className="text-base">📈</span>}
        />
        모닝 브리핑
      </Link>
      <nav className="flex items-center gap-4 text-[13px]">
        <Link
          href="/archive"
          className="text-muted-foreground transition-colors hover:text-foreground"
        >
          지난 브리핑
        </Link>
        {me === undefined ? (
          <span aria-hidden className="opacity-0">·</span>
        ) : me ? (
          <>
            <span className="text-muted-foreground">{me.display_name}</span>
            <SignOutLink />
          </>
        ) : (
          <SignInLink size="sm" />
        )}
      </nav>
    </header>
  );
}
