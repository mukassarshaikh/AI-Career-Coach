"use client";

/**
 * ContourProgress — Signature ascending contour-line SVG progress indicator per design_system.md §4.
 */

interface ContourProgressProps {
  className?: string;
  active?: boolean;
}

export function ContourProgress({ className = "", active = true }: ContourProgressProps) {
  return (
    <div className={`relative w-full overflow-hidden h-6 flex items-center ${className}`}>
      <svg
        viewBox="0 0 400 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full text-brass"
        preserveAspectRatio="none"
      >
        <path
          d="M0 20 Q 100 22, 200 12 T 400 4"
          stroke="currentColor"
          strokeWidth="2"
          strokeDasharray="6 4"
          className={active ? "animate-[dash_1.5s_linear_infinite]" : ""}
          strokeLinecap="round"
        />
        <circle cx="396" cy="4" r="3" fill="currentColor" />
      </svg>
      <style jsx>{`
        @keyframes dash {
          to {
            stroke-dashoffset: -20;
          }
        }
      `}</style>
    </div>
  );
}
