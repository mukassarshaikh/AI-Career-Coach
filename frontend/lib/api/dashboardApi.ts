import { fetchWithAuth } from "./client";
import type { DashboardSummary } from "@/types/dashboard";

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return fetchWithAuth<DashboardSummary>("/api/v1/dashboard/summary", {
    method: "GET",
  });
}
