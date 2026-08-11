/**
 * Dashboard summary types — matches GET /api/v1/dashboard/summary backend schema.
 */

export interface DashboardSummary {
  resume_score: number | null;
  missing_skills_count: number;
  target_role: string | null;
  roadmap_total_items: number;
  roadmap_completed_items: number;
  roadmap_completion_percentage: number;
  active_roadmap_id: string | null;
}
