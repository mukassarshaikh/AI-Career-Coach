"use client";

/**
 * AtsScoreGauge — Semi-circle arc gauge with contour-line stroke style per design_system.md §4 & §8.
 */

import type { AtsBreakdown } from "@/types/resume";

interface AtsScoreGaugeProps {
  score: number;
  breakdown?: AtsBreakdown | null;
  className?: string;
}

export function AtsScoreGauge({ score, breakdown, className = "" }: AtsScoreGaugeProps) {
  // Clamp score between 0 and 100
  const validScore = Math.min(100, Math.max(0, score || 0));
  
  // Semi-circle arc calculation: angle from 180 (0%) down to 0 (100%)
  const radius = 80;
  const strokeWidth = 12;
  const circumference = Math.PI * radius; // Half-circle circumference
  const strokeDashoffset = circumference - (validScore / 100) * circumference;

  return (
    <div className={`rounded-xl border border-line bg-paper-raised p-8 shadow-sm flex flex-col items-center text-center space-y-6 ${className}`}>
      <div className="space-y-1">
        <h3 className="font-display text-display-md text-ink">ATS Readability & Score</h3>
        <p className="font-body text-body-sm text-ink-muted">
          Evaluated against applicant tracking system parser rules and keyword density.
        </p>
      </div>

      {/* Signature Arc Gauge SVG */}
      <div className="relative w-64 h-36 flex flex-col items-center justify-end pb-2">
        <svg width="220" height="120" viewBox="0 0 220 120" className="overflow-visible">
          {/* Background Arc Track */}
          <path
            d="M 30 110 A 80 80 0 0 1 190 110"
            fill="none"
            stroke="var(--color-line)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Active Score Arc using signature brass contour color */}
          <path
            d="M 30 110 A 80 80 0 0 1 190 110"
            fill="none"
            stroke="var(--color-brass)"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />

          {/* Hand-plotted contour stroke highlight accent */}
          <path
            d="M 30 110 A 80 80 0 0 1 190 110"
            fill="none"
            stroke="var(--color-forest)"
            strokeWidth="2"
            strokeDasharray="4 6"
            className="opacity-40"
          />
        </svg>

        {/* Center Score Readout in Plex Mono (data-lg) */}
        <div className="absolute bottom-2 flex flex-col items-center">
          <span className="font-mono text-[2.75rem] font-bold leading-none text-ink">
            {validScore}
          </span>
          <span className="font-mono text-data text-ink-muted">/ 100 overall</span>
        </div>
      </div>

      {/* Sub-scores breakdown */}
      {breakdown && (
        <div className="w-full pt-4 border-t border-line grid grid-cols-3 gap-4">
          <div className="space-y-1">
            <p className="font-body text-body-sm font-medium text-ink-muted">Formatting</p>
            <p className="font-mono text-data-lg font-bold text-ink">
              {breakdown.formatting ?? "N/A"}
            </p>
          </div>

          <div className="space-y-1">
            <p className="font-body text-body-sm font-medium text-ink-muted">Structure</p>
            <p className="font-mono text-data-lg font-bold text-ink">
              {breakdown.structure ?? "N/A"}
            </p>
          </div>

          <div className="space-y-1">
            <p className="font-body text-body-sm font-medium text-ink-muted">Parseability</p>
            <p className="font-mono text-data-lg font-bold text-ink">
              {breakdown.parseability ?? "N/A"}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
