import { getSession } from "next-auth/react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface ApiClientOptions extends RequestInit {
  skipAuth?: boolean;
}

export async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const session = await getSession();
  const headers = new Headers(options.headers || {});

  // Extract authentication token from NextAuth session
  const rawToken = (session as any)?.accessToken;
  const token = typeof rawToken === "string" ? rawToken : null;

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${BACKEND_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.message || JSON.stringify(errorJson);
    } catch {
      // Body not JSON
    }
    throw new Error(errorDetail || `API request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

/**
 * apiClient — alias wrapper supporting options.skipAuth for public unauthenticated endpoints (e.g. GET /api/v1/health).
 */
export async function apiClient<T>(
  endpoint: string,
  options: ApiClientOptions = {}
): Promise<T> {
  const { skipAuth, ...fetchOptions } = options;
  if (skipAuth) {
    const response = await fetch(`${BACKEND_URL}${endpoint}`, fetchOptions);
    if (!response.ok) {
      let errorDetail = response.statusText;
      try {
        const errorJson = await response.json();
        errorDetail = errorJson.detail || errorJson.message || JSON.stringify(errorJson);
      } catch {
        // Body not JSON
      }
      throw new Error(errorDetail || `API request failed with status ${response.status}`);
    }
    return response.json() as Promise<T>;
  }

  return fetchWithAuth<T>(endpoint, fetchOptions);
}
