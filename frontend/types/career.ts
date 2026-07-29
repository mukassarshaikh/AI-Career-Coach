/**
 * Career / chat types — mirrors backend Pydantic schemas.
 * Filled out in Phase 3.
 */

export type ChatContextType = "general" | "mock_interview" | "career_strategy";
export type ChatRole = "user" | "assistant";

export interface ChatSession {
  id: string;
  userId: string;
  contextType: ChatContextType;
  createdAt: string;
}

export interface ChatMessage {
  id: string;
  sessionId: string;
  role: ChatRole;
  content: string;
  createdAt: string;
}
