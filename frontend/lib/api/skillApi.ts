import { fetchWithAuth } from "./client";
import type {
  ComputeSkillGapResponse,
  GenerateSkillVectorResponse,
  SkillGapReportResponse,
} from "@/types/skill";

export async function generateSkillVector(
  resumeId: string
): Promise<GenerateSkillVectorResponse> {
  return fetchWithAuth<GenerateSkillVectorResponse>("/api/v1/skill/vector", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume_id: resumeId }),
  });
}

export async function generateSkillGapReport(
  targetRole: string
): Promise<ComputeSkillGapResponse> {
  return fetchWithAuth<ComputeSkillGapResponse>("/api/v1/skill/gap-report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_role: targetRole }),
  });
}

export async function refreshSkillGapReport(
  targetRole: string
): Promise<ComputeSkillGapResponse> {
  return fetchWithAuth<ComputeSkillGapResponse>("/api/v1/skill/gap-report/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_role: targetRole }),
  });
}

export async function getSkillGapReport(): Promise<SkillGapReportResponse> {
  return fetchWithAuth<SkillGapReportResponse>("/api/v1/skill/gap-report", {
    method: "GET",
  });
}

export async function getAvailableRoles(): Promise<string[]> {
  return fetchWithAuth<string[]>("/api/v1/skill/roles", {
    method: "GET",
  });
}

