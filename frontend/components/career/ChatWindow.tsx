"use client";

import { useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import { sendMessage } from "@/lib/api/careerApi";
import { useSessionHistory } from "@/lib/hooks/useCareer";
import { ChatMessageBubble } from "./ChatMessageBubble";
import type { ChatContextType, ChatMessageResponse } from "@/types/career";

interface ChatWindowProps {
  sessionId: string;
  contextType: ChatContextType;
}

export function ChatWindow({ sessionId, contextType }: ChatWindowProps) {
  const { data: historyData, isLoading: isHistoryLoading, refetch } = useSessionHistory(sessionId);
  const [messages, setMessages] = useState<ChatMessageResponse[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [inFlightContent, setInFlightContent] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const chatContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Sync loaded history from TanStack Query into local messages state
  useEffect(() => {
    if (historyData?.messages && !isStreaming) {
      setMessages(historyData.messages);
    }
  }, [historyData, isStreaming]);

  // Auto-scroll to bottom as messages or streamed tokens update
  useEffect(() => {
    if (chatContainerRef.current) {
      const container = chatContainerRef.current;
      const isNearBottom =
        container.scrollHeight - container.scrollTop - container.clientHeight < 150;
      if (isNearBottom || isStreaming) {
        container.scrollTop = container.scrollHeight;
      }
    }
  }, [messages, inFlightContent, isStreaming]);

  // Adjust textarea height up to 4 lines
  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const textarea = e.target;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
  };

  const handleSendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    setErrorMsg(null);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    // 1. Append user message locally
    const userMsg: ChatMessageResponse = {
      id: `temp-user-${Date.now()}`,
      session_id: sessionId,
      role: "user",
      content: trimmed,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    // 2. Init streaming state
    setIsStreaming(true);
    setInFlightContent("");

    let accumulatedText = "";

    try {
      const response = await sendMessage(sessionId, trimmed);

      if (!response.ok) {
        let errText = "Failed to send message.";
        try {
          const errJson = await response.json();
          errText = errJson.detail || errJson.message || errText;
        } catch {
          // ignore
        }
        throw new Error(errText);
      }

      if (!response.body) {
        throw new Error("No response body received from stream.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        // Preserve incomplete tail line in buffer
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (trimmedLine.startsWith("data: ")) {
            const rawChunk = trimmedLine.substring(6);
            if (rawChunk.startsWith("[ERROR:")) {
              setErrorMsg(rawChunk);
            } else {
              accumulatedText += rawChunk;
              setInFlightContent(accumulatedText);
            }
          }
        }
      }

      // Flush remaining buffer text if any
      if (buffer.trim().startsWith("data: ")) {
        const rawChunk = buffer.trim().substring(6);
        if (!rawChunk.startsWith("[ERROR:")) {
          accumulatedText += rawChunk;
          setInFlightContent(accumulatedText);
        }
      }

      // 3. Move completed message into message state
      if (accumulatedText) {
        const assistantMsg: ChatMessageResponse = {
          id: `temp-assistant-${Date.now()}`,
          session_id: sessionId,
          role: "assistant",
          content: accumulatedText,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "An error occurred while streaming response.");
    } finally {
      setIsStreaming(false);
      setInFlightContent("");
      refetch();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const contextLabels: Record<ChatContextType, string> = {
    general: "General Advice",
    mock_interview: "Mock Interview",
    career_strategy: "Career Strategy",
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)] max-w-4xl mx-auto border border-line rounded-xl bg-paper-raised shadow-sm overflow-hidden">
      {/* Chat Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-line bg-paper">
        <div>
          <span className="text-data text-ink-muted uppercase tracking-wider font-mono text-xs">
            Active Session
          </span>
          <h2 className="text-body font-semibold text-ink">
            {contextLabels[contextType]}
          </h2>
        </div>
      </div>

      {/* Message History List */}
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-6 space-y-4 bg-paper/50"
      >
        {isHistoryLoading && messages.length === 0 ? (
          <div className="flex justify-center items-center h-32">
            <p className="text-body-sm text-ink-muted font-sans">
              Loading conversation history...
            </p>
          </div>
        ) : messages.length === 0 && !isStreaming ? (
          <div className="text-center py-12">
            <p className="text-body text-ink font-medium mb-1">
              Conversation Started
            </p>
            <p className="text-body-sm text-ink-muted">
              Ask your Career Advisor anything to begin tailored guidance.
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <ChatMessageBubble
              key={msg.id}
              role={msg.role}
              content={msg.content}
            />
          ))
        )}

        {/* In-Flight Streaming Assistant Message */}
        {isStreaming && (
          <ChatMessageBubble
            role="assistant"
            content={inFlightContent}
            isStreaming={true}
          />
        )}

        {/* Error message alert */}
        {errorMsg && (
          <div className="p-4 rounded-md bg-clay-alert/10 border border-clay-alert text-clay-alert text-body-sm font-sans">
            {errorMsg}
          </div>
        )}
      </div>

      {/* Input Area & Controls */}
      <div className="p-4 border-t border-line bg-paper-raised">
        <div className="flex gap-3 items-end">
          <textarea
            ref={textareaRef}
            id="input-chat-message"
            rows={1}
            value={input}
            onChange={handleTextareaInput}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question or reply..."
            disabled={isStreaming}
            className="flex-1 resize-none rounded-md border border-line bg-paper px-4 py-3 text-body text-ink placeholder:text-ink-muted focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest disabled:opacity-50 font-sans max-h-32"
          />
          <button
            type="button"
            id="btn-send-message"
            onClick={handleSendMessage}
            disabled={isStreaming || !input.trim()}
            className="bg-forest text-white p-3.5 rounded-md hover:bg-forest-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        {/* Subtle thinking indicator per design system §4 (no spinner overlay) */}
        {isStreaming && (
          <p className="text-body-sm text-ink-muted mt-2 font-sans">
            Career Advisor is thinking...
          </p>
        )}
      </div>
    </div>
  );
}
