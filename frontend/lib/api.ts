"use client";

/**
 * Browser-side API helpers. All calls hit /api/* on this same origin;
 * the nginx in front of us proxies that to the backend KSvc.
 */

export type Post = {
  id: string;
  body: string;
  author_id: string;
  author_name: string;
  created_at: string;
};

export async function fetchFeed(): Promise<Post[]> {
  const r = await fetch("/api/feed", { credentials: "include" });
  if (!r.ok) return [];
  return r.json();
}

export async function fetchUserPosts(userId: string): Promise<Post[]> {
  const r = await fetch(`/api/users/${userId}/posts`, {
    credentials: "include",
  });
  if (!r.ok) return [];
  return r.json();
}

export async function createPost(body: string): Promise<Post | null> {
  const r = await fetch("/api/posts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ body }),
  });
  if (!r.ok) return null;
  return r.json();
}
