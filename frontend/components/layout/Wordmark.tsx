"use client";

/**
 * Wordmark logo component matching design_system.md §10.
 * Product name in Fraunces with an inline brass contour-line glyph.
 */

import Link from "next/link";

interface WordmarkProps {
  className?: string;
  collapsed?: boolean;
}

export function Wordmark({ className = "", collapsed = false }: WordmarkProps) {
  return (
    <Link
      href="/resume"
      className={`inline-flex items-center gap-2.5 transition-opacity hover:opacity-90 ${className}`}
    >
      {/* Signature contour-line glyph */}
      <svg
        width="28"
        height="28"
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="text-brass flex-shrink-0"
        aria-hidden="true"
      >
        <path
          d="M4 24C9 24 11 18 16 18C21 18 23 10 28 8"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="28" cy="8" r="2.5" fill="currentColor" />
      </svg>

      {!collapsed && (
        <span className="font-display text-[1.25rem] font-medium tracking-tight text-ink">
          AI Career Coach
        </span>
      )}
    </Link>
  );
}
