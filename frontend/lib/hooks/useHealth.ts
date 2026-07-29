/**
 * useHealth — TanStack Query hook for the backend health-check.
 * Used on the dashboard to verify connectivity during development.
 */

import { useQuery } from "@tanstack/react-query";
import { getHealth, getHealthAuthenticated } from "@/lib/api/healthApi";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    staleTime: 60_000,
  });
}

export function useHealthAuthenticated() {
  return useQuery({
    queryKey: ["health", "auth"],
    queryFn: getHealthAuthenticated,
    staleTime: 60_000,
  });
}
