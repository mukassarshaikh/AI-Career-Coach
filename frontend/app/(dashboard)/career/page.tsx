"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { History } from "lucide-react";
import { HistoryDrawer } from "@/components/career";
import { SessionTypeSelector } from "@/components/career/SessionTypeSelector";
import { useCreateSession } from "@/lib/hooks/useCareer";
import type { ChatContextType } from "@/types/career";

export default function CareerPage() {
  const router = useRouter();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const createSessionMutation = useCreateSession();

  const handleStartSession = (contextType: ChatContextType) => {
    createSessionMutation.mutate(contextType, {
      onSuccess: (data) => {
        router.push(`/career/${data.id}`);
      },
    });
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
        </div>
      </div>

      {/* Main Content Area — SessionTypeSelector */}
      <SessionTypeSelector
        onStartSession={handleStartSession}
        isLoading={createSessionMutation.isPending}
      />

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
