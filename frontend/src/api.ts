import type { SessionCreateResponse, Turn } from "./types";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function createSession(body: { consent: unknown }): Promise<SessionCreateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`session start failed: ${response.status}`);
  }
  return response.json() as Promise<SessionCreateResponse>;
}

export async function confirmTurn(turnId: string, editedTranslation?: string): Promise<Turn> {
  const response = await fetch(`${API_BASE_URL}/api/turns/${turnId}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ edited_translation: editedTranslation || null }),
  });
  if (!response.ok) {
    throw new Error(`turn confirm failed: ${response.status}`);
  }
  return response.json() as Promise<Turn>;
}

export async function escalateSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/escalate`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`session escalation failed: ${response.status}`);
  }
}

export async function submitFeedback(
  turnId: string,
  body: { reason: string; comment?: string },
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/turns/${turnId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`feedback failed: ${response.status}`);
  }
}

export function websocketUrl(path: string): string {
  const url = new URL(path, API_BASE_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}
