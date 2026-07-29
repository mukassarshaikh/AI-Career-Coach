import type { Metadata } from "next";

export const metadata: Metadata = { title: "Resume Detail" };

interface Props {
  params: { id: string };
}

export default function ResumeDetailPage({ params }: Props) {
  return (
    <div>
      <h1 className="text-2xl font-bold text-foreground">Resume {params.id}</h1>
      <p className="text-muted-foreground mt-2">
        ATS score, grammar suggestions, keyword gaps. (Implemented in Phase 1)
      </p>
    </div>
  );
}
