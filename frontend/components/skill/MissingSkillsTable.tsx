"use client";

import type { MissingSkillItem } from "@/types/skill";

interface MissingSkillsTableProps {
  missingSkills: MissingSkillItem[];
}

export function MissingSkillsTable({ missingSkills }: MissingSkillsTableProps) {
  const sortedSkills = [...missingSkills].sort(
    (a, b) => b.demand_weight - a.demand_weight
  );

  return (
    <div className="bg-paper-raised rounded-xl p-6 border border-line shadow-sm flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-display text-display-md text-ink">
            Missing Skill Gaps
          </h2>
          <span className="font-mono text-data text-ink-muted">
            {sortedSkills.length} Identified
          </span>
        </div>
        <p className="text-body-sm text-ink-muted mb-6">
          Skills required for your target role ranked by employer demand weight. Focus on high-importance gaps first.
        </p>

        {sortedSkills.length === 0 ? (
          <div className="p-8 text-center bg-paper rounded-md border border-line">
            <p className="text-body text-ink font-medium">No skill gaps identified!</p>
            <p className="text-body-sm text-ink-muted mt-1">
              Your resume skills closely match the requirements for this role.
            </p>
          </div>
        ) : (
          <div className="space-y-4 max-h-[380px] overflow-y-auto pr-1">
            {sortedSkills.map((item, idx) => {
              const weightPct = Math.round(item.demand_weight * 100);
              const importanceLower = (item.importance || "medium").toLowerCase();

              let badgeStyle = "bg-teal/15 text-teal border-teal/30";
              if (importanceLower === "high") {
                badgeStyle = "bg-brass-soft text-ink border-brass/40";
              } else if (importanceLower === "low") {
                badgeStyle = "bg-line/40 text-ink-muted border-line";
              }

              return (
                <div
                  key={`${item.skill}-${idx}`}
                  className="p-4 rounded-md bg-paper border border-line hover:border-teal/50 transition-colors"
                >
                  <div className="flex items-center justify-between gap-4 mb-2">
                    <span className="font-mono text-body font-semibold text-ink">
                      {item.skill}
                    </span>
                    <div className="flex items-center gap-3">
                      <span
                        className={`font-mono text-xs px-2.5 py-0.5 rounded-md font-medium border uppercase tracking-wider ${badgeStyle}`}
                      >
                        {item.importance}
                      </span>
                      <span className="font-mono text-data text-ink font-bold">
                        {weightPct}%
                      </span>
                    </div>
                  </div>

                  {/* Demand Weight Bar */}
                  <div className="w-full bg-line/60 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        importanceLower === "high" ? "bg-brass" : "bg-teal"
                      }`}
                      style={{ width: `${weightPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
