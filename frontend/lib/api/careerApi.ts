import { getSession } from "next-auth/react";
import { fetchWithAuth } from "./client";
import type {
  ChatContextType,
  ChatHistoryResponse,
  ChatSessionPreview,
  CreateSessionResponse,
} from "@/types/career";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

/**
 * Fetches all chat sessions for the authenticated user with preview snippet.
 */
export async function getSessionsList(): Promise<ChatSessionPreview[]> {
  return fetchWithAuth<ChatSessionPreview[]>("/api/v1/career/chat/sessions");
}


/**
 * Creates a new career chat session for the specified context type.
 */
export async function createSession(
  contextType: ChatContextType
): Promise<CreateSessionResponse> {
  return fetchWithAuth<CreateSessionResponse>("/api/v1/career/chat/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ context_type: contextType }),
  });
}

/**
 * Fetches complete message history for an existing chat session.
 */
export async function getSessionHistory(
  sessionId: string
): Promise<ChatHistoryResponse> {
  return fetchWithAuth<ChatHistoryResponse>(
    `/api/v1/career/chat/${sessionId}/history`
  );
}

/**
 * Sends a user message to the streaming endpoint.
 * Returns the raw fetch Response object allowing the caller to read response.body as a ReadableStream.
 */
export async function sendMessage(
  sessionId: string,
  content: string
): Promise<Response> {
  const session = await getSession();
  const rawToken = (session as any)?.accessToken;
  const token = typeof rawToken === "string" ? rawToken : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(
    `${BACKEND_URL}/api/v1/career/chat/${sessionId}/message`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({ content }),
    }
  );

  return response;
}
