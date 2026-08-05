/**
 * Skill Intelligence TypeScript types — mirrors backend Pydantic schemas.
 */

export interface GenerateSkillVectorRequest {
  resume_id: string;
}

export interface GenerateSkillVectorResponse {
  resume_id: string;
  job_id: string;
  message: string;
}

export interface ComputeSkillGapRequest {
  target_role: string;
}

export interface ComputeSkillGapResponse {
  target_role: string;
  job_id: string;
  message: string;
}

export interface MissingSkillItem {
  skill: string;
  demand_weight: number;
  importance: "high" | "medium" | "low" | string;
  status: string;
}

export interface SkillGapReportResponse {
  id: string;
  user_id: string;
  skill_vector_id: string;
  target_role: string;
  missing_skills: MissingSkillItem[];
  created_at: string;
}

// Backward compatibility interfaces
export type SkillGapReport = SkillGapReportResponse;
export type MissingSkill = MissingSkillItem;
