"use client";

/**
 * Resume Management Page — Upload & Resume List.
 * Restyled matching design_system.md (§1, §2, §3, §5, §6).
 */

import Link from "next/link";
import { FileText, ArrowRight, Loader2 } from "lucide-react";
import { ResumeUploadCard } from "@/components/resume";
import { useResumeList } from "@/lib/hooks/useResume";

export default function ResumePage() {
  const { data: resumes, isLoading, refetch } = useResumeList();

  const handleUploadSuccess = () => {
    refetch();
  };

  return (
    <div className="space-y-10 max-w-5xl mx-auto pb-16">
      {/* Page Header */}
      <div className="space-y-2">
        <h1 className="font-display text-display-lg tracking-tight text-ink">
          Resume Management
        </h1>
        <p className="font-body text-body text-ink-muted max-w-2xl">
          Upload your resume to evaluate ATS score, audit grammar, and analyze skill coverage against target job roles.
        </p>
      </div>

      {/* Resume Upload Card Component */}
      <section>
        <ResumeUploadCard onUploadSuccess={handleUploadSuccess} />
      </section>

      {/* Resume History List Section */}
      <section className="space-y-5 pt-4 border-t border-line">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-display-md text-ink">Your Resumes</h2>
          <span className="font-mono text-data text-ink-muted">
            {resumes?.length || 0} total uploaded
          </span>
        </div>

        {isLoading ? (
          <div className="p-10 text-center font-body text-body-sm text-ink-muted flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-forest" />
            <span>Loading your resume history...</span>
          </div>
        ) : !resumes || resumes.length === 0 ? (
          /* Empty State per design_system.md §5 & §6 */
          <div className="rounded-xl border border-line bg-paper-raised p-10 text-center space-y-2 shadow-sm">
            <p className="font-body text-body font-medium text-ink">No resumes uploaded yet</p>
            <p className="font-body text-body-sm text-ink-muted">
              Upload your first resume to get an ATS score and skill-gap report.
            </p>
          </div>
        ) : (
          <div className="grid gap-3.5">
            {resumes.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between rounded-xl border border-line bg-paper-raised p-5 shadow-sm hover:border-forest/40 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-md bg-paper flex items-center justify-center text-forest border border-line">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-mono text-data font-semibold text-ink">
                      Resume ({item.id.substring(0, 8)}...)
                    </p>
                    <p className="font-mono text-data text-ink-muted">
                      Uploaded {new Date(item.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {item.ats_score !== null && item.ats_score !== undefined && (
                    <span className="px-3 py-1 rounded-md font-mono text-data font-semibold bg-brass-soft/50 text-ink border border-brass/30">
                      ATS: {item.ats_score}/100
                    </span>
                  )}
                  <Link
                    href={`/resume/${item.id}`}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-paper border border-line text-ink hover:bg-paper-raised font-body text-body-sm font-medium transition-colors"
                  >
                    <span>View report</span>
                    <ArrowRight className="w-3.5 h-3.5" />
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
