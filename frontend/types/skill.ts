/**
 * Skill types — mirrors backend Pydantic schemas.
 * Filled out in Phase 1.
 */

export interface SkillVector {
  id: string;
  userId: string;
  resumeId?: string | null;
  rawSkills?: SkillWithConfidence[] | null;
  createdAt: string;
  updatedAt: string;
}

export interface SkillWithConfidence {
  name: string;
  confidence: number;
  source: string;
}

export interface SkillGapReport {
  id: string;
  userId: string;
  skillVectorId: string;
  targetRole: string;
  missingSkills: MissingSkill[];
  createdAt: string;
}

export interface MissingSkill {
  skill: string;
  demandWeight: number;
  relevanceScore: number;
}
