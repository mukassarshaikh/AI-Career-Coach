/**
 * Learning / roadmap types — mirrors backend Pydantic schemas.
 * Filled out in Phase 2.
 */

export type RoadmapStatus = "active" | "completed" | "archived";
export type RoadmapItemStatus = "not_started" | "in_progress" | "completed";
export type RoadmapItemType = "course" | "article" | "project" | "milestone";
export type RoadmapItemDifficulty = "beginner" | "intermediate" | "advanced";

export interface Roadmap {
  id: string;
  userId: string;
  skillGapReportId: string;
  status: RoadmapStatus;
  createdAt: string;
  updatedAt: string;
  items?: RoadmapItem[];
}

export interface RoadmapItem {
  id: string;
  roadmapId: string;
  skillName: string;
  type: RoadmapItemType;
  title: string;
  description?: string | null;
  url?: string | null;
  sequenceOrder: number;
  difficulty: RoadmapItemDifficulty;
  status: RoadmapItemStatus;
  completedAt?: string | null;
}
