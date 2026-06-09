import { Home } from "@/components/Home";

export default function HomePage() {
  // Pre-rendered shell; the Home client component fetches the latest
  // briefing on mount so the same static page works for everyone.
  return <Home />;
}
