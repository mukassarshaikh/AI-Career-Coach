/**
 * Root layout — wraps all routes.
 * Provides: TanStack Query client, NextAuth SessionProvider, global CSS.
 */

import type { Metadata } from "next";
import "@/styles/globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: {
    default: "AI Career Coach",
    template: "%s | AI Career Coach",
  },
  description:
    "AI-powered career coaching: ATS resume scoring, skill-gap analysis, personalized learning roadmaps, and a conversational career advisor.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
