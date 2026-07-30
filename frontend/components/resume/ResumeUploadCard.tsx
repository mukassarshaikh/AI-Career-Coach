"use client";

/**
 * ResumeUploadCard — Drag-and-drop file upload & live status polling card.
 * Restyled matching design_system.md (§1, §2, §3, §4, §5, §6).
 */

import { useState } from "react";
import Link from "next/link";
import { UploadCloud, CheckCircle2, AlertTriangle, FileText, Loader2 } from "lucide-react";
import { uploadResumeFile } from "@/lib/api/resumeApi";
import { useJobStatus } from "@/lib/hooks/useJobStatus";
import { ContourProgress } from "@/components/ui/ContourProgress";
import type { ResumeUploadResponse } from "@/types/resume";

interface ResumeUploadCardProps {
  onUploadSuccess?: (res: ResumeUploadResponse) => void;
}

export function ResumeUploadCard({ onUploadSuccess }: ResumeUploadCardProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<ResumeUploadResponse | null>(null);

  // Poll background job status if upload returned a job_id
  const { data: jobStatus } = useJobStatus(uploadResult?.job_id || null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    setUploadError(null);
    const ext = selectedFile.name.split(".").pop()?.toLowerCase();
    if (ext !== "pdf" && ext !== "docx") {
      setUploadError("That file format isn't supported. Upload a PDF or Word (.docx) file under 10MB.");
      setFile(null);
      return;
    }
    setFile(selectedFile);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setIsUploading(true);
    setUploadError(null);

    try {
      const res = await uploadResumeFile(file);
      setUploadResult(res);
      if (onUploadSuccess) {
        onUploadSuccess(res);
      }
    } catch (err: any) {
      setUploadError(err.message || "Could not upload resume file. Try again.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="rounded-xl border border-line bg-paper-raised p-8 shadow-sm max-w-2xl mx-auto space-y-6">
      <div className="space-y-1.5">
        <h2 className="font-display text-display-md text-ink">Upload your resume</h2>
        <p className="font-body text-body-sm text-ink-muted">
          Upload a PDF or Word (.docx) document under 10MB to evaluate ATS score, audit grammar, and analyze skill coverage.
        </p>
      </div>

      {!uploadResult ? (
        <form onSubmit={handleSubmit} className="space-y-5">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition-all ${
              isDragging
                ? "border-forest bg-brass-soft/20"
                : file
                ? "border-forest bg-brass-soft/10"
                : "border-line hover:border-forest/40 bg-paper/50"
            }`}
          >
            <input
              id="resume-file-input"
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileChange}
              className="absolute inset-0 cursor-pointer opacity-0"
            />

            <div className="w-12 h-12 rounded-full bg-paper flex items-center justify-center text-forest mb-3 border border-line">
              {file ? <FileText className="w-6 h-6" /> : <UploadCloud className="w-6 h-6" />}
            </div>

            {file ? (
              <div className="space-y-1">
                <p className="font-mono text-data font-semibold text-ink">{file.name}</p>
                <p className="font-mono text-data text-ink-muted">
                  {(file.size / 1024 / 1024).toFixed(2)} MB • Ready to upload
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                <p className="font-body text-body-sm font-medium text-ink">
                  <span className="font-semibold text-forest underline underline-offset-2">Select a file</span> or drag and drop here
                </p>
                <p className="font-body text-body-sm text-ink-muted">PDF or Word (.docx) up to 10MB</p>
              </div>
            )}
          </div>

          {uploadError && (
            <div className="rounded-md bg-clay-alert/10 border border-clay-alert/20 p-3.5 text-body-sm font-medium text-clay-alert flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            {file && (
              <button
                type="button"
                onClick={() => setFile(null)}
                className="px-4 py-2 font-body text-body-sm font-medium text-ink-muted hover:text-ink transition-colors cursor-pointer"
              >
                Clear
              </button>
            )}
            <button
              id="upload-resume-btn"
              type="submit"
              disabled={!file || isUploading}
              className="rounded-md bg-forest px-5 py-2.5 font-body text-body-sm font-medium text-white shadow-sm hover:bg-forest-hover disabled:opacity-50 transition-colors cursor-pointer flex items-center gap-2"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                "Upload resume"
              )}
            </button>
          </div>
        </form>
      ) : (
        /* Live Job Polling Status View */
        <div className="space-y-6">
          <div className="rounded-xl border border-line bg-paper/60 p-6 space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-display text-body-lg font-medium text-ink">Processing resume</h3>
                <p className="font-mono text-data text-ink-muted">ID: {uploadResult.resume_id}</p>
              </div>
              <span
                className={`px-3 py-1 rounded-md font-mono text-data font-medium ${
                  jobStatus?.status === "complete"
                    ? "bg-brass-soft text-ink border border-brass/30"
                    : jobStatus?.status === "failed"
                    ? "bg-clay-alert/10 text-clay-alert border border-clay-alert/20"
                    : "bg-paper border border-line text-forest"
                }`}
              >
                {jobStatus?.status || "queued"}
              </span>
            </div>

            {/* Signature Contour-Line Progress Bar (design_system.md §4) */}
            {(jobStatus?.status === "queued" || jobStatus?.status === "in_progress" || !jobStatus) && (
              <div className="space-y-3">
                <ContourProgress active={true} />
                <p className="font-body text-body-sm text-ink-muted flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-forest" />
                  <span>
                    {jobStatus?.status === "in_progress"
                      ? "Reading and structuring your resume"
                      : "Queued for processing"}
                  </span>
                </p>
              </div>
            )}

            {jobStatus?.status === "complete" && (
              <div className="space-y-5 pt-1">
                <div className="flex items-center gap-3 p-4 rounded-md bg-brass-soft/40 border border-brass/30 text-body-sm text-ink font-medium">
                  <CheckCircle2 className="w-5 h-5 text-forest flex-shrink-0" />
                  <span>Resume parsed and structured successfully.</span>
                </div>

                <div className="flex justify-between items-center pt-2 border-t border-line">
                  <button
                    onClick={() => {
                      setUploadResult(null);
                      setFile(null);
                    }}
                    className="font-body text-body-sm font-medium text-ink-muted hover:text-ink transition-colors cursor-pointer"
                  >
                    Upload another resume
                  </button>

                  <Link
                    id="view-resume-report-link"
                    href={`/resume/${uploadResult.resume_id}`}
                    className="inline-flex items-center gap-2 rounded-md bg-forest px-4 py-2 font-body text-body-sm font-medium text-white shadow-sm hover:bg-forest-hover transition-colors"
                  >
                    <span>View report</span>
                    <span>→</span>
                  </Link>
                </div>
              </div>
            )}

            {jobStatus?.status === "failed" && (
              <div className="space-y-4 pt-1">
                <div className="p-4 rounded-md bg-clay-alert/10 border border-clay-alert/20 text-body-sm font-medium text-clay-alert flex items-start gap-2.5">
                  <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <span>
                    That file couldn't be processed. {jobStatus.result?.error || "Check the file format and try again."}
                  </span>
                </div>
                <div className="flex justify-end">
                  <button
                    onClick={() => {
                      setUploadResult(null);
                      setFile(null);
                    }}
                    className="px-4 py-2 font-body text-body-sm font-medium rounded-md bg-paper border border-line text-ink hover:bg-paper-raised transition-colors cursor-pointer"
                  >
                    Try uploading again
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
