"use client";

/**
 * GrammarSuggestionsList — Renders grammar, active voice, and tone audit suggestions per design_system.md §5 & §6.
 */

import { FileEdit, CheckCircle2 } from "lucide-react";
import type { GrammarSuggestion } from "@/types/resume";

interface GrammarSuggestionsListProps {
  suggestions?: GrammarSuggestion[] | null;
  className?: string;
}

export function GrammarSuggestionsList({ suggestions, className = "" }: GrammarSuggestionsListProps) {
  if (!suggestions || suggestions.length === 0) {
    return (
      <div className={`rounded-xl border border-line bg-paper-raised p-8 shadow-sm space-y-4 ${className}`}>
        <h3 className="font-display text-display-md text-ink">Grammar & Tone Audit</h3>
        <div className="flex items-center gap-3 p-4 rounded-md bg-paper border border-line text-body-sm text-ink font-medium">
          <CheckCircle2 className="w-5 h-5 text-forest flex-shrink-0" />
          <span>No grammar or phrasing issues detected. Your resume wording is clear and concise.</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-xl border border-line bg-paper-raised p-8 shadow-sm space-y-6 ${className}`}>
      <div className="space-y-1">
        <h3 className="font-display text-display-md text-ink">Grammar & Tone Audit</h3>
        <p className="font-body text-body-sm text-ink-muted">
          Recommended phrasing improvements to enhance action orientation and clarity.
        </p>
      </div>

      <div className="divide-y divide-line border-t border-b border-line">
        {suggestions.map((item, index) => (
          <div key={index} className="py-4 space-y-2 first:pt-4 last:pb-4">
            <div className="flex items-center justify-between">
              <span className="font-mono text-data font-semibold text-forest uppercase tracking-wider">
                {item.location || "General Section"}
              </span>
              <span className="inline-flex items-center gap-1 font-body text-body-sm text-ink-muted">
                <FileEdit className="w-3.5 h-3.5 text-brass" />
                <span>Suggested revision</span>
              </span>
            </div>

            <p className="font-body text-body-sm text-ink font-medium">
              <span className="text-ink-muted">Issue: </span>
              {item.issue}
            </p>

            <div className="p-3 rounded-md bg-paper border border-line font-body text-body-sm text-ink">
              <span className="font-semibold text-forest">Recommendation: </span>
              {item.suggestion}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
