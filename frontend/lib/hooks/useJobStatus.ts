import { useQuery } from "@tanstack/react-query";
import { getJobStatus } from "@/lib/api/resumeApi";

export function useJobStatus(jobId: string | null) {
  return useQuery({
    queryKey: ["jobStatus", jobId],
    queryFn: () => getJobStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 2000;
      const status = data.status;
      return status === "queued" || status === "in_progress" ? 2000 : false;
    },
  });
}
