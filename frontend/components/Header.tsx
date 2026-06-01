"use client";

import Link from "next/link";

import { useMe } from "@/lib/identity";
import { SignInLink, SignOutLink } from "./SignIn";

export function Header() {
  const me = useMe();

  return (
    <header
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "1.25rem 0",
        borderBottom: "1px solid #e5e7eb",
        marginBottom: "1.5rem",
      }}
    >
      <Link
        href="/"
        style={{
          fontSize: "1.15rem",
          fontWeight: 600,
          color: "inherit",
          textDecoration: "none",
        }}
      >
        template-coders
      </Link>
      <nav style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
        {me === undefined ? (
          // Loading: render nothing so the page doesn't flash a sign-in
          // button at people who turn out to be signed in already.
          <span style={{ opacity: 0 }}>·</span>
        ) : me ? (
          <>
            <Link href="/profile" style={{ color: "inherit" }}>
              {me.display_name}
            </Link>
            <SignOutLink />
          </>
        ) : (
          <SignInLink />
        )}
      </nav>
    </header>
  );
}
