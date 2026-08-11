"use client";

/**
 * RoadmapTimeline — Ascending contour-line SVG timeline per design_system.md §4, §5 & §8.
 * Rendered with a genuine SVG path element connecting milestone dots and item cards grouped by skill.
 */

import React, { useMemo } from "react";
import { Check, ExternalLink, Play, Circle } from "lucide-react";
import type { RoadmapItem, RoadmapItemStatus } from "@/types/learning";

interface RoadmapTimelineProps {
  items: RoadmapItem[];
  roadmapId: string;
  onUpdateStatus: (itemId: string, status: RoadmapItemStatus) => void;
  isUpdating?: boolean;
}

export function RoadmapTimeline({
  items,
  onUpdateStatus,
}: RoadmapTimelineProps) {
  // Sort items by sequence_order
  const sortedItems = useMemo(() => {
    return [...items].sort((a, b) => a.sequence_order - b.sequence_order);
  }, [items]);

  // Group items by skill_name while preserving order
  const groupedItems = useMemo(() => {
    const groups: { skillName: string; items: RoadmapItem[] }[] = [];
    sortedItems.forEach((item) => {
      let group = groups.find((g) => g.skillName === item.skill_name);
      if (!group) {
        group = { skillName: item.skill_name, items: [] };
        groups.push(group);
      }
      group.items.push(item);
    });
    return groups;
  }, [sortedItems]);

  // Calculate SVG curve coordinates for the ascending contour line
  const { pathD, totalHeight } = useMemo(() => {
    if (sortedItems.length === 0) return { pathD: "", totalHeight: 0 };
    
    // Estimate heights to generate an SVG path across the items
    const itemHeight = 160; 
    const groupHeaderHeight = 44; 
    let currentY = 24;

    const points: { x: number; y: number }[] = [];
    let globalIndex = 0;

    groupedItems.forEach((group) => {
      currentY += groupHeaderHeight;
      group.items.forEach(() => {
        // Hand-plotted ascending contour line curving organically left and right
        const baseX = 24;
        const x = baseX + Math.sin(globalIndex * 0.8) * 16;
        const y = currentY + 50;
        points.push({ x, y });
        currentY += itemHeight;
        globalIndex++;
      });
    });

    if (points.length < 2) return { pathD: "", totalHeight: currentY };

    let d = `M ${points[0].x} ${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const p1 = points[i];
      const p2 = points[i + 1];
      const midY = (p1.y + p2.y) / 2;
      d += ` C ${p1.x} ${midY}, ${p2.x} ${midY}, ${p2.x} ${p2.y}`;
    }
    return { pathD: d, totalHeight: currentY };
  }, [sortedItems, groupedItems]);

  return (
    <div className="relative w-full max-w-4xl mx-auto py-4">
      {/* Signature Contour Line SVG Path Overlay */}
      {pathD && (
        <svg
          className="absolute top-0 left-0 w-12 h-full pointer-events-none z-0 overflow-visible"
          style={{ height: `${totalHeight}px` }}
          viewBox={`0 0 48 ${totalHeight}`}
          preserveAspectRatio="none"
        >
          {/* Main ascending contour line spine */}
          <path
            d={pathD}
            fill="none"
            stroke="var(--color-brass)"
            strokeWidth="3"
            strokeLinecap="round"
            className="opacity-80"
          />
          {/* Accent hand-drawn dotted stroke */}
          <path
            d={pathD}
            fill="none"
            stroke="var(--color-forest)"
            strokeWidth="1.5"
            strokeDasharray="4 4"
            className="opacity-40"
          />
        </svg>
      )}

      {/* Grouped Timeline Content */}
      <div className="space-y-8 relative z-10">
        {groupedItems.map((group) => (
          <div key={group.skillName} className="space-y-4">
            {/* Skill Group Header Label */}
            <div className="flex items-center gap-3 pl-14">
              <span className="font-mono text-data text-ink-muted uppercase tracking-wider font-semibold">
                {group.skillName}
              </span>
              <div className="h-px flex-1 bg-line" />
            </div>

            {/* Items under this skill group */}
            <div className="space-y-4">
              {group.items.map((item) => {
                const isCompleted = item.status === "completed";
                const isInProgress = item.status === "in_progress";

                return (
                  <div
                    key={item.id}
                    className="relative flex items-start gap-6 group"
                  >
                    {/* SVG Node Anchor Position Indicator */}
                    <div className="w-12 flex-shrink-0 flex items-center justify-center pt-5">
                      {isCompleted ? (
                        <div
                          className="w-5 h-5 rounded-full bg-brass border-2 border-paper-raised shadow-sm flex items-center justify-center text-paper-raised z-20"
                          title="Completed milestone"
                        >
                          <Check className="w-3 h-3 stroke-[3]" />
                        </div>
                      ) : isInProgress ? (
                        <div
                          className="w-5 h-5 rounded-full bg-paper-raised border-2 border-teal shadow-sm flex items-center justify-center text-teal z-20 animate-pulse"
                          title="In progress"
                        >
                          <Circle className="w-2.5 h-2.5 fill-teal text-teal" />
                        </div>
                      ) : (
                        <div
                          className="w-4 h-4 rounded-full bg-paper-raised border-2 border-line z-20"
                          title="Not started"
                        />
                      )}
                    </div>

                    {/* Item Card */}
                    <div
                      className={`flex-1 rounded-xl border bg-paper-raised p-6 shadow-sm transition-all ${
                        isCompleted
                          ? "border-line/70 bg-paper-raised/80"
                          : isInProgress
                          ? "border-teal/50 ring-1 ring-teal/20"
                          : "border-line hover:border-forest/40"
                      }`}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                        <div className="space-y-2 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            {/* Sequence number badge */}
                            <span className="font-mono text-data text-ink-muted bg-paper px-2 py-0.5 rounded-md border border-line">
                              #{item.sequence_order}
                            </span>

                            {/* Type badge */}
                            <span className="font-mono text-data text-ink bg-brass-soft/50 px-2 py-0.5 rounded-md capitalize">
                              {item.type}
                            </span>

                            {/* Difficulty badge */}
                            <span className="font-mono text-data text-ink-muted bg-paper px-2 py-0.5 rounded-md border border-line capitalize">
                              {item.difficulty}
                            </span>

                            {/* Status badge */}
                            <span
                              className={`font-mono text-data px-2 py-0.5 rounded-md ${
                                isCompleted
                                  ? "bg-brass/20 text-ink font-semibold"
                                  : isInProgress
                                  ? "bg-teal/15 text-teal font-semibold"
                                  : "bg-paper text-ink-muted"
                              }`}
                            >
                              {item.status.replace("_", " ")}
                            </span>
                          </div>

                          <h3 className="font-body text-body font-semibold text-ink leading-snug">
                            {item.title}
                          </h3>

                          {item.description && (
                            <p className="font-body text-body-sm text-ink-muted leading-normal">
                              {item.description}
                            </p>
                          )}

                          {item.url && (
                            <a
                              href={item.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 font-body text-body-sm font-medium text-forest hover:underline pt-1"
                            >
                              <span>Open learning resource</span>
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          )}
                        </div>

                        {/* Action buttons */}
                        <div className="flex flex-shrink-0 items-center gap-2 pt-1 sm:pt-0">
                          {!isCompleted && (
                            <>
                              {item.status === "not_started" && (
                                <button
                                  type="button"
                                  onClick={() =>
                                    onUpdateStatus(item.id, "in_progress")
                                  }
                                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-line bg-paper text-ink text-body-sm font-medium hover:bg-paper-raised hover:border-forest/40 transition-colors"
                                >
                                  <Play className="w-3.5 h-3.5 text-forest" />
                                  <span>Start</span>
                                </button>
                              )}

                              <button
                                type="button"
                                onClick={() =>
                                  onUpdateStatus(item.id, "completed")
                                }
                                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-forest text-paper-raised text-body-sm font-medium hover:bg-forest-hover transition-colors shadow-sm"
                              >
                                <Check className="w-3.5 h-3.5" />
                                <span>Mark complete</span>
                              </button>
                            </>
                          )}

                          {isCompleted && (
                            <span className="inline-flex items-center gap-1.5 text-body-sm font-mono text-ink-muted">
                              <Check className="w-4 h-4 text-brass" />
                              <span>Completed</span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
