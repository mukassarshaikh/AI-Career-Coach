import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getDashboardSummary } from "@/lib/api/dashboardApi";
import {
  generateRoadmap,
  getActiveRoadmap,
  getRoadmap,
  regenerateRoadmap,
  updateRoadmapItem,
} from "@/lib/api/learningApi";
import type { DashboardSummary } from "@/types/dashboard";
import type {
  GenerateRoadmapResponse,
  Roadmap,
  RoadmapItemStatus,
  RoadmapItemUpdateResponse,
} from "@/types/learning";

export function useDashboardSummary() {
  return useQuery<DashboardSummary>({
    queryKey: ["dashboardSummary"],
    queryFn: getDashboardSummary,
  });
}

export function useActiveRoadmap() {
  return useQuery<Roadmap>({
    queryKey: ["activeRoadmap"],
    queryFn: getActiveRoadmap,
    retry: false, // 404 handled gracefully when user has no active roadmap
  });
}

export function useRoadmap(id: string | undefined) {
  return useQuery<Roadmap>({
    queryKey: ["roadmap", id],
    queryFn: () => getRoadmap(id!),
    enabled: !!id,
  });
}

interface UpdateRoadmapItemArgs {
  itemId: string;
  status: RoadmapItemStatus;
  roadmapId?: string;
}

export function useUpdateRoadmapItem() {
  const queryClient = useQueryClient();

  return useMutation<
    RoadmapItemUpdateResponse,
    Error,
    UpdateRoadmapItemArgs,
    { previousRoadmap?: Roadmap; previousActiveRoadmap?: Roadmap }
  >({
    mutationFn: ({ itemId, status }) => updateRoadmapItem(itemId, status),
    onMutate: async ({ itemId, status, roadmapId }) => {
      // Cancel outgoing refetches so they don't overwrite optimistic update
      if (roadmapId) {
        await queryClient.cancelQueries({ queryKey: ["roadmap", roadmapId] });
      }
      await queryClient.cancelQueries({ queryKey: ["activeRoadmap"] });

      const previousRoadmap = roadmapId
        ? queryClient.getQueryData<Roadmap>(["roadmap", roadmapId])
        : undefined;
      const previousActiveRoadmap = queryClient.getQueryData<Roadmap>(["activeRoadmap"]);

      // Helper to update item in a Roadmap object
      const updateItemsInRoadmap = (old?: Roadmap): Roadmap | undefined => {
        if (!old || !old.items) return old;
        return {
          ...old,
          items: old.items.map((item) => {
            if (item.id === itemId) {
              return {
                ...item,
                status,
                completed_at:
                  status === "completed" ? new Date().toISOString() : item.completed_at,
              };
            }
            return item;
          }),
        };
      };

      // Optimistically update caches
      if (roadmapId) {
        queryClient.setQueryData<Roadmap>(["roadmap", roadmapId], (old) =>
          updateItemsInRoadmap(old)
        );
      }
      queryClient.setQueryData<Roadmap>(["activeRoadmap"], (old) =>
        updateItemsInRoadmap(old)
      );

      return { previousRoadmap, previousActiveRoadmap };
    },
    onError: (_err, { roadmapId }, context) => {
      if (roadmapId && context?.previousRoadmap) {
        queryClient.setQueryData(["roadmap", roadmapId], context.previousRoadmap);
      }
      if (context?.previousActiveRoadmap) {
        queryClient.setQueryData(["activeRoadmap"], context.previousActiveRoadmap);
      }
    },
    onSettled: (_data, _error, { roadmapId }) => {
      if (roadmapId) {
        queryClient.invalidateQueries({ queryKey: ["roadmap", roadmapId] });
      }
      queryClient.invalidateQueries({ queryKey: ["activeRoadmap"] });
      queryClient.invalidateQueries({ queryKey: ["dashboardSummary"] });
    },
  });
}

export function useGenerateRoadmap() {
  const queryClient = useQueryClient();
  return useMutation<GenerateRoadmapResponse, Error, string>({
    mutationFn: (skillGapReportId: string) => generateRoadmap(skillGapReportId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["activeRoadmap"] });
      queryClient.invalidateQueries({ queryKey: ["dashboardSummary"] });
    },
  });
}

export function useRegenerateRoadmap() {
  const queryClient = useQueryClient();
  return useMutation<GenerateRoadmapResponse, Error, string>({
    mutationFn: (roadmapId: string) => regenerateRoadmap(roadmapId),
    onSuccess: (_data, roadmapId) => {
      queryClient.invalidateQueries({ queryKey: ["roadmap", roadmapId] });
      queryClient.invalidateQueries({ queryKey: ["activeRoadmap"] });
      queryClient.invalidateQueries({ queryKey: ["dashboardSummary"] });
    },
  });
}
