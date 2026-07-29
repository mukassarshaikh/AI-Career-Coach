/**
 * Dashboard types — summary card data shapes.
 * Filled out incrementally as each module ships (per Implementation_plan.md).
 */

export interface DashboardSummary {
  resumeCount: number;
  latestAtsScore?: number | null;
  activeRoadmapCount: number;
  openSkillGaps: number;
  nextActions: NextAction[];
}

export interface NextAction {
  id: string;
  label: string;
  href: string;
  priority: "high" | "medium" | "low";
}
