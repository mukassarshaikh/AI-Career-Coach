import { fetchWithAuth } from "./client";

export interface GenerateRoadmapResponse {
  skill_gap_report_id: string;
  job_id: string;
  message: string;
}

export async function generateRoadmap(
  skillGapReportId: string
): Promise<GenerateRoadmapResponse> {
  return fetchWithAuth<GenerateRoadmapResponse>("/api/v1/learning/roadmap", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ skill_gap_report_id: skillGapReportId }),
  });
}
