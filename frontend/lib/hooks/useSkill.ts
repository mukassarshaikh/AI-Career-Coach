import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  generateSkillGapReport,
  generateSkillVector,
  getSkillGapReport,
  refreshSkillGapReport,
} from "@/lib/api/skillApi";
import type {
  ComputeSkillGapResponse,
  GenerateSkillVectorResponse,
  SkillGapReportResponse,
} from "@/types/skill";

export function useSkillGapReport() {
  return useQuery<SkillGapReportResponse>({
    queryKey: ["skillGapReport"],
    queryFn: getSkillGapReport,
    retry: false, // Don't retry on 404 (no gap report yet)
  });
}

export function useGenerateSkillVector() {
  return useMutation<GenerateSkillVectorResponse, Error, string>({
    mutationFn: (resumeId: string) => generateSkillVector(resumeId),
  });
}

export function useGenerateSkillGapReport() {
  const queryClient = useQueryClient();
  return useMutation<ComputeSkillGapResponse, Error, string>({
    mutationFn: (targetRole: string) => generateSkillGapReport(targetRole),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skillGapReport"] });
    },
  });
}

export function useRefreshSkillGapReport() {
  const queryClient = useQueryClient();
  return useMutation<ComputeSkillGapResponse, Error, string>({
    mutationFn: (targetRole: string) => refreshSkillGapReport(targetRole),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skillGapReport"] });
    },
  });
}
