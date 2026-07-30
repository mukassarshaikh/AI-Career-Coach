"use client";

/**
 * Dashboard page — consolidated summary view.
 * Restyled matching design_system.md (§1, §2, §3, §5).
 */

import Link from "next/link";
import { FileText, Target, BarChart2, Compass, Activity } from "lucide-react";
import { useHealth } from "@/lib/hooks/useHealth";

export default function DashboardPage() {
  const { data: health, isLoading, isError } = useHealth();

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-16">
      <div className="space-y-1.5">
        <h1 className="font-display text-display-lg tracking-tight text-ink">
          Dashboard
        </h1>
        <p className="font-body text-body text-ink-muted">
          Your career progress and instrument data at a glance.
        </p>
      </div>

      {/* Backend health status indicator */}
      <div className="rounded-xl border border-line bg-paper-raised p-4 flex items-center gap-3 shadow-sm">
        <span
          aria-hidden="true"
          className={`w-2.5 h-2.5 rounded-full ${
            isLoading
              ? "bg-brass animate-pulse"
              : isError
              ? "bg-clay-alert"
              : "bg-forest"
          }`}
        />
        <span className="font-mono text-data font-medium text-ink flex items-center gap-2">
          <Activity className="w-4 h-4 text-forest" />
          <span>
            {isLoading
              ? "Connecting to backend service..."
              : isError
              ? "Backend service unreachable"
              : health?.message ?? "Backend connected"}
          </span>
        </span>
      </div>

      {/* Module summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {[
          { label: "Resumes", value: "—", href: "/resume", icon: FileText },
          { label: "ATS Score", value: "—", href: "/resume", icon: Target },
          { label: "Skill Gaps", value: "—", href: "/skill", icon: BarChart2 },
          { label: "Active Roadmaps", value: "—", href: "/learning", icon: Compass },
        ].map(({ label, value, href, icon: Icon }) => (
          <Link
            key={label}
            href={href}
            className="rounded-xl border border-line bg-paper-raised p-6 hover:border-forest/40 transition-colors space-y-3 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <span className="font-body text-body-sm font-medium text-ink-muted">{label}</span>
              <Icon className="w-5 h-5 text-forest" />
            </div>
            <p className="font-mono text-data-lg font-bold text-ink">{value}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
