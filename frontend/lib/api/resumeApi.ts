import { fetchWithAuth } from "./client";
import type {
  JobStatusResponse,
  ResumeReportResponse,
  ResumeResponse,
  ResumeUploadResponse,
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

export async function getResumeReport(resumeId: string): Promise<ResumeReportResponse> {
  return fetchWithAuth<ResumeReportResponse>(`/api/v1/resume/${resumeId}/report`, {
    method: "GET",
  });
}
