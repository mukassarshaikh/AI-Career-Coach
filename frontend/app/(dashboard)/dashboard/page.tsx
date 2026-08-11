"use client";

/**
 * Dashboard page — 2x2 consolidated metrics summary grid per design_system.md (§3, §4, §5, §6 & §8).
 * Integrates GET /api/v1/dashboard/summary verified backend contract.
 */

import Link from "next/link";
import { FileText, Target, Compass, MessageSquare, ArrowRight } from "lucide-react";
import { useDashboardSummary } from "@/lib/hooks/useLearning";
import { AtsScoreGauge } from "@/components/resume/AtsScoreGauge";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

export default function DashboardPage() {
  const { data: summary, isLoading, isError } = useDashboardSummary();

  const resumeScore = summary?.resume_score ?? null;
  const missingSkillsCount = summary?.missing_skills_count ?? 0;
  const targetRole = summary?.target_role ?? null;
  const completionPercentage = summary?.roadmap_completion_percentage ?? 0;
  const completedItems = summary?.roadmap_completed_items ?? 0;
  const totalItems = summary?.roadmap_total_items ?? 0;

  const chatSessionsCount = summary?.chat_sessions_count ?? 0;

  // Recharts color constants (documented hex values for SVG elements unable to resolve CSS variables directly)
  const BRASS_HEX = "#C89B3C"; // --color-brass
  const LINE_HEX = "#DAD8CE"; // --color-line

  const gaugeData = [
    { name: "Completed", value: completionPercentage },
    { name: "Remaining", value: Math.max(0, 100 - completionPercentage) },
  ];

  if (isLoading) {
    return (
      <div className="space-y-8 max-w-6xl mx-auto pb-16 animate-pulse">
        <div className="space-y-2">
          <div className="h-9 w-48 bg-line/40 rounded-md" />
          <div className="h-5 w-80 bg-line/30 rounded-md" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-64 rounded-xl border border-line bg-paper-raised p-8" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="font-display text-display-lg tracking-tight text-ink">
          Dashboard
        </h1>
        <p className="font-body text-body text-ink-muted">
          Your consolidated career progress, resume score, skill gaps, and learning trajectory.
        </p>
      </div>

      {/* 2x2 Summary Cards Grid per design_system.md §5 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Card 1: Resume Score */}
        <div className="rounded-xl border border-line bg-paper-raised p-8 shadow-sm flex flex-col justify-between space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <FileText className="w-5 h-5 text-forest" />
              <h2 className="font-display text-display-md text-ink">Resume Score</h2>
            </div>
            <Link
              href="/resume"
              className="font-body text-body-sm font-medium text-forest hover:underline flex items-center gap-1"
            >
              <span>View details</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {resumeScore !== null ? (
            <div className="flex flex-col items-center justify-center py-2">
              <div className="scale-90 transform -my-4">
                <AtsScoreGauge score={resumeScore} />
              </div>
            </div>
          ) : (
            <div className="py-6 space-y-4 text-center">
              <p className="font-body text-body text-ink-muted">
                Upload your resume to get an ATS score and keyword gap audit.
              </p>
              <Link
                href="/resume"
                className="inline-flex items-center gap-2 rounded-md bg-forest px-4 py-2 text-body-sm font-medium text-paper-raised hover:bg-forest-hover transition-colors shadow-sm"
              >
                <span>Upload resume</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          )}
        </div>

        {/* Card 2: Skill Gaps */}
        <div className="rounded-xl border border-line bg-paper-raised p-8 shadow-sm flex flex-col justify-between space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Target className="w-5 h-5 text-forest" />
              <h2 className="font-display text-display-md text-ink">Skill Gaps</h2>
            </div>
            <Link
              href="/skill"
              className="font-body text-body-sm font-medium text-forest hover:underline flex items-center gap-1"
            >
              <span>Skill report</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {targetRole ? (
            <div className="space-y-4 py-4">
              <div className="space-y-1">
                <span className="font-mono text-data-lg text-[3rem] font-bold text-ink leading-none">
                  {missingSkillsCount}
                </span>
                <p className="font-body text-body text-ink-muted">
                  missing skills identified
                </p>
              </div>

              <div className="pt-4 border-t border-line">
                <p className="font-body text-body-sm text-ink-muted">
                  Target role:{" "}
                  <span className="font-semibold text-ink">{targetRole}</span>
                </p>
              </div>
            </div>
          ) : (
            <div className="py-6 space-y-4 text-center">
              <p className="font-body text-body text-ink-muted">
                Select a target career role to generate your skill gap analysis.
              </p>
              <Link
                href="/skill"
                className="inline-flex items-center gap-2 rounded-md bg-forest px-4 py-2 text-body-sm font-medium text-paper-raised hover:bg-forest-hover transition-colors shadow-sm"
              >
                <span>Select target role</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          )}
        </div>

        {/* Card 3: Roadmap Progress */}
        <div className="rounded-xl border border-line bg-paper-raised p-8 shadow-sm flex flex-col justify-between space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Compass className="w-5 h-5 text-forest" />
              <h2 className="font-display text-display-md text-ink">Roadmap Progress</h2>
            </div>
            <Link
              href="/learning"
              className="font-body text-body-sm font-medium text-forest hover:underline flex items-center gap-1"
            >
              <span>Learning path</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {totalItems > 0 ? (
            <div className="flex flex-col items-center justify-center space-y-4 py-2">
              <div className="relative w-48 h-32 flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={gaugeData}
                      cx="50%"
                      cy="80%"
                      startAngle={180}
                      endAngle={0}
                      innerRadius={55}
                      outerRadius={75}
                      paddingAngle={0}
                      dataKey="value"
                    >
                      {/* Documented Recharts hex exception: BRASS_HEX (#C89B3C) & LINE_HEX (#DAD8CE) */}
                      <Cell key="completed" fill={BRASS_HEX} />
                      <Cell key="remaining" fill={LINE_HEX} />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>

                <div className="absolute bottom-2 text-center">
                  <span className="font-mono text-data-lg font-bold text-ink">
                    {Math.round(completionPercentage)}%
                  </span>
                </div>
              </div>

              <div className="text-center space-y-1">
                <p className="font-mono text-data font-semibold text-ink">
                  {completedItems} / {totalItems} items completed
                </p>
                <p className="font-body text-body-sm text-ink-muted">
                  Active roadmap overall completion
                </p>
              </div>
            </div>
          ) : (
            <div className="py-6 space-y-4 text-center">
              <p className="font-body text-body text-ink-muted">
                Generate a personalized learning roadmap from your skill gap report.
              </p>
              <Link
                href="/skill"
                className="inline-flex items-center gap-2 rounded-md bg-forest px-4 py-2 text-body-sm font-medium text-paper-raised hover:bg-forest-hover transition-colors shadow-sm"
              >
                <span>Generate roadmap</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          )}
        </div>

        {/* Card 4: Career Advisor (Active) */}
        <div className="rounded-xl border border-forest bg-forest text-paper-raised p-8 shadow-sm flex flex-col justify-between space-y-6 hover:bg-forest-hover transition-colors">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <MessageSquare className="w-5 h-5 text-brass-soft" />
                <h2 className="font-display text-display-md text-paper-raised">
                  Career Advisor
                </h2>
              </div>
              <span className="text-data text-xs px-2.5 py-1 rounded-md bg-brass-soft/20 text-brass-soft font-mono">
                Active
              </span>
            </div>
            <p className="font-body text-body text-paper/90 leading-relaxed">
              Conversational AI career coaching, compensation guidance, and mock interviews tailored to your candidate profile.
            </p>
            {chatSessionsCount > 0 && (
              <div className="pt-2 border-t border-paper/20 text-body-sm text-paper/80 font-mono">
                {chatSessionsCount} conversation session{chatSessionsCount > 1 ? "s" : ""} active
              </div>
            )}
          </div>

          <div>
            <Link
              href="/career"
              className="inline-flex items-center gap-2 rounded-md bg-brass px-4 py-2.5 text-body-sm font-medium text-ink hover:bg-brass/90 transition-colors shadow-sm"
            >
              <span>{chatSessionsCount > 0 ? "Continue conversation" : "Start Career Advisor"}</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>


      </div>
    </div>
  );
}
