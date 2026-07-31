import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getResume,
  getResumeReport,
  listResumes,
  scoreResume,
  submitJobDescription,
} from "@/lib/api/resumeApi";

export function useResumeList() {
  return useQuery({
    queryKey: ["resumeList"],
    queryFn: () => listResumes(),
  });
}

/**
 * useResume — Fetches a single resume record by ID.
 * Polls every 2s while parsed_json is null (max 45s timeout to prevent infinite loops if worker is off).
 */
export function useResume(resumeId: string | null, maxParseWaitMs: number = 45000) {
  const startTimeRef = useRef<number | null>(null);
  const [isParseTimedOut, setIsParseTimedOut] = useState(false);

  useEffect(() => {
    if (resumeId) {
      startTimeRef.current = Date.now();
      setIsParseTimedOut(false);
    }
  }, [resumeId]);

  const query = useQuery({
    queryKey: ["resume", resumeId],
    queryFn: () => getResume(resumeId!),
    enabled: !!resumeId,
    refetchInterval: (q) => {
      if (isParseTimedOut) return false;
      const data = q.state.data;
      if (startTimeRef.current && Date.now() - startTimeRef.current > maxParseWaitMs) {
        setIsParseTimedOut(true);
        return false;
      }
      if (data && !data.parsed_json && data.ats_score === null) {
        return 2000;
      }
      return false;
    },
  });

  return {
    ...query,
    isParseTimedOut,
  };
}

export function useResumeReport(resumeId: string | null, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["resumeReport", resumeId],
    queryFn: () => getResumeReport(resumeId!),
    enabled: !!resumeId && (options?.enabled ?? true),
    retry: false, // Prevent continuous 404 retries for unscored resumes
  });
}

export function useScoreResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (resumeId: string) => scoreResume(resumeId),
    onSuccess: (_, resumeId) => {
      queryClient.invalidateQueries({ queryKey: ["resume", resumeId] });
      queryClient.invalidateQueries({ queryKey: ["resumeReport", resumeId] });
    },
  });
}

export function useSubmitJobDescription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ resumeId, rawText }: { resumeId: string; rawText: string }) =>
      submitJobDescription(resumeId, rawText),
    onSuccess: (_, { resumeId }) => {
      queryClient.invalidateQueries({ queryKey: ["resumeReport", resumeId] });
    },
  });
}
