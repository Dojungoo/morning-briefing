import { Feed } from "@/components/Feed";

export default function HomePage() {
  // Pre-rendered HTML wraps the Feed client component; the component
  // fetches /api/feed itself on mount so the same static page works
  // for everyone.
  return <Feed />;
}
