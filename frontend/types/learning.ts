/**
 * Learning / roadmap types — mirrors backend Pydantic schemas.
 */

export type RoadmapStatus = "active" | "completed" | "archived";
export type RoadmapItemStatus = "not_started" | "in_progress" | "completed";
export type RoadmapItemType = "course" | "article" | "project" | "milestone";
export type RoadmapItemDifficulty = "beginner" | "intermediate" | "advanced";

export interface RoadmapItem {
  id: string;
  roadmap_id: string;
  skill_name: string;
  type: RoadmapItemType;
  title: string;
  description?: string | null;
  url?: string | null;
  sequence_order: number;
  difficulty: RoadmapItemDifficulty;
  status: RoadmapItemStatus;
  completed_at?: string | null;
}

export interface Roadmap {
  id: string;
  user_id: string;
  skill_gap_report_id: string;
  status: RoadmapStatus;
  created_at: string;
  updated_at: string;
  items: RoadmapItem[];
}

export interface RoadmapItemUpdateResponse {
  item: RoadmapItem;
  job_id: string | null;
  message: string;
}

export interface GenerateRoadmapResponse {
  skill_gap_report_id: string;
  job_id: string;
  message: string;
}
