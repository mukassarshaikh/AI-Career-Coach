/**
 * Health API — typed wrapper for GET /api/v1/health
 */

import { apiClient } from "./client";

export interface HealthResponse {
  status: string;
  message: string;
}

export async function getHealth(): Promise<HealthResponse> {
  return apiClient<HealthResponse>("/api/v1/health", { skipAuth: true });
}

export async function getHealthAuthenticated(): Promise<HealthResponse> {
  return apiClient<HealthResponse>("/api/v1/health/auth");
}
