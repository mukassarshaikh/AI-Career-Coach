import { fetchWithAuth } from "./client";

export async function deleteUserAccount(): Promise<{ deleted: boolean }> {
  return fetchWithAuth<{ deleted: boolean }>("/api/v1/user/me", {
    method: "DELETE",
  });
}
