"use client";

/**
 * Resume Page — Upload + List Resumes
 * Per frontend_architecture.md §1: /app/(dashboard)/resume/page.tsx
 */

import Link from "next/link";
import { ResumeUploadCard } from "@/components/resume";
import { useResumeList } from "@/lib/hooks/useResume";

export default function ResumePage() {
  const { data: resumes, isLoading, refetch } = useResumeList();

  const handleUploadSuccess = () => {
    refetch();
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">Resume Management</h1>
        <p className="text-sm text-slate-400">
          Upload new resumes, monitor parsing status, and view ATS compatibility reports.
        </p>
      </div>

      {/* Upload Card */}
      <section>
        <ResumeUploadCard onUploadSuccess={handleUploadSuccess} />
      </section>

      {/* Resume History List */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-100">Your Resumes</h2>
          <span className="text-xs text-slate-500">{resumes?.length || 0} total uploaded</span>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-xs text-slate-400 animate-pulse">
            Loading your resumes from database...
          </div>
        ) : !resumes || resumes.length === 0 ? (
          <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-8 text-center space-y-2">
            <p className="text-sm font-medium text-slate-300">No resumes uploaded yet</p>
            <p className="text-xs text-slate-500">
              Upload a PDF or Word document above to start evaluating your resume against ATS benchmarks.
            </p>
          </div>
        ) : (
          <div className="grid gap-3">
            {resumes.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/80 p-4 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 text-lg">
                    📄
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-200">
                      Resume ({item.id.substring(0, 8)}...)
                    </p>
                    <p className="text-xs text-slate-400">
                      Uploaded on {new Date(item.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {item.ats_score !== null && item.ats_score !== undefined && (
                    <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      ATS: {item.ats_score}/100
                    </span>
                  )}
                  <Link
                    href={`/resume/${item.id}`}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-colors"
                  >
                    View Report →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
