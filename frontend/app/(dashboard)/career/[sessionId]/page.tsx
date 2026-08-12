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

          <Link
            id="btn-new-session"
            href="/career"
            className="flex items-center gap-2 border border-line bg-paper-raised text-ink px-4 py-2 rounded-md hover:bg-paper text-body-sm font-medium transition-colors"
          >
            <RefreshCw className="w-4 h-4 text-ink-muted" />
            <span>New session</span>
          </Link>
        </div>
      </div>

      {/* Main Content Area — Session Chat or Mock Interview */}
      {contextType === "mock_interview" ? (
        <MockInterviewPanel sessionId={sessionId} />
      ) : (
        <ChatWindow sessionId={sessionId} contextType={contextType} />
      )}

      {/* History Slide-In Drawer */}
      <HistoryDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
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
