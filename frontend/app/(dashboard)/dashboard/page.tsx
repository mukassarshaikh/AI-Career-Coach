"use client";

/**
 * Dashboard page — consolidated summary view.
 * Includes a health-check status card to verify backend connectivity.
 */

import { useHealth } from "@/lib/hooks/useHealth";

export default function DashboardPage() {
  const { data: health, isLoading, isError } = useHealth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Your career progress at a glance
        </p>
      </div>

      {/* Backend health status — development helper */}
      <div className="rounded-xl border border-border bg-card p-4 flex items-center gap-3">
        <span
          aria-hidden="true"
          className={`w-2.5 h-2.5 rounded-full ${
            isLoading
              ? "bg-yellow-400 animate-pulse"
              : isError
              ? "bg-red-500"
              : "bg-green-500"
          }`}
        />
        <span className="text-sm font-medium text-card-foreground">
          {isLoading
            ? "Checking backend…"
            : isError
            ? "Backend unreachable — start uvicorn"
            : health?.message ?? "Backend OK"}
        </span>
      </div>

      {/* Module summary cards — wired in as each Phase 1+ module ships */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Resumes", value: "—", href: "/resume", icon: "📄" },
          { label: "ATS Score", value: "—", href: "/resume", icon: "🎯" },
          { label: "Skill Gaps", value: "—", href: "/skill", icon: "📊" },
          { label: "Active Roadmaps", value: "—", href: "/learning", icon: "🗺️" },
        ].map(({ label, value, href, icon }) => (
          <a
            key={label}
            href={href}
            className="rounded-xl border border-border bg-card p-4 hover:bg-muted/50 transition-colors space-y-2"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{label}</span>
              <span className="text-lg">{icon}</span>
            </div>
            <p className="text-2xl font-bold text-foreground">{value}</p>
          </a>
        ))}
      </div>
    </div>
  );
}
