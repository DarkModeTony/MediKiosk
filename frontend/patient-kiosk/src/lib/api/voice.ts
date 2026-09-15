import { fetchApi } from "./client";

export async function transcribeVoice(
  audioBlob: Blob,
  languageCode?: string
): Promise<{ transcript: string; detected_language: string; status: string }> {
  if (!audioBlob || audioBlob.size === 0) {
    throw new Error("No audio was recorded. Please speak clearly and try again.");
  }

  const ext = audioBlob.type.includes("wav") ? "wav" : "webm";
  const formData = new FormData();
  formData.append("audio", audioBlob, `recording.${ext}`);
  if (languageCode) formData.append("language_code", languageCode);

  const baseUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/api\/v1\/?$/, "");
  const res = await fetch(`${baseUrl}/api/v1/voice/transcribe`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Voice transcription failed: ${res.status}`);
  }

  return res.json();
}
