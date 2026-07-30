"use client";

import { useState } from "react";
import Link from "next/link";
import { uploadResumeFile } from "@/lib/api/resumeApi";
import { useJobStatus } from "@/lib/hooks/useJobStatus";
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
  const { data: jobStatus, isLoading: isJobStatusLoading } = useJobStatus(
    uploadResult?.job_id || null
  );

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
      setUploadError("Invalid file type. Please upload a PDF (.pdf) or Word document (.docx).");
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
      setUploadError(err.message || "Failed to upload resume file.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-6 shadow-xl backdrop-blur max-w-2xl mx-auto space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-bold text-slate-100">Upload Your Resume</h2>
        <p className="text-xs text-slate-400">
          Upload your latest resume (PDF or DOCX) to get instant ATS scoring, grammar audits, and skill-gap analysis.
        </p>
      </div>

      {!uploadResult ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition-all ${
              isDragging
                ? "border-indigo-500 bg-indigo-500/10"
                : file
                ? "border-emerald-500/50 bg-emerald-500/5"
                : "border-slate-800 hover:border-slate-700 bg-slate-900/50"
            }`}
          >
            <input
              id="resume-file-input"
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileChange}
              className="absolute inset-0 cursor-pointer opacity-0"
            />

            <div className="w-12 h-12 rounded-full bg-slate-800/80 flex items-center justify-center text-indigo-400 mb-3">
              📄
            </div>

            {file ? (
              <div className="space-y-1">
                <p className="text-sm font-semibold text-emerald-400">{file.name}</p>
                <p className="text-xs text-slate-400">
                  {(file.size / 1024 / 1024).toFixed(2)} MB • Ready to upload
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                <p className="text-sm font-medium text-slate-200">
                  <span className="font-semibold text-indigo-400">Click to upload</span> or drag and drop
                </p>
                <p className="text-xs text-slate-500">PDF or Word (.docx) up to 10MB</p>
              </div>
            )}
          </div>

          {uploadError && (
            <div className="rounded-lg bg-rose-500/10 border border-rose-500/20 p-3 text-xs text-rose-400">
              {uploadError}
            </div>
          )}

          <div className="flex justify-end gap-3">
            {file && (
              <button
                type="button"
                onClick={() => setFile(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
              >
                Clear
              </button>
            )}
            <button
              id="upload-resume-btn"
              type="submit"
              disabled={!file || isUploading}
              className="rounded-lg bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 disabled:opacity-50 transition-all cursor-pointer flex items-center gap-2"
            >
              {isUploading ? (
                <>
                  <span className="animate-spin">⏳</span> Uploading...
                </>
              ) : (
                "Upload Resume"
              )}
            </button>
          </div>
        </form>
      ) : (
        /* Live Polling Status View */
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-200">Processing Resume</h3>
                <p className="text-xs text-slate-400">ID: {uploadResult.resume_id}</p>
              </div>
              <span
                className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                  jobStatus?.status === "complete"
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                    : jobStatus?.status === "failed"
                    ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                    : "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 animate-pulse"
                }`}
              >
                {jobStatus?.status || "queued"}
              </span>
            </div>

            {/* Live Progress Banner */}
            {jobStatus?.status === "queued" && (
              <div className="flex items-center gap-3 p-3 rounded-lg bg-indigo-500/10 text-xs text-indigo-300">
                <span className="animate-spin text-base">⏳</span>
                <span>Job queued. Waiting for worker process to extract text...</span>
              </div>
            )}

            {jobStatus?.status === "in_progress" && (
              <div className="flex items-center gap-3 p-3 rounded-lg bg-indigo-500/10 text-xs text-indigo-300">
                <span className="animate-spin text-base">🔄</span>
                <span>Extracting text & structuring resume via Groq LLM...</span>
              </div>
            )}

            {jobStatus?.status === "complete" && (
              <div className="space-y-4">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-emerald-500/10 text-xs text-emerald-300 border border-emerald-500/20">
                  <span className="text-base">✅</span>
                  <span>Resume parsed and structured successfully!</span>
                </div>

                <div className="flex justify-between items-center pt-2">
                  <button
                    onClick={() => {
                      setUploadResult(null);
                      setFile(null);
                    }}
                    className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    Upload Another Resume
                  </button>

                  <Link
                    id="view-resume-report-link"
                    href={`/resume/${uploadResult.resume_id}`}
                    className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-emerald-600/30 hover:bg-emerald-500 transition-all"
                  >
                    View Resume & Report →
                  </Link>
                </div>
              </div>
            )}

            {jobStatus?.status === "failed" && (
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-rose-500/10 text-xs text-rose-300 border border-rose-500/20">
                  Processing failed: {jobStatus.result?.error || "Unknown worker error"}
                </div>
                <button
                  onClick={() => {
                    setUploadResult(null);
                    setFile(null);
                  }}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800 text-slate-200 hover:bg-slate-700 transition-colors"
                >
                  Try Uploading Again
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
