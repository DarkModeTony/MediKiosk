import { fetchApi } from "./client";

export interface SessionCreateRequest {
  patient_id?: string;
  language: string;
}

export interface SessionCreateResponse {
  session_token: string;
  expires_at: string;
  encounter_id?: string | null;
  patient_id?: string | null;
}

export async function createKioskSession(data: SessionCreateRequest): Promise<SessionCreateResponse> {
  // In development, mock the response if the backend is unavailable
  try {
    return await fetchApi<SessionCreateResponse>("/kiosk/session", {
      method: "POST",
      body: JSON.stringify(data),
    });
  } catch (e) {
    if (process.env.NEXT_PUBLIC_DATA_MODE !== "mock") throw e;
    console.warn("Backend unavailable, using mock session creation");
    return {
      session_token: "mock-session-raj-123", // Canonical Demo ID
      expires_at: new Date(Date.now() + 15 * 60000).toISOString(),
    };
  }
}
