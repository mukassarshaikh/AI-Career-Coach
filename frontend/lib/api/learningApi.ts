import { fetchWithAuth } from "./client";
import type {
  GenerateRoadmapResponse,
  Roadmap,
  RoadmapItemStatus,
  RoadmapItemUpdateResponse,
} from "@/types/learning";

export async function getActiveRoadmap(): Promise<Roadmap> {
  return fetchWithAuth<Roadmap>("/api/v1/learning/roadmap", {
    method: "GET",
  });
}

export async function getRoadmap(id: string): Promise<Roadmap> {
  return fetchWithAuth<Roadmap>(`/api/v1/learning/roadmap/${id}`, {
    method: "GET",
  });
}

export async function updateRoadmapItem(
  itemId: string,
  status: RoadmapItemStatus
): Promise<RoadmapItemUpdateResponse> {
  return fetchWithAuth<RoadmapItemUpdateResponse>(
    `/api/v1/learning/roadmap-item/${itemId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }
  );
}

export async function regenerateRoadmap(
  roadmapId: string
): Promise<GenerateRoadmapResponse> {
  return fetchWithAuth<GenerateRoadmapResponse>(
    `/api/v1/learning/roadmap/${roadmapId}/regenerate`,
    {
      method: "POST",
    }
  );
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
