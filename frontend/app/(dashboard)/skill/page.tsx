import type { Metadata } from "next";

export const metadata: Metadata = { title: "Skill Gap Report" };

export default function SkillPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-foreground">Skill Gap Report</h1>
      <p className="text-muted-foreground mt-2">
        Radar chart and missing skills table. (Implemented in Phase 1)
      </p>
    </div>
  );
}
