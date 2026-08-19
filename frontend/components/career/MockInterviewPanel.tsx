"use client";

import { useEffect, useRef, useState } from "react";
import { UserCheck, Send, Sparkles, AlertCircle } from "lucide-react";
import { sendMessage } from "@/lib/api/careerApi";
import { useSessionHistory } from "@/lib/hooks/useCareer";
import { ChatMessageBubble } from "./ChatMessageBubble";
import type { ChatMessageResponse } from "@/types/career";

interface MockInterviewPanelProps {
  sessionId: string;
}

export function MockInterviewPanel({ sessionId }: MockInterviewPanelProps) {
  const { data: historyData, isLoading, refetch } = useSessionHistory(sessionId);
  const [messages, setMessages] = useState<ChatMessageResponse[]>([]);
  const [answerInput, setAnswerInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [inFlightContent, setInFlightContent] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (historyData?.messages && !isStreaming) {
      setMessages(historyData.messages);
    }
  }, [historyData, isStreaming]);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages, inFlightContent, isStreaming]);

  const sendPromptMessage = async (promptText: string) => {
    if (!promptText.trim() || isStreaming) return;

    setErrorMsg(null);
    setAnswerInput("");

    const userMsg: ChatMessageResponse = {
      id: `temp-user-${Date.now()}`,
      session_id: sessionId,
      role: "user",
      content: promptText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);
    setInFlightContent("");

    let accumulated = "";

    try {
      const response = await sendMessage(sessionId, promptText);
      if (!response.ok) {
        let errStr = "Failed to transmit message.";
        try {
          const json = await response.json();
          errStr = json.detail || json.message || errStr;
        } catch {
          // ignore
        }
        throw new Error(errStr);
      }

      if (!response.body) {
        throw new Error("Empty response body from stream.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data: ")) {
            const rawChunk = trimmed.substring(6);
            if (rawChunk.startsWith("[ERROR:")) {
              setErrorMsg(rawChunk);
            } else {
              accumulated += rawChunk;
              setInFlightContent(accumulated);
            }
          }
        }
      }

      if (buffer.trim().startsWith("data: ")) {
        const rawChunk = buffer.trim().substring(6);
        if (!rawChunk.startsWith("[ERROR:")) {
          accumulated += rawChunk;
          setInFlightContent(accumulated);
        }
      }

      if (accumulated) {
        const assistantMsg: ChatMessageResponse = {
          id: `temp-assistant-${Date.now()}`,
          session_id: sessionId,
          role: "assistant",
          content: accumulated,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Interview evaluation streaming failed.");
    } finally {
      setIsStreaming(false);
      setInFlightContent("");
      refetch();
    }
  };

  const handleStartInterview = () => {
    sendPromptMessage("Hello, I am ready for my mock interview. Please ask your first role-specific question.");
  };

  const handleNextQuestion = () => {
    sendPromptMessage("Thank you. Please ask the next interview question.");
  };

  return (
    <div className="flex flex-col h-full w-full border border-line rounded-xl bg-paper-raised shadow-sm overflow-hidden">
      {/* Mock Interview Header */}
      <div className="px-6 py-4 border-b border-line bg-paper flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-md bg-forest text-white">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-body font-semibold text-ink">Mock Interview Mode</h2>
            <p className="text-body-sm text-ink-muted">
              Role-specific questions and answer evaluation feedback
            </p>
          </div>
        </div>

        <button
          type="button"
          id="btn-next-question"
          onClick={handleNextQuestion}
          disabled={isStreaming}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-line bg-paper-raised text-ink text-body-sm font-medium hover:bg-paper transition-colors disabled:opacity-50"
        >
          <Sparkles className="w-4 h-4 text-forest" />
          <span>Next Question</span>
        </button>
      </div>

      {/* Questions & Feedback History Container */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto p-6 space-y-4 bg-paper/40"
      >
        {isLoading && messages.length === 0 ? (
          <div className="text-center py-12 text-body-sm text-ink-muted">
            Loading mock interview scenario...
          </div>
        ) : messages.length === 0 && !isStreaming ? (
          <div className="text-center py-12 space-y-4">
            <UserCheck className="w-12 h-12 text-forest mx-auto opacity-80" />
            <div>
              <h3 className="text-body font-semibold text-ink">
                Start Mock Interview Practice
              </h3>
              <p className="text-body-sm text-ink-muted max-w-md mx-auto mt-1">
                The interviewer will ask questions tailored to your target role and skill gaps, evaluate your answers, and provide actionable feedback.
              </p>
            </div>
            <button
              type="button"
              id="btn-begin-interview"
              onClick={handleStartInterview}
              className="inline-flex items-center gap-2 bg-forest text-white px-5 py-2.5 rounded-md font-medium text-body-sm hover:bg-forest-hover transition-colors"
            >
              <span>Begin Practice Session</span>
            </button>
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

        {isStreaming && (
          <ChatMessageBubble
            role="assistant"
            content={inFlightContent}
            isStreaming={true}
          />
        )}

        {errorMsg && (
          <div className="flex items-center gap-2 p-4 rounded-md bg-clay-alert/10 border border-clay-alert text-clay-alert text-body-sm">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      {/* Answer Submission Controls */}
      <div className="p-4 border-t border-line bg-paper-raised space-y-3">
        <div className="flex gap-3 items-end">
          <textarea
            id="input-interview-answer"
            rows={2}
            value={answerInput}
            onChange={(e) => setAnswerInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendPromptMessage(answerInput);
              }
            }}
            placeholder="Type your interview answer here..."
            disabled={isStreaming}
            className="flex-1 resize-none rounded-md border border-line bg-paper px-4 py-3 text-body text-ink placeholder:text-ink-muted focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest disabled:opacity-50 font-sans max-h-32"
          />
          <button
            type="button"
            id="btn-submit-answer"
            onClick={() => sendPromptMessage(answerInput)}
            disabled={isStreaming || !answerInput.trim()}
            className="bg-forest text-white px-5 py-3 rounded-md hover:bg-forest-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium text-body-sm flex items-center gap-2"
          >
            <span>Submit Answer</span>
            <Send className="w-4 h-4" />
          </button>
        </div>

        {isStreaming && (
          <p className="text-body-sm text-ink-muted font-sans">
            Interviewer is evaluating your response...
          </p>
        )}
      </div>
    </div>
  );
}
