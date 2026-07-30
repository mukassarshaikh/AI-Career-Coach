"use client";

/**
 * Resume Detail / Report Page (Stub)
 * Navigation target for the next story.
 */

import Link from "next/link";
import { useParams } from "next/navigation";
import { useResume, useResumeReport } from "@/lib/hooks/useResume";

export default function ResumeDetailPage() {
  const params = useParams();
  const resumeId = params?.id as string;

  const { data: resume, isLoading: isResumeLoading } = useResume(resumeId);
  const { data: report, isLoading: isReportLoading } = useResumeReport(resumeId);

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      <div className="flex items-center justify-between">
        <Link
          href="/resume"
          className="text-xs text-indigo-400 hover:underline flex items-center gap-1 font-medium"
        >
          ← Back to Resume Upload
        </Link>
        <span className="text-xs text-slate-500 font-mono">ID: {resumeId}</span>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-xl font-bold text-slate-100">Resume Evaluation & ATS Report</h1>
            <p className="text-xs text-slate-400">Detailed breakdown, grammar audit, and target job description analysis.</p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
            Phase 1 Story 2 (Next Story)
          </span>
        </div>

        {isResumeLoading || isReportLoading ? (
          <div className="p-8 text-center text-xs text-slate-400 animate-pulse">
            Loading resume details from backend API...
          </div>
        ) : (
          <div className="space-y-4 pt-2">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                <p className="text-xs text-slate-400 font-medium">Overall ATS Score</p>
                <p className="text-3xl font-extrabold text-emerald-400">
                  {resume?.ats_score ?? report?.ats_breakdown?.overall_score ?? "N/A"} / 100
                </p>
              </div>

              <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                <p className="text-xs text-slate-400 font-medium">File Storage</p>
                <a
                  href={resume?.file_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-indigo-400 hover:underline truncate block"
                >
                  {resume?.file_url || "Cloudinary Storage URL"}
                </a>
              </div>
            </div>

            <div className="rounded-lg bg-indigo-500/10 border border-indigo-500/20 p-4 text-xs text-indigo-300">
              <p className="font-semibold text-sm mb-1">Navigation Target Ready!</p>
              <p>
                The full ATS score gauge, grammar suggestions list, and job description keyword gap input will be built in the next story.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
