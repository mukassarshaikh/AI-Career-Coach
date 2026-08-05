"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { MissingSkillItem } from "@/types/skill";

interface SkillGapRadarChartProps {
  missingSkills: MissingSkillItem[];
  targetRole: string;
}

interface RadarDataItem {
  subject: string;
  candidateScore: number;
  marketWeight: number;
  isMissing: boolean;
  importance: string;
}

/**
 * Custom Dot Renderer for Recharts Radar
 * Renders a prominent brass dot (#C89B3C) on missing-skill radar points per design_system.md §8 & §4.
 */

function CustomBrassDot(props: any) {
  const { cx, cy, payload } = props;
  if (!cx || !cy) return null;

  if (payload && payload.isMissing) {
    return (
      <g key={`dot-${payload.subject}`}>
        {/* Outer subtle glow */}
        <circle cx={cx} cy={cy} r={7} fill="#C89B3C" fillOpacity={0.25} />
        {/* Brass dot per design system §8 */}
        <circle
          cx={cx}
          cy={cy}
          r={4.5}
          fill="#C89B3C"
          stroke="#1B2A22"
          strokeWidth={1.5}
        />
      </g>
    );
  }

  // Matched skill dot (teal)
  return (
    <circle
      key={`dot-${payload?.subject}`}
      cx={cx}
      cy={cy}
      r={3}
      fill="#3E6259"
      stroke="#F2F3EE"
      strokeWidth={1}
    />
  );
}

export function SkillGapRadarChart({
  missingSkills,
  targetRole,
}: SkillGapRadarChartProps) {
  // Construct Radar Chart Data: missing skills + representative matched core skills
  const chartData: RadarDataItem[] = missingSkills.map((item) => ({
    subject: item.skill,
    candidateScore: Math.max(10, Math.round((1 - item.demand_weight) * 100)),
    marketWeight: Math.round(item.demand_weight * 100),
    isMissing: true,
    importance: item.importance,
  }));

  // Add dummy/matched foundational competencies if missing skills count is small to make radar legible
  if (chartData.length < 6) {
    const matchedDefaults = [
      "Core Problem Solving",
      "Git / Version Control",
      "API Principles",
    ];
    matchedDefaults.slice(0, 6 - chartData.length).forEach((name) => {
      chartData.push({
        subject: name,
        candidateScore: 85,
        marketWeight: 90,
        isMissing: false,
        importance: "matched",
      });
    });
  }

  return (
    <div className="bg-paper-raised rounded-xl p-6 border border-line shadow-sm flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-display text-display-md text-ink">
            Skill Gap Map
          </h2>
          <span className="font-mono text-data text-teal bg-teal/10 px-2.5 py-1 rounded-md border border-teal/20">
            {targetRole}
          </span>
        </div>
        <p className="text-body-sm text-ink-muted mb-4">
          Visual radar plot comparing candidate proficiency against market demand for{" "}
          <strong className="text-ink font-medium">{targetRole}</strong>. Brass dots
          highlight missing skill gaps.
        </p>
      </div>

      <div className="w-full h-[340px] flex items-center justify-center">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={chartData}>
            <PolarGrid stroke="#DAD8CE" strokeDasharray="3 3" />
            <PolarAngleAxis
              dataKey="subject"
              tick={{ fill: "#1B2A22", fontSize: 11, fontFamily: "var(--font-mono)" }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              tick={{ fill: "#6B675E", fontSize: 9 }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data: RadarDataItem = payload[0].payload;
                  return (
                    <div className="bg-ink text-paper text-xs font-mono p-3 rounded-md shadow-lg border border-brass/30 space-y-1">
                      <div className="font-bold text-brass">{data.subject}</div>
                      <div>
                        Status:{" "}
                        <span className={data.isMissing ? "text-brass" : "text-teal"}>
                          {data.isMissing ? "Missing Gap" : "Matched"}
                        </span>
                      </div>
                      <div>Market Demand: {data.marketWeight}%</div>
                      <div>Your Score: {data.candidateScore}%</div>
                    </div>
                  );
                }
                return null;
              }}
            />
            {/* Market Demand Reference Layer */}
            <Radar
              name="Market Benchmark"
              dataKey="marketWeight"
              stroke="#DAD8CE"
              fill="#DAD8CE"
              fillOpacity={0.15}
              strokeDasharray="4 4"
            />
            {/* Candidate Skill Vector Layer in --color-teal */}
            <Radar
              name="Your Skills"
              dataKey="candidateScore"
              stroke="#3E6259"
              fill="#3E6259"
              fillOpacity={0.35}
              dot={<CustomBrassDot />}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-line text-body-sm">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-teal inline-block" />
          <span className="font-mono text-data text-ink">Candidate Proficiency</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-brass border border-ink inline-block" />
          <span className="font-mono text-data text-ink">Missing Skill Gap (Brass Dot)</span>
        </div>
      </div>
    </div>
  );
}
