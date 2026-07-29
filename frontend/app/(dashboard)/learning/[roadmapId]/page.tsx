import type { Metadata } from "next";

interface Props {
  params: { roadmapId: string };
}

export const metadata: Metadata = { title: "Roadmap Detail" };

export default function RoadmapDetailPage({ params }: Props) {
  return (
    <div>
      <h1 className="text-2xl font-bold text-foreground">Roadmap {params.roadmapId}</h1>
      <p className="text-muted-foreground mt-2">
        Timeline, item cards, progress bar. (Implemented in Phase 2)
      </p>
    </div>
  );
}
