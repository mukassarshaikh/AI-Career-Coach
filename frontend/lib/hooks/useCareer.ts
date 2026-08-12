import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createSession, getSessionHistory, getSessionsList } from "@/lib/api/careerApi";
import type {
  ChatContextType,
  ChatHistoryResponse,
  ChatSessionPreview,
  CreateSessionResponse,
} from "@/types/career";

/**
 * Mutation hook to create a new chat session.
 */
export function useCreateSession() {
  const queryClient = useQueryClient();

  return useMutation<CreateSessionResponse, Error, ChatContextType>({
    mutationFn: (contextType: ChatContextType) => createSession(contextType),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["sessionHistory", data.id] });
      queryClient.invalidateQueries({ queryKey: ["userSessions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboardSummary"] });
    },
  });
}

/**
 * Query hook to fetch all past user chat sessions.
 */
export function useSessionsList() {
  return useQuery<ChatSessionPreview[]>({
    queryKey: ["userSessions"],
    queryFn: getSessionsList,
  });
}

/**
 * Query hook to fetch message history for a given session ID.
 * Only enabled when sessionId is present.
 */
export function useSessionHistory(sessionId: string | undefined) {
  return useQuery<ChatHistoryResponse>({
    queryKey: ["sessionHistory", sessionId],
    queryFn: () => getSessionHistory(sessionId!),
    enabled: !!sessionId,
  });
}

