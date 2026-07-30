import { useQuery } from "@tanstack/react-query";
import { getResume, getResumeReport, listResumes } from "@/lib/api/resumeApi";

export function useResumeList() {
  return useQuery({
    queryKey: ["resumeList"],
    queryFn: () => listResumes(),
  });
}

export function useResume(resumeId: string | null) {
  return useQuery({
    queryKey: ["resume", resumeId],
    queryFn: () => getResume(resumeId!),
    enabled: !!resumeId,
  });
}

export function useResumeReport(resumeId: string | null) {
  return useQuery({
    queryKey: ["resumeReport", resumeId],
    queryFn: () => getResumeReport(resumeId!),
    enabled: !!resumeId,
  });
}
