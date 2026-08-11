"use client";

import type { ChatRole } from "@/types/career";

interface ChatMessageBubbleProps {
  role: ChatRole;
  content: string;
  isStreaming?: boolean;
  timestamp?: string;
}

export function ChatMessageBubble({
  role,
  content,
  isStreaming = false,
}: ChatMessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} my-2`}>
      <div
        className={`p-4 rounded-md max-w-[85%] font-sans text-body leading-relaxed whitespace-pre-wrap transition-colors ${
          isUser
            ? "bg-forest text-white"
            : "bg-paper-raised text-ink border border-line shadow-sm"
        }`}
      >
        <span>{content}</span>
        {isStreaming && (
          <span className="inline-block w-2 h-4 ml-1 bg-ink animate-pulse align-middle" />
        )}
      </div>
    </div>
  );
}
