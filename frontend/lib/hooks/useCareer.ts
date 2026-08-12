import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createSession,
  deleteSession,
  getSessionHistory,
  getSessionsList,
  renameSession,
} from "@/lib/api/careerApi";
import type {
  ChatContextType,
  ChatHistoryResponse,
  ChatSessionPreview,
  CreateSessionResponse,
  DeleteSessionResponse,
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
 * Mutation hook to rename an existing chat session.
 */
export function useRenameSession() {
  const queryClient = useQueryClient();

  return useMutation<
    CreateSessionResponse,
    Error,
    { sessionId: string; name: string }
  >({
    mutationFn: ({ sessionId, name }) => renameSession(sessionId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["userSessions"] });
    },
  });
}

/**
 * Mutation hook to delete an existing chat session with optimistic removal.
 */
export function useDeleteSession() {
  const queryClient = useQueryClient();

  return useMutation<DeleteSessionResponse, Error, string>({
    mutationFn: (sessionId: string) => deleteSession(sessionId),
    onMutate: async (sessionId: string) => {
      await queryClient.cancelQueries({ queryKey: ["userSessions"] });
      const previousSessions = queryClient.getQueryData<ChatSessionPreview[]>([
        "userSessions",
      ]);

      if (previousSessions) {
        queryClient.setQueryData<ChatSessionPreview[]>(
          ["userSessions"],
          previousSessions.filter((s) => s.id !== sessionId)
        );
      }

      return { previousSessions };
    },
    onError: (_err, _sessionId, context: any) => {
      if (context?.previousSessions) {
        queryClient.setQueryData(["userSessions"], context.previousSessions);
      }
    },
    onSettled: () => {
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
