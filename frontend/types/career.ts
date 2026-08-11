/**
 * Career / chat types — mirrors backend Pydantic schemas.
 */

export type ChatContextType = "general" | "mock_interview" | "career_strategy";
export type ChatRole = "user" | "assistant";

export interface CreateSessionRequest {
  context_type: ChatContextType;
}

export interface CreateSessionResponse {
  id: string;
  context_type: ChatContextType;
  created_at: string;
}

export interface SendMessageRequest {
  content: string;
}

export interface ChatMessageResponse {
  id: string;
  session_id: string;
  role: ChatRole;
  content: string;
  created_at: string;
}

export interface ChatHistoryResponse {
  session_id: string;
  messages: ChatMessageResponse[];
}
