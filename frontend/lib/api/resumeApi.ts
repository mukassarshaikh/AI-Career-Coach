import { fetchWithAuth } from "./client";
import type {
  JobStatusResponse,
  ResumeReportResponse,
  ResumeResponse,
  ResumeUploadResponse,
  ScoreResumeResponse,
  SubmitJobDescriptionResponse,
} from "@/types/resume";

export async function uploadResumeFile(file: File): Promise<ResumeUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return fetchWithAuth<ResumeUploadResponse>("/api/v1/resume/upload", {
    method: "POST",
    body: formData,
  });
}

export async function listResumes(): Promise<ResumeResponse[]> {
  return fetchWithAuth<ResumeResponse[]>("/api/v1/resume", {
    method: "GET",
  });
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  return fetchWithAuth<JobStatusResponse>(`/api/v1/resume/jobs/${jobId}`, {
    method: "GET",
  });
}

export async function getResume(resumeId: string): Promise<ResumeResponse> {
  return fetchWithAuth<ResumeResponse>(`/api/v1/resume/${resumeId}`, {
    method: "GET",
  });
}

export async function scoreResume(resumeId: string): Promise<ScoreResumeResponse> {
  return fetchWithAuth<ScoreResumeResponse>(`/api/v1/resume/${resumeId}/score`, {
    method: "POST",
  });
}

export async function submitJobDescription(
  resumeId: string,
  rawText: string
): Promise<SubmitJobDescriptionResponse> {
  return fetchWithAuth<SubmitJobDescriptionResponse>(`/api/v1/resume/${resumeId}/job-description`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_text: rawText }),
  });
}

export async function getResumeReport(resumeId: string): Promise<ResumeReportResponse> {
  return fetchWithAuth<ResumeReportResponse>(`/api/v1/resume/${resumeId}/report`, {
    method: "GET",
  });
}
