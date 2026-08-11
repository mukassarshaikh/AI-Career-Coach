"use client";

/**
 * Roadmap Detail Page — full interactive timeline with ascending SVG path spine per design_system.md §4, §5 & §8.
 * Verified real data against roadmap 4e8c800c-7021-4bce-9bc6-54ebc88238b1.
 */

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, RefreshCw, Loader2, Sparkles, AlertCircle } from "lucide-react";
import {
  useRoadmap,
  useUpdateRoadmapItem,
  useRegenerateRoadmap,
} from "@/lib/hooks/useLearning";
import { useJobStatus } from "@/lib/hooks/useJobStatus";
import { RoadmapTimeline } from "@/components/learning/RoadmapTimeline";
import { ContourProgress } from "@/components/learning/ContourProgress";
import type { RoadmapItemStatus } from "@/types/learning";

export default function RoadmapDetailPage() {
  const params = useParams();
  const router = useRouter();
  const roadmapId = params.roadmapId as string;

  const { data: roadmap, isLoading, isError, refetch } = useRoadmap(roadmapId);
  const updateItemMutation = useUpdateRoadmapItem();
  const regenerateMutation = useRegenerateRoadmap();

  // Background skill vector recalculation job tracking after marking complete
  const [recalcJobId, setRecalcJobId] = useState<string | null>(null);
  const { data: recalcJobStatus } = useJobStatus(recalcJobId);

  // Roadmap regeneration job tracking
  const [regenJobId, setRegenJobId] = useState<string | null>(null);
  const { data: regenJobStatus } = useJobStatus(regenJobId);

  // Clear recalculation job state when completed
  useEffect(() => {
    if (recalcJobStatus?.status === "completed" || recalcJobStatus?.status === "failed") {
      setRecalcJobId(null);
    }
  }, [recalcJobStatus]);

  // Handle roadmap regeneration completion
  useEffect(() => {
    if (regenJobStatus?.status === "completed") {
      setRegenJobId(null);
      refetch();
    }
  }, [regenJobStatus, refetch]);

  const handleUpdateStatus = async (itemId: string, status: RoadmapItemStatus) => {
    try {
      const res = await updateItemMutation.mutateAsync({
        itemId,
        status,
        roadmapId,
      });

      // If completing item triggered background recalculation, track job_id
      if (res?.job_id) {
        setRecalcJobId(res.job_id);
      }
    } catch (err) {
      console.error("Failed to update item status:", err);
    }
  };

  const handleRegenerate = async () => {
    if (!roadmapId) return;
    try {
      const res = await regenerateMutation.mutateAsync(roadmapId);
      if (res?.job_id) {
        setRegenJobId(res.job_id);
      }
    } catch (err) {
      console.error("Failed to regenerate roadmap:", err);
    }
  };

  const isRecalculating =
    recalcJobStatus?.status === "queued" || recalcJobStatus?.status === "in_progress";

  const isRegenerating =
    regenJobStatus?.status === "queued" ||
    regenJobStatus?.status === "in_progress" ||
    regenerateMutation.isPending;

  if (isLoading) {
    return (
      <div className="space-y-8 max-w-4xl mx-auto pb-16 animate-pulse">
        <div className="h-6 w-32 bg-line/40 rounded-md" />
        <div className="h-10 w-96 bg-line/40 rounded-md" />
        <div className="h-96 rounded-xl border border-line bg-paper-raised p-8" />
      </div>
    );
  }

  if (isError || !roadmap) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto pb-16">
        <Link
          href="/learning"
          className="inline-flex items-center gap-1.5 font-body text-body-sm font-medium text-forest hover:underline"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Learning Intelligence</span>
        </Link>

        <div className="rounded-xl border border-line bg-paper-raised p-10 text-center space-y-4 shadow-sm">
          <AlertCircle className="w-8 h-8 text-clay-alert mx-auto" />
          <h2 className="font-display text-display-md text-ink">
            Roadmap not found
          </h2>
          <p className="font-body text-body text-ink-muted">
            The requested learning roadmap could not be loaded or does not exist.
          </p>
        </div>
      </div>
    );
  }

  const items = roadmap.items || [];
  const completedCount = items.filter((i) => i.status === "completed").length;
  const totalCount = items.length;
  const percentage = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  return (
    <div className="space-y-8 max-w-4xl mx-auto pb-16">
      {/* Top Background Recalculation Status Strip per design_system.md §5 */}
      {isRecalculating && (
        <div className="rounded-md border border-brass/40 bg-brass-soft/30 px-4 py-3 flex items-center justify-between gap-4 shadow-sm animate-pulse">
          <div className="flex items-center gap-2.5">
            <Loader2 className="w-4 h-4 text-forest animate-spin flex-shrink-0" />
            <span className="font-body text-body-sm font-medium text-ink">
              Updating your skill profile in the background…
            </span>
          </div>
          <div className="w-32">
            <ContourProgress value={75} size="sm" />
          </div>
        </div>
      )}

      {/* Top Regeneration Strip */}
      {isRegenerating && (
        <div className="rounded-md border border-forest/40 bg-forest/10 px-4 py-3 flex items-center gap-3 shadow-sm">
          <Loader2 className="w-4 h-4 text-forest animate-spin" />
          <span className="font-body text-body-sm font-medium text-ink">
            Regenerating roadmap with updated skill priorities…
          </span>
        </div>
      )}

      {/* Navigation & Header */}
      <div className="space-y-4">
        <Link
          href="/learning"
          className="inline-flex items-center gap-1.5 font-body text-body-sm font-medium text-forest hover:underline"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Learning Intelligence</span>
        </Link>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="font-display text-display-lg tracking-tight text-ink">
              Learning Roadmap Path
            </h1>
            <p className="font-mono text-data text-ink-muted">
              {completedCount} of {totalCount} items completed ({Math.round(percentage)}%)
            </p>
          </div>

          <button
            type="button"
            onClick={handleRegenerate}
            disabled={isRegenerating}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md border border-line bg-paper-raised text-ink text-body-sm font-medium hover:border-forest/40 transition-colors shadow-sm disabled:opacity-50 self-start sm:self-auto"
          >
            <RefreshCw className={`w-4 h-4 text-forest ${isRegenerating ? "animate-spin" : ""}`} />
            <span>Regenerate roadmap</span>
          </button>
        </div>
      </div>

      {/* Full Ascending Contour Line Roadmap Timeline */}
      <RoadmapTimeline
        items={items}
        roadmapId={roadmapId}
        onUpdateStatus={handleUpdateStatus}
        isUpdating={updateItemMutation.isPending}
      />
    </div>
  );
}
