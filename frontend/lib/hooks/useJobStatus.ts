import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getJobStatus } from "@/lib/api/resumeApi";
import type { JobStatusResponse } from "@/types/resume";

/**
 * useJobStatus — Polls async background Arq job status via Redis.
 * Includes a 90-second timeout safeguard (maxDurationMs) with retry capability to handle transient network issues.
 */
export function useJobStatus(jobId: string | null, maxDurationMs: number = 90000) {
  const startTimeRef = useRef<number | null>(null);
  const [isTimedOut, setIsTimedOut] = useState(false);

  useEffect(() => {
    if (jobId) {
      startTimeRef.current = Date.now();
      setIsTimedOut(false);
    } else {
      startTimeRef.current = null;
      setIsTimedOut(false);
    }
  }, [jobId]);

  const query = useQuery<JobStatusResponse>({
    queryKey: ["jobStatus", jobId],
    queryFn: () => getJobStatus(jobId!),
    enabled: !!jobId && !isTimedOut,
    retry: 3,
    refetchInterval: (q) => {
      if (isTimedOut) return false;
      const data = q.state.data;
      if (startTimeRef.current && Date.now() - startTimeRef.current > maxDurationMs) {
        setIsTimedOut(true);
        return false;
      }
      if (!data) return 2000;
      const status = data.status;
      return status === "queued" || status === "in_progress" ? 2000 : false;
    },
  });

  if (isTimedOut && jobId) {
    return {
      ...query,
      data: {
        job_id: jobId,
        status: "failed" as const,
        result: { error: "Job processing timed out after 90 seconds." },
      },
    };
  }

  return query;
}
