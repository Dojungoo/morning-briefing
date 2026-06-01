import type { ReactNode } from "react";

import { Header } from "@/components/Header";

export const metadata = {
  title: "template-coders",
  description: "A coders.kr-aware SPA starter.",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <body
        style={{
          fontFamily: "system-ui, sans-serif",
          maxWidth: "44rem",
          margin: "0 auto",
          padding: "0 1rem",
          lineHeight: 1.5,
          color: "#0f172a",
        }}
      >
        <Header />
        <main>{children}</main>
        <footer
          style={{
            marginTop: "3rem",
            padding: "1.25rem 0",
            borderTop: "1px solid #e5e7eb",
            fontSize: ".88rem",
            opacity: 0.7,
          }}
        >
          Hosted on <a href="https://coders.kr">coders.kr</a> — identity and
          metering handled by the platform; this app reads <code>X-Coders-User</code>
          {" "}on the backend and learns who you are on the frontend by
          fetching <code>/api/me</code>.
        </footer>
      </body>
    </html>
  );
}
