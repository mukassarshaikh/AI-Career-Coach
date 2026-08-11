"use client";

/**
 * Learning Overview page — active roadmap summary and roadmap generation entry point.
 * Follows design_system.md (§4, §5, §6 & §8).
 */

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Compass, ArrowRight, RefreshCw, Loader2, Sparkles } from "lucide-react";
import { useActiveRoadmap, useGenerateRoadmap } from "@/lib/hooks/useLearning";
import { useSkillGapReport } from "@/lib/hooks/useSkill";
import { useJobStatus } from "@/lib/hooks/useJobStatus";
import { ContourProgress } from "@/components/learning/ContourProgress";

export default function LearningPage() {
  const router = useRouter();
  const { data: activeRoadmap, isLoading: isLoadingRoadmap, isError: isRoadmapError } = useActiveRoadmap();
  const { data: gapReport } = useSkillGapReport();
  const generateMutation = useGenerateRoadmap();

  const [jobId, setJobId] = useState<string | null>(null);
  const { data: jobStatusData } = useJobStatus(jobId);

  // When roadmap generation background job completes, redirect to active roadmap
  useEffect(() => {
    if (jobStatusData?.status === "completed") {
      setJobId(null);
      // If result contains a roadmap ID or fetch active
      if (activeRoadmap?.id) {
        router.push(`/learning/${activeRoadmap.id}`);
      } else {
        router.refresh();
      }
    }
  }, [jobStatusData, activeRoadmap, router]);

  const handleGenerateRoadmap = async () => {
    if (!gapReport?.id) return;
    try {
      const res = await generateMutation.mutateAsync(gapReport.id);
      setJobId(res.job_id);
    } catch (err) {
      console.error("Failed to enqueue roadmap generation:", err);
    }
  };

  const isGenerating = !!jobId || generateMutation.isPending;

  if (isLoadingRoadmap) {
    return (
      <div className="space-y-8 max-w-4xl mx-auto pb-16 animate-pulse">
        <div className="h-10 w-64 bg-line/40 rounded-md" />
        <div className="h-64 rounded-xl border border-line bg-paper-raised p-8" />
      </div>
    );
  }

  const completedItems = activeRoadmap?.items
    ? activeRoadmap.items.filter((i) => i.status === "completed").length
    : 0;
  const totalItems = activeRoadmap?.items?.length ?? 0;
  const completionPercentage = totalItems > 0 ? (completedItems / totalItems) * 100 : 0;

  return (
    <div className="space-y-8 max-w-4xl mx-auto pb-16">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="font-display text-display-lg tracking-tight text-ink">
          Learning Intelligence
        </h1>
        <p className="font-body text-body text-ink-muted">
          Dynamic, skill-sequenced learning path tailored to your career target.
        </p>
      </div>

      {/* Generation in Progress Notice */}
      {isGenerating && (
        <div className="rounded-xl border border-brass/40 bg-brass-soft/30 p-6 flex items-center gap-4 shadow-sm">
          <Loader2 className="w-5 h-5 text-forest animate-spin flex-shrink-0" />
          <div className="space-y-1">
            <p className="font-body text-body-sm font-semibold text-ink">
              Building your personalized learning roadmap...
            </p>
            <p className="font-body text-body-sm text-ink-muted">
              Analyzing skill gaps, ordering resources by sequence order, and mapping milestones.
            </p>
          </div>
        </div>
      )}

      {/* Active Roadmap Present */}
      {activeRoadmap ? (
        <div className="rounded-xl border border-line bg-paper-raised p-8 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-line">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Compass className="w-5 h-5 text-brass" />
                <h2 className="font-display text-display-md text-ink">
                  Active Learning Roadmap
                </h2>
              </div>
              {gapReport?.target_role && (
                <p className="font-body text-body-sm text-ink-muted">
                  Target role:{" "}
                  <span className="font-semibold text-ink">{gapReport.target_role}</span>
                </p>
              )}
            </div>

            <Link
              href={`/learning/${activeRoadmap.id}`}
              className="inline-flex items-center justify-center gap-2 rounded-md bg-forest px-5 py-2.5 text-body-sm font-medium text-paper-raised hover:bg-forest-hover transition-colors shadow-sm self-start sm:self-auto"
            >
              <span>View full roadmap</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Progress Summary */}
          <div className="space-y-3">
            <div className="flex items-center justify-between font-mono text-data">
              <span className="text-ink font-semibold">Overall Completion</span>
              <span className="text-ink-muted">
                {completedItems} / {totalItems} items completed ({Math.round(completionPercentage)}%)
              </span>
            </div>

            <ContourProgress value={completionPercentage} size="lg" />
          </div>

          {/* Action Row */}
          {gapReport?.id && (
            <div className="pt-4 flex items-center justify-between text-body-sm">
              <span className="text-ink-muted">
                Need an updated path? You can regenerate a new roadmap from your latest skill gap report.
              </span>

              <button
                type="button"
                onClick={handleGenerateRoadmap}
                disabled={isGenerating}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md border border-line bg-paper text-ink hover:bg-paper-raised hover:border-forest/40 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 text-forest ${isGenerating ? "animate-spin" : ""}`} />
                <span>Generate new roadmap</span>
              </button>
            </div>
          )}
        </div>
      ) : (
        /* Empty State — No Active Roadmap */
        <div className="rounded-xl border border-line bg-paper-raised p-10 text-center space-y-6 shadow-sm">
          <div className="w-12 h-12 rounded-full bg-brass-soft/40 mx-auto flex items-center justify-center text-forest">
            <Compass className="w-6 h-6" />
          </div>

          <div className="space-y-2 max-w-md mx-auto">
            <h2 className="font-display text-display-md text-ink">
              No active learning roadmap
            </h2>
            <p className="font-body text-body text-ink-muted">
              You don't have a learning roadmap yet. Generate one from your skill gap report to chart your learning path.
            </p>
          </div>

          <div>
            {gapReport?.id ? (
              <button
                type="button"
                onClick={handleGenerateRoadmap}
                disabled={isGenerating}
                className="inline-flex items-center gap-2 rounded-md bg-forest px-5 py-2.5 text-body-sm font-medium text-paper-raised hover:bg-forest-hover transition-colors shadow-sm disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4 text-brass" />
                <span>{isGenerating ? "Generating roadmap..." : "Generate roadmap from skill report"}</span>
              </button>
            ) : (
              <Link
                href="/skill"
                className="inline-flex items-center gap-2 rounded-md bg-forest px-5 py-2.5 text-body-sm font-medium text-paper-raised hover:bg-forest-hover transition-colors shadow-sm"
              >
                <span>Create skill gap report first</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
