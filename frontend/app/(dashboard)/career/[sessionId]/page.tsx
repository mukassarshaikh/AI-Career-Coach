"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AlertCircle, ArrowLeft, History, Loader2, RefreshCw } from "lucide-react";
import { ChatWindow, HistoryDrawer, MockInterviewPanel } from "@/components/career";
import { useSessionHistory, useSessionsList } from "@/lib/hooks/useCareer";
import type { ChatContextType } from "@/types/career";

export default function CareerSessionPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const { data: history, isLoading, isError } = useSessionHistory(sessionId);
  const { data: sessions } = useSessionsList();

  // Find active session metadata to resolve context_type
  const activeSession = sessions?.find((s) => s.id === sessionId);
  const contextType: ChatContextType = activeSession?.context_type || "general";

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto space-y-6 animate-pulse">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <div className="h-8 w-48 bg-line/40 rounded-md" />
            <div className="h-4 w-96 bg-line/40 rounded-md" />
          </div>
        </div>
        <div className="h-[550px] border border-line bg-paper-raised rounded-xl flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-forest animate-spin" />
        </div>
      </div>
    );
  }

  if (isError || !history) {
    return (
      <div className="max-w-4xl mx-auto py-12 space-y-6">
        <Link
          href="/career"
          className="inline-flex items-center gap-1.5 font-body text-body-sm font-medium text-forest hover:underline"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Career Advisor</span>
        </Link>

        <div className="rounded-xl border border-line bg-paper-raised p-10 text-center space-y-4 shadow-sm">
          <AlertCircle className="w-8 h-8 text-clay-alert mx-auto" />
          <h2 className="font-display text-display-md text-ink">
            Session not found
          </h2>
          <p className="font-body text-body text-ink-muted max-w-md mx-auto">
            The requested chat session could not be loaded or does not exist.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-[calc(100vh-5.5rem)] flex flex-col">
      {/* Main Content Area — Session Chat or Mock Interview */}
      {contextType === "mock_interview" ? (
        <MockInterviewPanel sessionId={sessionId} />
      ) : (
        <ChatWindow
          sessionId={sessionId}
          contextType={contextType}
          onOpenHistory={() => setIsDrawerOpen(true)}
        />
      )}

      {/* History Slide-In Drawer */}
      <HistoryDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />
    </div>
  );
}

