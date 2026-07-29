/**
 * Shared API fetch client.
 *
 * Reads the NextAuth session token and attaches it as a Bearer header on
 * every request to the FastAPI backend.
 *
 * Per frontend_architecture.md §4:
 *   "All requests attach the NextAuth session token automatically via a
 *    shared fetch wrapper (/lib/api/client.ts) that reads the session and
 *    sets the Authorization header."
 */

import { getSession } from "next-auth/react";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
}

export async function apiClient<T>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const { skipAuth = false, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  };

  if (!skipAuth) {
    const session = await getSession();
    if (session) {
      // NextAuth encodes the JWT into the session cookie; we need the raw token.
      // We fetch it via the session endpoint which returns the token in the response.
      const tokenRes = await fetch("/api/auth/session");
      const tokenData = await tokenRes.json();
      if (tokenData?.accessToken) {
        headers["Authorization"] = `Bearer ${tokenData.accessToken}`;
      }
    }
  }

  const res = await fetch(`${BACKEND_URL}${path}`, {
    ...fetchOptions,
    headers,
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API error ${res.status}: ${error}`);
  }

  // Handle 204 No Content
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}
