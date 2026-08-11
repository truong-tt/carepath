import { useCallback, useEffect, useRef, useState } from "react";
import type { VisitTurn } from "./types";

const API_BASE: string = import.meta.env.VITE_API_BASE ?? "";

export type ConnectionState = "idle" | "connecting" | "open" | "closed";

export interface VisitError {
  message: string;
  retryable: boolean;
}

function socketUrl(visitId: string): string {
  const base = API_BASE || window.location.origin;
  const url = new URL(`/ws/sessions/${visitId}`, base);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}

/**
 * Client for the existing interpreter websocket protocol
 * (session_state / turn_result / turn_error). Reconnecting replays the whole
 * transcript for free: the server sends session_state on every accept.
 */
export function useVisitSocket(visitId: string | null) {
  const [turns, setTurns] = useState<VisitTurn[]>([]);
  const [connection, setConnection] = useState<ConnectionState>("idle");
  const [error, setError] = useState<VisitError | null>(null);
  const [pending, setPending] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const onTurnRef = useRef<((turn: VisitTurn) => void) | null>(null);

  useEffect(() => {
    if (!visitId) return;
    setConnection("connecting");
    const socket = new WebSocket(socketUrl(visitId));
    socketRef.current = socket;

    socket.onopen = () => setConnection("open");
    socket.onclose = () => setConnection("closed");
    socket.onerror = () =>
      setError({ message: "Mất kết nối tới máy chủ.", retryable: true });

    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data as string);
      if (payload.type === "session_state") {
        setTurns(payload.turns ?? []);
        return;
      }
      if (payload.type === "turn_result") {
        setPending(false);
        setError(null);
        const turn: VisitTurn = {
          ...payload.turn,
          requires_confirmation: payload.requires_confirmation,
          low_confidence: payload.low_confidence,
        };
        setTurns((current) => [...current.filter((item) => item.id !== turn.id), turn]);
        onTurnRef.current?.(turn);
        return;
      }
      if (payload.type === "turn_error") {
        setPending(false);
        setError({ message: payload.message, retryable: payload.retryable !== false });
      }
    };

    return () => {
      socketRef.current = null;
      socket.close();
    };
  }, [visitId]);

  const sendTurn = useCallback(
    (speaker: string, lang: string, text: string, confidence?: number) => {
      const socket = socketRef.current;
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        setError({ message: "Chưa kết nối tới máy chủ.", retryable: true });
        return;
      }
      setPending(true);
      setError(null);
      socket.send(
        JSON.stringify({
          type: "text_turn",
          speaker,
          lang,
          text,
          // Omitted rather than defaulted when the browser does not report one:
          // the server treats an absent confidence as a typed turn.
          ...(confidence === undefined ? {} : { confidence }),
        }),
      );
    },
    [],
  );

  /** Patch a turn in place after the clinician confirms or edits it. */
  const replaceTurn = useCallback((turn: VisitTurn) => {
    setTurns((current) => current.map((item) => (item.id === turn.id ? turn : item)));
  }, []);

  /** Merge turns created outside the socket, e.g. read from a document. */
  const addTurns = useCallback((incoming: VisitTurn[]) => {
    setTurns((current) => {
      const ids = new Set(incoming.map((turn) => turn.id));
      return [...current.filter((turn) => !ids.has(turn.id)), ...incoming];
    });
  }, []);

  const setOnTurn = useCallback((handler: ((turn: VisitTurn) => void) | null) => {
    onTurnRef.current = handler;
  }, []);

  return {
    turns,
    connection,
    error,
    pending,
    sendTurn,
    replaceTurn,
    addTurns,
    setOnTurn,
    clearError: () => setError(null),
  };
}

export async function startVisit(patientContext: Record<string, string>): Promise<string> {
  const response = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      consent: {
        ai_disclosure: true,
        interpreter_right: true,
        scope: "translation_aid",
        recorded_at: new Date().toISOString(),
        patient_context: patientContext,
      },
    }),
  });
  if (!response.ok) throw new Error(`start visit failed: ${response.status}`);
  return (await response.json()).session_id as string;
}

export async function confirmTurn(
  turnId: string,
  editedTranslation?: string,
): Promise<VisitTurn> {
  const response = await fetch(`${API_BASE}/api/turns/${turnId}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ edited_translation: editedTranslation ?? null }),
  });
  if (!response.ok) throw new Error(`confirm failed: ${response.status}`);
  return (await response.json()) as VisitTurn;
}

export async function escalateVisit(visitId: string): Promise<void> {
  await fetch(`${API_BASE}/api/sessions/${visitId}/escalate`, { method: "POST" });
}

export async function finishVisit(visitId: string) {
  const response = await fetch(`${API_BASE}/api/v1/visits/${visitId}/note`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `finish failed: ${response.status}`);
  }
  return response.json();
}
