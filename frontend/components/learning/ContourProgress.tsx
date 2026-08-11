"use client";

/**
 * ContourProgress — Progress bar styled with contour-line pattern per design_system.md §4.
 */

interface ContourProgressProps {
  value: number; // 0 to 100
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function ContourProgress({
  value,
  className = "",
  size = "md",
}: ContourProgressProps) {
  const percentage = Math.min(100, Math.max(0, value));

  const heightClasses = {
    sm: "h-2",
    md: "h-3.5",
    lg: "h-5",
  }[size];

  return (
    <div
      className={`relative w-full bg-paper rounded-full overflow-hidden border border-line ${heightClasses} ${className}`}
      role="progressbar"
      aria-valuenow={percentage}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      {/* Active progress fill */}
      <div
        className="h-full bg-brass transition-all duration-500 ease-out relative overflow-hidden"
        style={{ width: `${percentage}%` }}
      >
        {/* Signature contour line overlay texture */}
        <svg
          className="absolute inset-0 w-full h-full opacity-30 pointer-events-none"
          preserveAspectRatio="none"
          viewBox="0 0 100 20"
        >
          <path
            d="M 0 10 Q 25 3, 50 12 T 100 8"
            fill="none"
            stroke="var(--color-ink)"
            strokeWidth="1.5"
            strokeDasharray="3 3"
          />
        </svg>
      </div>
    </div>
  );
}
