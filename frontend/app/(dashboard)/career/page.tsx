"use client";

import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { ChatWindow, MockInterviewPanel } from "@/components/career";
import { SessionTypeSelector } from "@/components/career/SessionTypeSelector";
import { useCreateSession } from "@/lib/hooks/useCareer";
import type { ChatContextType } from "@/types/career";

export default function CareerPage() {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeContextType, setActiveContextType] = useState<ChatContextType>("general");

  const createSessionMutation = useCreateSession();

  const handleStartSession = (contextType: ChatContextType) => {
    setActiveContextType(contextType);
    createSessionMutation.mutate(contextType, {
      onSuccess: (data) => {
        setActiveSessionId(data.id);
      },
    });
  };

  const handleNewSession = () => {
    setActiveSessionId(null);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header section */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-display-lg font-serif font-normal text-ink">
            Career Advisor
          </h1>
          <p className="text-body text-ink-muted mt-1">
            AI-powered career guidance, interview practice, and strategy advice tailored to your profile.
          </p>
        </div>

        {activeSessionId && (
          <button
            type="button"
            id="btn-new-session"
            onClick={handleNewSession}
            className="flex items-center gap-2 border border-line bg-paper-raised text-ink px-4 py-2 rounded-md hover:bg-paper text-body-sm font-medium transition-colors"
          >
            <RefreshCw className="w-4 h-4 text-ink-muted" />
            <span>New session</span>
          </button>
        )}
      </div>

      {/* Main Content Area */}
      {!activeSessionId ? (
        <SessionTypeSelector
          onStartSession={handleStartSession}
          isLoading={createSessionMutation.isPending}
        />
      ) : activeContextType === "mock_interview" ? (
        <MockInterviewPanel sessionId={activeSessionId} />
      ) : (
        <ChatWindow
          sessionId={activeSessionId}
          contextType={activeContextType}
        />
      )}

      {/* Legal & professional disclaimer */}
      <div className="pt-2 text-center">
        <p className="text-body-sm text-ink-muted max-w-2xl mx-auto leading-normal">
          This advisor is not a licensed career counselor, lawyer, or financial advisor. For legal, visa, or compensation matters, consult a qualified professional.
        </p>
      </div>
    </div>
  );
}
