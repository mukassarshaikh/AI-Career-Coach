"use client";

/**
 * TargetJobDescriptionCard — Textarea for job description input, keyword gap analysis trigger,
 * and displaying missing keywords & prioritized action items per design_system.md §5, §6, §7.
 */

import { useState } from "react";
import { Loader2, Search, Target, AlertTriangle } from "lucide-react";
import { useSubmitJobDescription } from "@/lib/hooks/useResume";
import { useJobStatus } from "@/lib/hooks/useJobStatus";
import { ContourProgress } from "@/components/ui/ContourProgress";
import type { KeywordGap, ActionItem } from "@/types/resume";

interface TargetJobDescriptionCardProps {
  resumeId: string;
  hasInitialReport: boolean;
  isScoringInProgress?: boolean;
  isScoringFailed?: boolean;
  keywordGaps?: KeywordGap[] | null;
  actionItems?: ActionItem[] | null;
  onAnalysisSubmitted?: () => void;
  className?: string;
}

export function TargetJobDescriptionCard({
  resumeId,
  hasInitialReport,
  isScoringInProgress = false,
  isScoringFailed = false,
  keywordGaps,
  actionItems,
  onAnalysisSubmitted,
  className = "",
}: TargetJobDescriptionCardProps) {
  const [jobDescriptionText, setJobDescriptionText] = useState("");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  const submitJdMutation = useSubmitJobDescription();
  const { data: jobStatus } = useJobStatus(activeJobId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobDescriptionText.trim() || !hasInitialReport) return;

    try {
      const res = await submitJdMutation.mutateAsync({
        resumeId,
        rawText: jobDescriptionText.trim(),
      });
      setActiveJobId(res.job_id);
      if (onAnalysisSubmitted) {
        onAnalysisSubmitted();
      }
    } catch {
      // Handled in UI via submitJdMutation.isError
    }
  };

  const isAnalyzing =
    submitJdMutation.isPending ||
    (activeJobId !== null && (jobStatus?.status === "queued" || jobStatus?.status === "in_progress"));

  return (
    <div className={`rounded-xl border border-line bg-paper-raised p-8 shadow-sm space-y-6 ${className}`}>
      <div className="space-y-1.5">
        <h3 className="font-display text-display-md text-ink">Target Job Description Analysis</h3>
        <p className="font-body text-body-sm text-ink-muted">
          Compare your resume against a specific job posting to discover missing keywords and prioritized recommendations.
        </p>
      </div>

      {!hasInitialReport && (
        <div className="rounded-md bg-brass-soft/40 border border-brass/30 p-4 font-body text-body-sm text-ink flex items-start gap-2.5">
          <AlertTriangle className="w-5 h-5 text-brass flex-shrink-0 mt-0.5" />
          <span>
            {isScoringInProgress
              ? "Initial resume evaluation is processing above. Target job description analysis will become available once initial evaluation completes."
              : isScoringFailed
              ? "Initial resume evaluation encountered an error above. Click 'Retry Scoring' above to resolve initial evaluation."
              : "Complete the initial resume evaluation above to unlock target job description analysis."}
          </span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <label htmlFor="jd-textarea" className="block font-body text-body-sm font-medium text-ink">
            Target job description text
          </label>
          <textarea
            id="jd-textarea"
            rows={5}
            disabled={!hasInitialReport || isAnalyzing}
            value={jobDescriptionText}
            onChange={(e) => setJobDescriptionText(e.target.value)}
            placeholder="Paste the full job posting requirements and qualifications here..."
            className="w-full rounded-md border border-line bg-paper-raised p-3.5 font-body text-body-sm text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-forest focus:border-transparent disabled:opacity-50 transition-all resize-y"
          />
        </div>

        {submitJdMutation.isError && (
          <p role="alert" className="font-body text-body-sm font-medium text-clay-alert">
            Failed to submit job description. Try submitting again.
          </p>
        )}

        <div className="flex justify-end pt-1">
          <button
            type="submit"
            disabled={!hasInitialReport || !jobDescriptionText.trim() || isAnalyzing}
            className="rounded-md bg-forest px-5 py-2.5 font-body text-body-sm font-medium text-white shadow-sm hover:bg-forest-hover disabled:opacity-50 transition-colors cursor-pointer flex items-center gap-2"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Analyzing keywords...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Analyze against target job</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Progress status while analysis runs */}
      {isAnalyzing && (
        <div className="p-5 rounded-xl border border-line bg-paper/60 space-y-3">
          <div className="flex items-center justify-between font-body text-body-sm font-medium text-ink">
            <span>Analyzing keyword match against target role</span>
            <span className="font-mono text-data text-forest">{jobStatus?.status || "processing"}</span>
          </div>
          <ContourProgress active={true} />
        </div>
      )}

      {/* Analysis Results Display */}
      {(!isAnalyzing && (keywordGaps?.length || actionItems?.length)) ? (
        <div className="space-y-6 pt-6 border-t border-line">
          {/* Missing Keywords Badges */}
          {keywordGaps && keywordGaps.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-brass" />
                <h4 className="font-display text-body-lg font-medium text-ink">
                  Missing Keywords ({keywordGaps.length})
                </h4>
              </div>
              <p className="font-body text-body-sm text-ink-muted">
                Skills and terms found in the job description that are missing from your resume.
              </p>
              <div className="flex flex-wrap gap-2 pt-1">
                {keywordGaps.map((item, index) => {
                  const kw = typeof item === "string" ? item : item.keyword || item;
                  return (
                    <span
                      key={index}
                      className="px-3 py-1 rounded-md font-mono text-data font-medium bg-brass-soft text-ink border border-brass/30"
                    >
                      {kw}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {/* Action Items Prioritized List */}
          {actionItems && actionItems.length > 0 && (
            <div className="space-y-3 pt-4 border-t border-line">
              <h4 className="font-display text-body-lg font-medium text-ink">
                Prioritized Action Items
              </h4>
              <p className="font-body text-body-sm text-ink-muted">
                Recommended edits to increase keyword alignment with this target position.
              </p>
              <ol className="space-y-3 pt-1">
                {actionItems.map((item, index) => {
                  const actionText = typeof item === "string" ? item : item.action || item;
                  return (
                    <li key={index} className="flex items-start gap-3 p-4 rounded-md bg-paper border border-line">
                      <span className="w-6 h-6 rounded-full bg-forest text-white font-mono text-data font-bold flex items-center justify-center flex-shrink-0 text-xs">
                        {index + 1}
                      </span>
                      <div className="space-y-1">
                        <p className="font-body text-body-sm font-medium text-ink">{actionText}</p>
                        {item.impact && (
                          <p className="font-body text-body-sm text-ink-muted">
                            <span className="font-semibold text-forest">Impact: </span>
                            {item.impact}
                          </p>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ol>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
