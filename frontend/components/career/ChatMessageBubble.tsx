"use client";

import React from "react";
import type { ChatRole } from "@/types/career";

interface ChatMessageBubbleProps {
  role: ChatRole;
  content: string;
  isStreaming?: boolean;
  timestamp?: string;
}

function renderInlineText(str: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
  let lastIdx = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(str)) !== null) {
    if (match.index > lastIdx) {
      parts.push(str.substring(lastIdx, match.index));
    }
    const token = match[0];
    if (token.startsWith("**") && token.endsWith("**")) {
      parts.push(
        <strong key={match.index} className="font-semibold text-ink">
          {token.slice(2, -2)}
        </strong>
      );
    } else if (token.startsWith("`") && token.endsWith("`")) {
      parts.push(
        <code
          key={match.index}
          className="px-1.5 py-0.5 rounded bg-forest/10 font-mono text-data-sm text-forest"
        >
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith("*") && token.endsWith("*")) {
      parts.push(
        <em key={match.index} className="italic">
          {token.slice(1, -1)}
        </em>
      );
    }
    lastIdx = match.index + token.length;
  }
  if (lastIdx < str.length) {
    parts.push(str.substring(lastIdx));
  }
  return parts;
}

function renderMarkdownTable(tableLines: string[], keyPrefix: number) {
  const rows = tableLines
    .filter((line) => !line.trim().match(/^\|?[\s:-|]+\|?$/))
    .map((line) =>
      line
        .trim()
        .replace(/^\|/, "")
        .replace(/\|$/, "")
        .split("|")
        .map((cell) => cell.trim())
    );

  if (rows.length === 0) return null;

  const headerRow = rows[0];
  const bodyRows = rows.slice(1);

  return (
    <div key={keyPrefix} className="my-3 overflow-x-auto rounded-lg border border-line bg-paper shadow-xs">
      <table className="w-full text-left border-collapse text-body-sm font-sans">
        {headerRow && (
          <thead>
            <tr className="bg-paper-raised border-b border-line">
              {headerRow.map((cell, i) => (
                <th
                  key={i}
                  className="px-4 py-2.5 font-semibold text-ink border-r border-line last:border-r-0"
                >
                  {renderInlineText(cell)}
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {bodyRows.map((row, rIdx) => (
            <tr
              key={rIdx}
              className="border-b border-line/60 last:border-b-0 hover:bg-paper-raised/50 transition-colors"
            >
              {row.map((cell, cIdx) => (
                <td
                  key={cIdx}
                  className="px-4 py-2.5 text-ink border-r border-line/60 last:border-r-0 align-top whitespace-pre-wrap"
                >
                  {renderInlineText(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function renderFormattedContent(content: string): React.ReactNode {
  // 1. Clean raw <br> tags (case-insensitive) into standard newlines
  const cleanedText = content.replace(/<br\s*\/?>/gi, "\n");

  // 2. Split text into lines to process markdown structures (tables, lists, paragraphs)
  const lines = cleanedText.split("\n");
  const nodes: React.ReactNode[] = [];
  let idx = 0;

  while (idx < lines.length) {
    const line = lines[idx];

    // Check if line is part of a markdown table (starts or contains '|')
    if (line.trim().startsWith("|") || (line.trim().includes("|") && line.trim().endsWith("|"))) {
      const tableLines: string[] = [];
      while (
        idx < lines.length &&
        (lines[idx].trim().startsWith("|") || (lines[idx].trim().includes("|") && lines[idx].trim().endsWith("|")))
      ) {
        tableLines.push(lines[idx]);
        idx++;
      }
      nodes.push(renderMarkdownTable(tableLines, idx));
      continue;
    }

    // Check if line is a list item (starts with •, -, *, or numbered list)
    if (line.trim().match(/^[\s•\-\*]+|^\d+\.\s+/)) {
      const listLines: string[] = [];
      while (idx < lines.length && lines[idx].trim().match(/^[\s•\-\*]+|^\d+\.\s+/)) {
        listLines.push(lines[idx]);
        idx++;
      }
      nodes.push(
        <ul key={idx} className="my-2 space-y-1 pl-4 list-disc marker:text-forest">
          {listLines.map((item, lIdx) => {
            const cleanItem = item.replace(/^[\s•\-\*]+|^\d+\.\s+/, "");
            return (
              <li key={lIdx} className="text-body text-ink leading-relaxed">
                {renderInlineText(cleanItem)}
              </li>
            );
          })}
        </ul>
      );
      continue;
    }

    // Paragraph or Header
    const trimmed = line.trim();
    if (trimmed.startsWith("### ")) {
      nodes.push(
        <h4 key={idx} className="my-2 font-display text-display-xs text-ink">
          {renderInlineText(trimmed.slice(4))}
        </h4>
      );
    } else if (trimmed.startsWith("## ")) {
      nodes.push(
        <h3 key={idx} className="my-3 font-display text-display-sm text-ink">
          {renderInlineText(trimmed.slice(3))}
        </h3>
      );
    } else if (trimmed.startsWith("# ")) {
      nodes.push(
        <h2 key={idx} className="my-3 font-display text-display-md text-ink">
          {renderInlineText(trimmed.slice(2))}
        </h2>
      );
    } else if (trimmed) {
      nodes.push(
        <p key={idx} className="my-1 text-body text-ink leading-relaxed">
          {renderInlineText(line)}
        </p>
      );
    } else {
      // Empty line spacer
      nodes.push(<div key={idx} className="h-2" />);
    }

    idx++;
  }

  return <>{nodes}</>;
}

export function ChatMessageBubble({
  role,
  content,
  isStreaming = false,
}: ChatMessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} my-2.5`}>
      <div
        className={`p-4 rounded-xl font-sans text-body transition-colors ${
          isUser
            ? "bg-forest text-white max-w-[85%] sm:max-w-[75%]"
            : "bg-paper-raised text-ink border border-line shadow-sm max-w-[95%] md:max-w-[88%] w-full"
        }`}
      >
        {isUser ? (
          <span className="whitespace-pre-wrap">{content}</span>
        ) : (
          <div>{renderFormattedContent(content)}</div>
        )}

        {isStreaming && (
          <span className="inline-block w-2 h-4 ml-1.5 bg-forest animate-pulse align-middle rounded-xs" />
        )}
      </div>
    </div>
  );
}

