"use client";

/**
 * Resume Detail & Report Page — /app/(dashboard)/resume/[id]/page.tsx
 *
 * Fixes bug by:
 *   1. Gating `useResumeReport` on `hasAtsScore` so un-scored resumes do NOT spam 404 requests to GET /report.
 *   2. Polling `useResume` while `parsed_json` is null with a 45s max timeout cap to stop infinite polling loops.
 *   3. Auto-triggering `score_resume` ONCE when `parsed_json` is present and `ats_score` is null.
 *   4. Rendering explicit `ContourProgress` for both parsing and scoring phases.
 *   5. Handling timeout/failure with a clear error box and Retry button.
 */

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, ExternalLink, Loader2, RefreshCw, AlertTriangle } from "lucide-react";
import { useResume, useResumeReport, useScoreResume } from "@/lib/hooks/useResume";
import { useJobStatus } from "@/lib/hooks/useJobStatus";
import { AtsScoreGauge } from "@/components/resume/AtsScoreGauge";
import { GrammarSuggestionsList } from "@/components/resume/GrammarSuggestionsList";
import { TargetJobDescriptionCard } from "@/components/resume/TargetJobDescriptionCard";
import { ContourProgress } from "@/components/ui/ContourProgress";

export default function ResumeDetailPage() {
  const params = useParams();
  const resumeId = params?.id as string;

  // 1. Fetch Resume Record with 45s parse timeout cap
  const {
    data: resume,
    isLoading: isResumeLoading,
    refetch: refetchResume,
    isParseTimedOut,
  } = useResume(resumeId);

  // 2. Gated Report Fetching: ONLY enabled if resume has ats_score OR report already exists
  const hasAtsScore = resume?.ats_score !== null && resume?.ats_score !== undefined;
  const { data: report, refetch: refetchReport } = useResumeReport(resumeId, {
    enabled: hasAtsScore,
  });

  const scoreMutation = useScoreResume();
  const [scoreJobId, setScoreJobId] = useState<string | null>(null);
  const { data: scoreJobStatus } = useJobStatus(scoreJobId);

  // Guard against re-triggering auto-score on re-renders
  const hasAutoScoredRef = useRef(false);

  // Auto-trigger score_resume if parsed_json exists, ats_score is null, and no score job running
  useEffect(() => {
    if (!resume || hasAutoScoredRef.current) return;

    const isParsed = !!resume.parsed_json;
    const isUnscored = resume.ats_score === null || resume.ats_score === undefined;

    if (isParsed && isUnscored && !scoreMutation.isPending && !scoreJobId) {
      hasAutoScoredRef.current = true;
      scoreMutation.mutate(resumeId, {
        onSuccess: (data) => {
          setScoreJobId(data.job_id);
        },
      });
    }
  }, [resume, resumeId, scoreMutation, scoreJobId]);

  // When scoring job completes, refetch resume and report
  useEffect(() => {
    if (scoreJobStatus?.status === "complete") {
      refetchResume();
      refetchReport();
    }
  }, [scoreJobStatus?.status, refetchResume, refetchReport]);

  const handleRetryScoring = () => {
    hasAutoScoredRef.current = true;
    setScoreJobId(null);
    scoreMutation.mutate(resumeId, {
      onSuccess: (data) => {
        setScoreJobId(data.job_id);
      },
    });
  };

  const isParsingInProgress = !!resume && !resume.parsed_json && resume.ats_score === null && !isParseTimedOut;
  const isScoringInProgress =
    scoreMutation.isPending ||
    (scoreJobId !== null &&
      (scoreJobStatus?.status === "queued" || scoreJobStatus?.status === "in_progress"));

  const isScoringFailed = scoreJobStatus?.status === "failed" || scoreMutation.isError;
  const hasScoreOrReport = hasAtsScore || !!report?.ats_breakdown;

  return (
    <div className="space-y-10 max-w-5xl mx-auto pb-16">
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <Link
          href="/resume"
          className="font-body text-body-sm text-forest hover:underline flex items-center gap-1.5 font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Resume Management</span>
        </Link>
        <span className="font-mono text-data text-ink-muted">ID: {resumeId.substring(0, 12)}...</span>
      </div>

      {/* Main Page Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-line pb-6">
        <div className="space-y-1.5">
          <h1 className="font-display text-display-lg tracking-tight text-ink">
            Resume Evaluation & ATS Report
          </h1>
          <p className="font-body text-body text-ink-muted">
            Detailed ATS readability score, grammar audit recommendations, and target job keyword alignment.
          </p>
        </div>

        {resume?.file_url && (
          <a
            href={resume.file_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-md bg-paper border border-line px-4 py-2 font-mono text-data text-ink hover:bg-paper-raised transition-colors flex-shrink-0"
          >
            <span>View Original File</span>
            <ExternalLink className="w-4 h-4 text-forest" />
          </a>
        )}
      </div>

      {/* Parsing In Progress State */}
      {isParsingInProgress && !isScoringInProgress && (
        <div className="rounded-xl border border-line bg-paper-raised p-8 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="font-display text-display-md text-ink">Parsing Resume Document</h3>
              <p className="font-body text-body-sm text-ink-muted">
                Extracting text and structuring sections via Groq LLM parsing.
              </p>
            </div>
            <span className="px-3 py-1 rounded-md font-mono text-data font-medium bg-paper border border-line text-forest">
              parsing
            </span>
          </div>
          <ContourProgress active={true} />
          <p className="font-body text-body-sm text-ink-muted flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-forest" />
            <span>Reading document text and structuring resume sections...</span>
          </p>
        </div>
      )}

      {/* Parsing Timed Out Error State */}
      {isParseTimedOut && !resume?.parsed_json && !hasScoreOrReport && (
        <div className="rounded-xl border border-clay-alert/30 bg-clay-alert/10 p-8 space-y-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-clay-alert flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h3 className="font-display text-display-md text-clay-alert">Document Parsing Timed Out</h3>
              <p className="font-body text-body-sm text-ink font-medium">
                The background text parsing process did not complete within 45 seconds. Ensure your Python Arq background worker process (<code className="font-mono text-data bg-paper px-1.5 py-0.5 rounded">python -m app.workers.worker_settings</code>) is running and click retry.
              </p>
            </div>
          </div>
          <div className="flex justify-end pt-2">
            <button
              onClick={() => refetchResume()}
              className="inline-flex items-center gap-2 rounded-md bg-forest px-4 py-2.5 font-body text-body-sm font-medium text-white hover:bg-forest-hover transition-colors cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Retry Checking Resume Status</span>
            </button>
          </div>
        </div>
      )}

      {/* Auto-Scoring Live Job Progress State */}
      {isScoringInProgress && (
        <div className="rounded-xl border border-line bg-paper-raised p-8 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="font-display text-display-md text-ink">Scoring Resume</h3>
              <p className="font-body text-body-sm text-ink-muted">
                Evaluating format readability, structural compliance, and parser accuracy.
              </p>
            </div>
            <span className="px-3 py-1 rounded-md font-mono text-data font-medium bg-paper border border-line text-forest">
              {scoreJobStatus?.status || "processing"}
            </span>
          </div>
          <ContourProgress active={true} />
          <p className="font-body text-body-sm text-ink-muted flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-forest" />
            <span>Scoring your resume against ATS readability standards...</span>
          </p>
        </div>
      )}

      {/* Failed Scoring Error State */}
      {isScoringFailed && !isScoringInProgress && !hasScoreOrReport && (
        <div className="rounded-xl border border-clay-alert/30 bg-clay-alert/10 p-8 space-y-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-clay-alert flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h3 className="font-display text-display-md text-clay-alert">Scoring Couldn't Complete</h3>
              <p className="font-body text-body-sm text-ink font-medium">
                {scoreJobStatus?.result?.error ||
                  "The background scoring process encountered an error. Check that your background worker is running and try again."}
              </p>
            </div>
          </div>
          <div className="flex justify-end pt-2">
            <button
              onClick={handleRetryScoring}
              className="inline-flex items-center gap-2 rounded-md bg-forest px-4 py-2.5 font-body text-body-sm font-medium text-white hover:bg-forest-hover transition-colors cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Retry Scoring</span>
            </button>
          </div>
        </div>
      )}

      {/* Initial Loading Spinner */}
      {isResumeLoading && !isParsingInProgress && !isScoringInProgress && !isParseTimedOut && (
        <div className="p-12 text-center font-body text-body-sm text-ink-muted flex items-center justify-center gap-2">
          <Loader2 className="w-5 h-5 animate-spin text-forest" />
          <span>Loading evaluation data...</span>
        </div>
      )}

      {/* ATS Score Arc Gauge & Grammar Audit Section */}
      {hasScoreOrReport && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
          <AtsScoreGauge
            score={resume?.ats_score ?? report?.ats_breakdown?.overall_score ?? 0}
            breakdown={report?.ats_breakdown}
          />
          <GrammarSuggestionsList suggestions={report?.grammar_suggestions} />
        </div>
      )}

      {/* Target Job Description Analysis Section */}
      <section className="pt-4">
        <TargetJobDescriptionCard
          resumeId={resumeId}
          hasInitialReport={hasScoreOrReport}
          isScoringInProgress={isParsingInProgress || isScoringInProgress}
          isScoringFailed={isScoringFailed || isParseTimedOut}
          keywordGaps={report?.keyword_gaps}
          actionItems={report?.action_items}
          onAnalysisSubmitted={() => {
            refetchReport();
          }}
        />
      </section>
    </div>
  );
}
