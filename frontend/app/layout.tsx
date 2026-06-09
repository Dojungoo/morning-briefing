import type { ReactNode } from "react";
import { Inter, JetBrains_Mono } from "next/font/google";

import { Header } from "@/components/Header";
import { WarmingBar } from "@/components/WarmingBanner";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata = {
  title: "AI 보험·대체투자 모닝 브리핑",
  description:
    "보험·대체투자·프로젝트금융(PF) 실무자를 위한 AI 마켓 인텔리전스 브리핑.",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable}`}>
      <body>
        <WarmingBar />
        <div className="mx-auto max-w-3xl px-6 sm:px-8 pb-16">
          <Header />
          <main>{children}</main>
          <footer className="mt-20 border-t pt-6 text-[12px] text-muted-foreground leading-relaxed">
            AI 보험·대체투자 모닝 브리핑 · 헤드라인은 Google News, 금융지표는 Yahoo
            Finance에서 수집하며 AI가 요약합니다. 투자 권유가 아닙니다. ·{" "}
            <a
              href="https://coders.kr"
              className="font-medium text-foreground/80 underline-offset-4 hover:underline"
            >
              coders.kr
            </a>
            에서 호스팅
          </footer>
        </div>
      </body>
    </html>
  );
}
