import type { Metadata } from "next";

export const metadata: Metadata = { title: "Career Advisor" };

export default function CareerPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-foreground">Career Advisor</h1>
      <p className="text-muted-foreground mt-2">
        Chat window and mock interview. (Implemented in Phase 3)
      </p>
    </div>
  );
}
