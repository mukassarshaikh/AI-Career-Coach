"use client";

import { useState } from "react";
import { MessageSquare, UserCheck, Compass, ArrowRight } from "lucide-react";
import type { ChatContextType } from "@/types/career";

interface SessionTypeSelectorProps {
  onStartSession: (contextType: ChatContextType) => void;
  isLoading?: boolean;
}

interface Option {
  id: ChatContextType;
  title: string;
  description: string;
  icon: typeof MessageSquare;
}

const OPTIONS: Option[] = [
  {
    id: "general",
    title: "General Advice",
    description: "Ask anything about your career, compensation, or next move.",
    icon: MessageSquare,
  },
  {
    id: "mock_interview",
    title: "Mock Interview",
    description: "Practice for your target role with question-and-feedback cycles.",
    icon: UserCheck,
  },
  {
    id: "career_strategy",
    title: "Career Strategy",
    description: "Get a focused plan based on your skill gaps and learning progress.",
    icon: Compass,
  },
];

export function SessionTypeSelector({
  onStartSession,
  isLoading = false,
}: SessionTypeSelectorProps) {
  const [selectedType, setSelectedType] = useState<ChatContextType>("general");

  return (
    <div className="max-w-2xl mx-auto py-8">
      <h2 className="text-body-lg font-medium text-ink mb-2">
        Select session context
      </h2>
      <p className="text-body-sm text-ink-muted mb-6">
        Choose how you would like your Career Advisor to assist you in this conversation.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {OPTIONS.map((opt) => {
          const isSelected = selectedType === opt.id;
          const Icon = opt.icon;
          return (
            <button
              key={opt.id}
              type="button"
              id={`session-type-${opt.id}`}
              onClick={() => setSelectedType(opt.id)}
              className={`text-left p-6 rounded-xl border transition-all flex flex-col justify-between ${
                isSelected
                  ? "border-forest bg-paper-raised shadow-sm ring-1 ring-forest"
                  : "border-line bg-paper-raised hover:border-forest/50"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div
                    className={`p-2 rounded-md ${
                      isSelected
                        ? "bg-forest text-white"
                        : "bg-paper text-ink-muted"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  {isSelected && (
                    <span className="w-2.5 h-2.5 rounded-full bg-forest" />
                  )}
                </div>
                <h3 className="font-semibold text-ink text-body mb-1">
                  {opt.title}
                </h3>
                <p className="text-body-sm text-ink-muted leading-relaxed">
                  {opt.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>

      <div className="flex justify-end">
        <button
          type="button"
          id="btn-start-session"
          onClick={() => onStartSession(selectedType)}
          disabled={isLoading}
          className="flex items-center gap-2 bg-forest text-white font-medium px-6 py-3 rounded-md hover:bg-forest-hover transition-colors disabled:opacity-50"
        >
          <span>{isLoading ? "Starting session..." : "Start session"}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
