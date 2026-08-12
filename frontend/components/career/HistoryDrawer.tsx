"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Compass,
  Edit2,
  MessageSquare,
  Plus,
  Trash2,
  UserCheck,
  X,
} from "lucide-react";
import {
  useDeleteSession,
  useRenameSession,
  useSessionsList,
} from "@/lib/hooks/useCareer";
import type { ChatContextType, ChatSessionPreview } from "@/types/career";

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectSession?: (sessionId: string, contextType: ChatContextType) => void;
  onNewSession?: () => void;
}

export function HistoryDrawer({
  isOpen,
  onClose,
  onSelectSession,
  onNewSession,
}: HistoryDrawerProps) {
  const router = useRouter();
  const { data: sessions, isLoading } = useSessionsList();
  const renameSessionMutation = useRenameSession();
  const deleteSessionMutation = useDeleteSession();

  const drawerRef = useRef<HTMLDivElement>(null);

  // State for inline rename
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState<string>("");

  // State for delete confirmation modal
  const [sessionToDelete, setSessionToDelete] = useState<ChatSessionPreview | null>(
    null
  );

  // Close on Escape key (if no dialog or inline edit is overriding)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        if (sessionToDelete) {
          setSessionToDelete(null);
        } else if (editingSessionId) {
          setEditingSessionId(null);
        } else {
          onClose();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, sessionToDelete, editingSessionId, onClose]);

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

  const handleStartRename = (
    e: React.MouseEvent,
    session: ChatSessionPreview
  ) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditingName(session.name || session.preview || "Untitled session");
  };

  const handleSaveRename = (sessionId: string) => {
    const trimmed = editingName.trim();
    if (trimmed) {
      renameSessionMutation.mutate({ sessionId, name: trimmed });
    }
    setEditingSessionId(null);
  };

  const handleConfirmDelete = () => {
    if (sessionToDelete) {
      deleteSessionMutation.mutate(sessionToDelete.id);
      setSessionToDelete(null);
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
      {/* Backdrop overlay */}
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
        className="relative w-80 max-w-full h-full bg-paper-raised border-l border-line shadow-sm flex flex-col p-6 z-10 font-sans"
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

        {/* New Session Action */}
        <button
          type="button"
          id="btn-drawer-new-session"
          onClick={() => {
            if (onNewSession) onNewSession();
            router.push("/career");
            onClose();
          }}
          className="w-full flex items-center justify-center gap-2 bg-forest text-white py-2.5 px-4 rounded-md font-medium text-body-sm hover:bg-forest-hover transition-colors mb-6 shadow-sm"
        >
          <Plus className="w-4 h-4" />
          <span>New session</span>
        </button>

        {/* Sessions Grouped by Context Type */}
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
                    {items.map((session) => {
                      const isEditing = editingSessionId === session.id;
                      const sessionName =
                        session.name || session.preview || "Untitled session";

                      return (
                        <div
                          key={session.id}
                          className="group relative flex items-center justify-between p-3 rounded-md border border-line bg-paper/50 hover:bg-paper hover:border-forest/50 transition-colors"
                        >
                          <div
                            onClick={() => {
                              if (!isEditing) {
                                if (onSelectSession) {
                                  onSelectSession(
                                    session.id,
                                    session.context_type
                                  );
                                }
                                router.push(`/career/${session.id}`);
                                onClose();
                              }
                            }}
                            className="flex-1 min-w-0 cursor-pointer pr-2"
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-mono text-xs text-ink-muted">
                                {formatRelativeDate(session.created_at)}
                              </span>
                            </div>

                            {isEditing ? (
                              <input
                                type="text"
                                autoFocus
                                value={editingName}
                                onChange={(e) => setEditingName(e.target.value)}
                                onKeyDown={(e) => {
                                  if (e.key === "Enter") {
                                    handleSaveRename(session.id);
                                  } else if (e.key === "Escape") {
                                    setEditingSessionId(null);
                                  }
                                }}
                                onBlur={() => handleSaveRename(session.id)}
                                className="w-full text-body-sm px-2 py-1 bg-paper border border-forest rounded focus:outline-none font-medium text-ink"
                              />
                            ) : (
                              <p className="text-body-sm text-ink font-medium truncate group-hover:text-forest">
                                {sessionName}
                              </p>
                            )}
                          </div>

                          {/* Action Buttons (Rename & Delete) */}
                          {!isEditing && (
                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                type="button"
                                title="Rename session"
                                onClick={(e) => handleStartRename(e, session)}
                                className="p-1 text-ink-muted hover:text-forest rounded hover:bg-paper-raised"
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </button>
                              <button
                                type="button"
                                title="Delete session"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSessionToDelete(session);
                                }}
                                className="p-1 text-ink-muted hover:text-clay-alert rounded hover:bg-paper-raised"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Confirmation Dialog Modal for Session Deletion */}
      {sessionToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-ink/40"
            onClick={() => setSessionToDelete(null)}
          />
          <div
            role="alertdialog"
            aria-labelledby="delete-dialog-title"
            aria-describedby="delete-dialog-desc"
            className="relative bg-paper-raised border border-line rounded-lg p-6 max-w-sm w-full shadow-lg z-10 space-y-4"
          >
            <div>
              <h3
                id="delete-dialog-title"
                className="text-body font-semibold text-ink"
              >
                Delete this session?
              </h3>
              <p
                id="delete-dialog-desc"
                className="text-body-sm text-ink-muted mt-1"
              >
                This action cannot be undone. All messages in this session will be permanently deleted.
              </p>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-line">
              <button
                type="button"
                id="btn-cancel-delete"
                onClick={() => setSessionToDelete(null)}
                className="px-4 py-2 text-body-sm font-medium text-ink bg-paper border border-line rounded-md hover:bg-paper-raised transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                id="btn-confirm-delete"
                onClick={handleConfirmDelete}
                className="px-4 py-2 text-body-sm font-medium text-white bg-clay-alert rounded-md hover:bg-clay-alert/90 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
