"use client";

/**
 * Resume Detail / Report Page (Stub)
 * Restyled matching design_system.md (§1, §2, §3, §5).
 */

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Loader2, FileText } from "lucide-react";
import { useResume, useResumeReport } from "@/lib/hooks/useResume";

export default function ResumeDetailPage() {
  const params = useParams();
  const resumeId = params?.id as string;

  const { data: resume, isLoading: isResumeLoading } = useResume(resumeId);
  const { data: report, isLoading: isReportLoading } = useResumeReport(resumeId);

  return (
    <div className="space-y-8 max-w-4xl mx-auto pb-16">
      <div className="flex items-center justify-between">
        <Link
          href="/resume"
          className="font-body text-body-sm text-forest hover:underline flex items-center gap-1.5 font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Resume Upload</span>
        </Link>
        <span className="font-mono text-data text-ink-muted">ID: {resumeId}</span>
      </div>

      <div className="rounded-xl border border-line bg-paper-raised p-8 space-y-6 shadow-sm">
        <div className="flex items-center justify-between border-b border-line pb-5">
          <div>
            <h1 className="font-display text-display-md text-ink">Resume Evaluation & ATS Report</h1>
            <p className="font-body text-body-sm text-ink-muted">Detailed breakdown, grammar audit, and target job description analysis.</p>
          </div>
          <span className="px-3 py-1 rounded-md font-mono text-data font-semibold bg-brass-soft/50 text-ink border border-brass/30">
            Next Story Target
          </span>
        </div>

        {isResumeLoading || isReportLoading ? (
          <div className="p-10 text-center font-body text-body-sm text-ink-muted flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-forest" />
            <span>Loading resume evaluation from server...</span>
          </div>
        ) : (
          <div className="space-y-6 pt-2">
            <div className="grid grid-cols-2 gap-5">
              <div className="p-5 rounded-xl bg-paper border border-line space-y-1.5">
                <p className="font-body text-body-sm font-medium text-ink-muted">Overall ATS Score</p>
                <p className="font-mono text-data-lg font-bold text-forest">
                  {resume?.ats_score ?? report?.ats_breakdown?.overall_score ?? "N/A"} / 100
                </p>
              </div>

              <div className="p-5 rounded-xl bg-paper border border-line space-y-1.5">
                <p className="font-body text-body-sm font-medium text-ink-muted flex items-center gap-2">
                  <FileText className="w-4 h-4 text-forest" />
                  <span>Cloudinary Storage URL</span>
                </p>
                <a
                  href={resume?.file_url}
                  target="_blank"
                  rel="noreferrer"
                  className="font-mono text-data text-forest hover:underline truncate block"
                >
                  {resume?.file_url || "Cloudinary URL"}
                </a>
              </div>
            </div>

            <div className="rounded-xl bg-brass-soft/30 border border-brass/30 p-5 text-body-sm text-ink">
              <p className="font-body font-semibold text-body mb-1">Navigation Target Verified</p>
              <p className="font-body text-ink-muted">
                The full ATS score arc gauge, grammar suggestions audit cards, and target job description keyword gap input will be built in Frontend Story 2.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
