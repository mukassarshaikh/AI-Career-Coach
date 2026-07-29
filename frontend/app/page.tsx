import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Career Coach — Land Your Next Role Faster",
  description:
    "AI-powered ATS scoring, skill-gap analysis, personalized learning roadmaps, and a conversational career advisor. Free to get started.",
};

export default function LandingPage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-background to-secondary px-6">
      <div className="max-w-3xl text-center space-y-8">
        {/* Hero */}
        <div className="space-y-4">
          <span className="inline-block px-3 py-1 text-sm font-medium rounded-full bg-primary/10 text-primary border border-primary/20">
            Phase 0 — Scaffolding Complete
          </span>
          <h1 className="text-5xl font-bold tracking-tight text-foreground">
            AI Career Coach
          </h1>
          <p className="text-xl text-muted-foreground max-w-xl mx-auto">
            ATS resume scoring · Skill-gap analysis · Personalized learning
            roadmaps · Conversational career advisor
          </p>
        </div>

        {/* CTA */}
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link
            id="get-started-link"
            href="/register"
            className="px-6 py-3 rounded-lg bg-primary text-primary-foreground font-semibold hover:opacity-90 transition-opacity"
          >
            Get started free
          </Link>
          <Link
            id="sign-in-link"
            href="/login"
            className="px-6 py-3 rounded-lg border border-border text-foreground font-semibold hover:bg-muted transition-colors"
          >
            Sign in
          </Link>
        </div>

        {/* Module grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
          {[
            { icon: "📄", label: "Resume Intelligence" },
            { icon: "🎯", label: "Skill Intelligence" },
            { icon: "🗺️", label: "Learning Intelligence" },
            { icon: "💬", label: "Career Intelligence" },
          ].map(({ icon, label }) => (
            <div
              key={label}
              className="flex flex-col items-center gap-2 p-4 rounded-xl border border-border bg-card text-card-foreground"
            >
              <span className="text-2xl">{icon}</span>
              <span className="text-sm font-medium text-center">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
