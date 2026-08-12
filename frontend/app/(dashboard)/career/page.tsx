"use client";

import { useState } from "react";
import { History, RefreshCw } from "lucide-react";
import { ChatWindow, HistoryDrawer, MockInterviewPanel } from "@/components/career";
import { SessionTypeSelector } from "@/components/career/SessionTypeSelector";
import { useCreateSession } from "@/lib/hooks/useCareer";
import type { ChatContextType } from "@/types/career";

export default function CareerPage() {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeContextType, setActiveContextType] = useState<ChatContextType>("general");
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

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

  const handleSelectSessionFromDrawer = (
    sessionId: string,
    contextType: ChatContextType
  ) => {
    setActiveSessionId(sessionId);
    setActiveContextType(contextType);
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

        <div className="flex items-center gap-3">
          <button
            type="button"
            id="btn-history-drawer"
            onClick={() => setIsDrawerOpen(true)}
            className="flex items-center gap-2 border border-line bg-paper-raised text-ink px-4 py-2 rounded-md hover:bg-paper text-body-sm font-medium transition-colors"
          >
            <History className="w-4 h-4 text-ink-muted" />
            <span>History</span>
          </button>

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

      {/* History Slide-In Drawer */}
      <HistoryDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        onSelectSession={handleSelectSessionFromDrawer}
        onNewSession={handleNewSession}
      />

      {/* Legal & professional disclaimer */}
      <div className="pt-2 text-center">
        <p className="text-body-sm text-ink-muted max-w-2xl mx-auto leading-normal">
          This advisor is not a licensed career counselor, lawyer, or financial advisor. For legal, visa, or compensation matters, consult a qualified professional.
        </p>
      </div>
    </div>
  );
}

