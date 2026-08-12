"use client";

import { useEffect, useRef } from "react";
import { MessageSquare, UserCheck, Compass, X, Plus } from "lucide-react";
import { useSessionsList } from "@/lib/hooks/useCareer";
import type { ChatContextType, ChatSessionPreview } from "@/types/career";

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectSession: (sessionId: string, contextType: ChatContextType) => void;
  onNewSession: () => void;
}

export function HistoryDrawer({
  isOpen,
  onClose,
  onSelectSession,
  onNewSession,
}: HistoryDrawerProps) {
  const { data: sessions, isLoading } = useSessionsList();
  const drawerRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Format relative date string
  const formatRelativeDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffSecs = Math.floor(diffMs / 1000);
      const diffMins = Math.floor(diffSecs / 60);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffSecs < 60) return "Just now";
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays === 1) return "Yesterday";
      if (diffDays < 30) return `${diffDays}d ago`;
      return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    } catch {
      return "Past session";
    }
  };

  if (!isOpen) return null;

  const groupedSessions: Record<ChatContextType, ChatSessionPreview[]> = {
    general: [],
    mock_interview: [],
    career_strategy: [],
  };

  if (sessions) {
    for (const session of sessions) {
      if (groupedSessions[session.context_type]) {
        groupedSessions[session.context_type].push(session);
      }
    }
  }

  const contextMeta: Record<
    ChatContextType,
    { label: string; icon: typeof MessageSquare }
  > = {
    general: { label: "General Advice", icon: MessageSquare },
    mock_interview: { label: "Mock Interview", icon: UserCheck },
    career_strategy: { label: "Career Strategy", icon: Compass },
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Dark backdrop overlay */}
      <div
        className="fixed inset-0 bg-ink/30 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-in Drawer Container (~320px wide) */}
      <div
        ref={drawerRef}
        role="dialog"
        aria-label="Chat History"
        aria-modal="true"
        className="relative w-80 max-w-full h-full bg-paper-raised border-l border-line shadow-md flex flex-col p-6 z-10 font-sans"
      >
        {/* Drawer Header */}
        <div className="flex items-center justify-between pb-4 border-b border-line mb-4">
          <h2 className="text-body font-semibold text-ink">Chat History</h2>
          <button
            type="button"
            id="btn-close-history-drawer"
            onClick={onClose}
            aria-label="Close history drawer"
            className="p-1.5 text-ink-muted hover:text-ink hover:bg-paper rounded-md transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* New Session Reset Action */}
        <button
          type="button"
          id="btn-drawer-new-session"
          onClick={() => {
            onNewSession();
            onClose();
          }}
          className="w-full flex items-center justify-center gap-2 bg-forest text-white py-2.5 px-4 rounded-md font-medium text-body-sm hover:bg-forest-hover transition-colors mb-6 shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>New session</span>
        </button>

        {/* Session List Grouped by Context Type */}
        <div className="flex-1 overflow-y-auto space-y-6 pr-1">
          {isLoading ? (
            <p className="text-body-sm text-ink-muted text-center py-8">
              Loading past sessions...
            </p>
          ) : !sessions || sessions.length === 0 ? (
            <p className="text-body-sm text-ink-muted text-center py-8">
              No past sessions found.
            </p>
          ) : (
            (Object.keys(contextMeta) as ChatContextType[]).map((contextKey) => {
              const items = groupedSessions[contextKey];
              if (items.length === 0) return null;
              const meta = contextMeta[contextKey];
              const Icon = meta.icon;

              return (
                <div key={contextKey} className="space-y-2">
                  <div className="flex items-center gap-1.5 text-data text-xs uppercase tracking-wider font-mono text-ink-muted px-1">
                    <Icon className="w-3.5 h-3.5 text-forest" />
                    <span>{meta.label}</span>
                  </div>

                  <div className="space-y-1.5">
                    {items.map((session) => (
                      <button
                        key={session.id}
                        type="button"
                        onClick={() => {
                          onSelectSession(session.id, session.context_type);
                          onClose();
                        }}
                        className="w-full text-left p-3 rounded-md border border-line bg-paper/50 hover:bg-paper hover:border-forest/50 transition-colors group"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-mono text-xs text-ink-muted">
                            {formatRelativeDate(session.created_at)}
                          </span>
                        </div>
                        <p className="text-body-sm text-ink font-medium truncate group-hover:text-forest">
                          {session.preview}
                        </p>
                      </button>
                    ))}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
