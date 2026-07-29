import type { Metadata } from "next";

export const metadata: Metadata = { title: "Resumes" };

export default function ResumePage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-foreground">Resumes</h1>
      <p className="text-muted-foreground mt-2">
        Upload and manage your resumes. (Implemented in Phase 1)
      </p>
    </div>
  );
}
