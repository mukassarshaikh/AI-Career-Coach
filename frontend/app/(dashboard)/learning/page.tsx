import type { Metadata } from "next";

export const metadata: Metadata = { title: "Learning Roadmaps" };

export default function LearningPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-foreground">Learning Roadmaps</h1>
      <p className="text-muted-foreground mt-2">
        Your personalized roadmaps. (Implemented in Phase 2)
      </p>
    </div>
  );
}
