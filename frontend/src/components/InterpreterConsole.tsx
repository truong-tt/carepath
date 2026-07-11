import { FormEvent, useEffect, useRef, useState } from "react";

import { speakTurn } from "../tts";
import type { TranscriptTurn, WsEvent } from "../types";
import { confirmTurn, escalateSession, getHealth, submitFeedback, websocketUrl } from "../api";
import type { Language } from "../copy";
import { Transcript } from "./Transcript";

type InterpreterConsoleProps = {
  language?: Language;
  sessionId: string;
};

type Speaker = "doctor" | "patient";

const speakerConfig: Record<Speaker, { label: string; lang: "vi" | "en" }> = {
  doctor: { label: "Doctor Vietnamese", lang: "vi" },
  patient: { label: "Patient English", lang: "en" },
};

export function InterpreterConsole({ language = "vi", sessionId }: InterpreterConsoleProps) {
  const [turns, setTurns] = useState<TranscriptTurn[]>([]);
  const [speaker, setSpeaker] = useState<Speaker>("doctor");
  const [typedText, setTypedText] = useState("");
  const [status, setStatus] = useState("Connecting");
  const [warning, setWarning] = useState<string | null>(null);
  const [escalated, setEscalated] = useState(false);
  const [providerMode, setProviderMode] = useState("");
  const [edits, setEdits] = useState<Record<string, string>>({});
  const socketRef = useRef<WebSocket | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    void getHealth()
      .then((health) => setProviderMode(health.provider_mode))
      .catch(() => setProviderMode("unknown"));
    const socket = new WebSocket(websocketUrl(`/ws/sessions/${sessionId}`));
    socketRef.current = socket;
    const isCurrentSocket = () => socketRef.current === socket;
    socket.addEventListener("open", () => {
      if (isCurrentSocket()) {
        setStatus("Connected");
      }
    });
    socket.addEventListener("close", () => {
      if (isCurrentSocket()) {
        setStatus("Disconnected");
      }
    });
    socket.addEventListener("message", (event: MessageEvent<string>) => {
      if (!isCurrentSocket()) {
        return;
      }
      const data = JSON.parse(event.data) as WsEvent;
      if (data.type === "session_state") {
        setTurns(data.turns);
      }
      if (data.type === "turn_result") {
        const nextTurn = {
          ...data.turn,
          low_confidence: data.low_confidence,
          requires_confirmation: data.requires_confirmation,
        };
        setTurns((current) => [...current, nextTurn]);
        if (data.low_confidence) {
          setWarning("Low confidence - please repeat or type.");
        } else if (data.requires_confirmation) {
          setWarning("Doctor confirmation required before patient playback.");
        } else {
          setWarning(null);
          speakTurn(data.turn);
        }
      }
      if (data.type === "turn_error") {
        setWarning(data.message);
      }
    });
    return () => {
      if (isCurrentSocket()) {
        socketRef.current = null;
      }
      socket.close();
    };
  }, [sessionId]);

  function sendJson(payload: unknown) {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      setWarning("Connection is not ready.");
      return false;
    }
    socket.send(JSON.stringify(payload));
    return true;
  }

  function submitTyped(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = typedText.trim();
    if (!text) {
      return;
    }
    const config = speakerConfig[speaker];
    if (sendJson({ type: "text_turn", speaker, lang: config.lang, text })) {
      setTypedText("");
    }
  }

  async function handleConfirm(turn: TranscriptTurn, editedTranslation?: string) {
    try {
      const confirmed = await confirmTurn(turn.id, editedTranslation);
      const nextTurn = {
        ...confirmed,
        low_confidence: turn.low_confidence,
        requires_confirmation: false,
      };
      setTurns((current) => current.map((item) => (item.id === turn.id ? nextTurn : item)));
      setWarning(null);
      speakTurn(confirmed);
    } catch {
      setWarning("Could not confirm the turn.");
    }
  }

  async function handleEscalate() {
    try {
      await escalateSession(sessionId);
      setEscalated(true);
      setWarning(null);
    } catch {
      setWarning("Could not mark the session escalated.");
    }
  }

  async function startRecording(nextSpeaker: Speaker) {
    const config = speakerConfig[nextSpeaker];
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      setWarning("Connection is not ready. Type the turn instead.");
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setWarning("Microphone is unavailable. Type the turn instead.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      streamRef.current = stream;
      recorderRef.current = recorder;
      socket.send(JSON.stringify({ type: "start_turn", speaker: nextSpeaker, lang: config.lang }));
      recorder.addEventListener("dataavailable", async (event) => {
        if (event.data.size > 0 && socket.readyState === WebSocket.OPEN) {
          socket.send(await event.data.arrayBuffer());
        }
      });
      recorder.addEventListener("stop", () => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: "end_turn" }));
        }
        stream.getTracks().forEach((track) => track.stop());
      });
      recorder.start(250);
      setStatus(`Recording ${config.label}`);
    } catch {
      setWarning("Microphone permission denied. Type the turn instead.");
    }
  }

  function stopRecording() {
    const recorder = recorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
      recorderRef.current = null;
      setStatus("Connected");
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  return (
    <main className="workspace" lang={language}>
      {escalated ? (
        <section className="escalation-card" role="alert" aria-live="assertive">
          <h1>Human interpreter requested</h1>
          <p>Pause AI playback and connect a qualified interpreter before continuing.</p>
          <p lang="vi">Đã yêu cầu thông dịch viên. Tạm dừng phát bản dịch AI trước khi tiếp tục.</p>
        </section>
      ) : null}
      <header className="topbar">
        <div>
          <p className="eyebrow">{providerMode ? `${providerMode} mode session` : "Session"}</p>
          <h1>Live interpreter</h1>
        </div>
        <button className="escalate" type="button" onClick={() => void handleEscalate()}>
          Human interpreter
        </button>
      </header>
      <section className="controls" aria-label="Push to talk controls">
        {(Object.keys(speakerConfig) as Speaker[]).map((key) => (
          <button
            className="talk"
            key={key}
            type="button"
            onPointerDown={() => void startRecording(key)}
            onPointerUp={stopRecording}
            onPointerCancel={stopRecording}
          >
            Hold to talk
            <span>{speakerConfig[key].label}</span>
          </button>
        ))}
      </section>
      <form className="typed" onSubmit={submitTyped}>
        <label>
          Speaker
          <select value={speaker} onChange={(event) => setSpeaker(event.target.value as Speaker)}>
            <option value="doctor">Doctor Vietnamese</option>
            <option value="patient">Patient English</option>
          </select>
        </label>
        <label>
          Typed fallback
          <input
            placeholder="Type a turn for mock mode"
            value={typedText}
            onChange={(event) => setTypedText(event.target.value)}
          />
        </label>
        <button type="submit">Send</button>
      </form>
      <div className="status" role="status">
        <span>{status}</span>
        {warning ? <strong>{warning}</strong> : null}
      </div>
      {turns.some((turn) => turn.low_confidence) ? (
        <section className="low-confidence" role="alert">
          <strong>Low confidence.</strong> Please repeat the turn or use typed fallback.
        </section>
      ) : null}
      <section className="confirmations" aria-label="Doctor confirmation">
        {turns
          .filter(
            (turn) =>
              turn.requires_confirmation ||
              turn.status === "awaiting_confirm" ||
              turn.status === "blocked",
          )
          .map((turn) => (
            <article className="confirmation" key={turn.id}>
              <div>
                <p className="meta">
                  Doctor confirmation required · {turn.risk_tier}
                  {turn.risk_tier === "critical" ? " · human interpreter recommended" : ""}
                </p>
                <p>{turn.source_text}</p>
                <p>{turn.translation}</p>
                {turn.readback ? (
                  <div className="readback">
                    <p>
                      <strong>Read-back:</strong> {turn.readback.back_translation}
                    </p>
                    {turn.readback.entities.length ? (
                      <table>
                        <thead>
                          <tr>
                            <th>Entity</th>
                            <th>Source</th>
                            <th>Translation</th>
                          </tr>
                        </thead>
                        <tbody>
                          {turn.readback.entities.map((entity, index) => (
                            <tr key={`${entity.kind}-${index}`}>
                              <td>{entity.kind}</td>
                              <td>{entity.source_text}</td>
                              <td>{entity.translated_text}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : null}
                    {turn.readback.flags.length ? <p>Flags: {turn.readback.flags.join(", ")}</p> : null}
                  </div>
                ) : null}
                <label className="edit-translation">
                  Edit translation
                  <textarea
                    value={edits[turn.id] ?? turn.translation}
                    onChange={(event) =>
                      setEdits((current) => ({ ...current, [turn.id]: event.target.value }))
                    }
                  />
                </label>
              </div>
              <div className="confirmation-actions">
                <button type="button" onClick={() => void handleConfirm(turn)}>
                  Confirm
                </button>
                <button
                  type="button"
                  onClick={() => void handleConfirm(turn, edits[turn.id] ?? turn.translation)}
                >
                  Save edit
                </button>
                <button className="escalate" type="button" onClick={() => void handleEscalate()}>
                  Escalate
                </button>
              </div>
            </article>
          ))}
      </section>
      <Transcript
        turns={turns}
        onFeedback={async (turnId, reason, comment) => {
          await submitFeedback(turnId, { reason, comment });
        }}
      />
    </main>
  );
}
