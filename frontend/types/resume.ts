/**
 * Resume types — mirrors backend Pydantic schemas.
 * Filled out fully in Phase 1.
 */

export interface Resume {
  id: string;
  userId: string;
  fileUrl: string;
  rawText?: string | null;
  parsedJson?: Record<string, unknown> | null;
  atsScore?: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface JobDescription {
  id: string;
  userId: string;
  resumeId?: string | null;
  rawText: string;
  parsedKeywords?: Record<string, unknown> | null;
  createdAt: string;
}

export interface ResumeReport {
  id: string;
  resumeId: string;
  jobDescriptionId?: string | null;
  atsBreakdown?: Record<string, unknown> | null;
  grammarSuggestions?: unknown[] | null;
  keywordGaps?: unknown[] | null;
  actionItems?: unknown[] | null;
  createdAt: string;
}

export type JobStatus = "pending" | "processing" | "complete" | "failed";

export interface AsyncJobResponse {
  jobId: string;
  status: JobStatus;
}
