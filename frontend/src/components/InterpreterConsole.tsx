import { FormEvent, useEffect, useRef, useState } from "react";

import { speakTurn } from "../tts";
import type { TranscriptTurn, WsEvent } from "../types";
import { confirmTurn, escalateSession, getHealth, submitFeedback, websocketUrl } from "../api";
import { copy, type Language } from "../copy";
import { Transcript } from "./Transcript";

type InterpreterConsoleProps = {
  initialSpeaker?: Speaker;
  language?: Language;
  sessionId: string;
};

type Speaker = "doctor" | "patient";

const speakerConfig: Record<Speaker, { lang: "vi" | "en" }> = {
  doctor: { lang: "vi" },
  patient: { lang: "en" },
};

export function InterpreterConsole({ initialSpeaker = "doctor", language = "vi", sessionId }: InterpreterConsoleProps) {
  const text = copy[language].workspace;
  const textRef = useRef(text);
  textRef.current = text;
  const [turns, setTurns] = useState<TranscriptTurn[]>([]);
  const [speaker, setSpeaker] = useState<Speaker>(initialSpeaker);
  const [typedText, setTypedText] = useState("");
  const [status, setStatus] = useState("connecting");
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
        setStatus("connected");
      }
    });
    socket.addEventListener("close", () => {
      if (isCurrentSocket()) {
        setStatus("disconnected");
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
          setWarning(textRef.current.lowConfidence);
        } else if (data.requires_confirmation) {
          setWarning(textRef.current.confirmationRequired);
        } else {
          setWarning(null);
          speakTurn(data.turn);
        }
      }
      if (data.type === "turn_error") {
        setWarning(textRef.current.turnError);
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
      setWarning(text.connectionNotReady);
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
      setWarning(text.confirmFailed);
    }
  }

  async function handleEscalate() {
    try {
      await escalateSession(sessionId);
      setEscalated(true);
      setWarning(null);
    } catch {
      setWarning(text.escalationFailed);
    }
  }

  async function startRecording(nextSpeaker: Speaker) {
    const config = speakerConfig[nextSpeaker];
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      setWarning(text.connectionNotReadyType);
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setWarning(text.microphoneUnavailable);
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
      setStatus(`recording:${nextSpeaker}`);
    } catch {
      setWarning(text.microphoneDenied);
    }
  }

  function stopRecording() {
    const recorder = recorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
      recorderRef.current = null;
      setStatus("connected");
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  return (
    <main className="workspace" lang={language}>
      {escalated ? (
        <section className="escalation-card" role="alert" aria-live="assertive">
          <h1>{text.escalationTitle}</h1>
          <p>{text.escalationBody}</p>
        </section>
      ) : null}
      <header className="topbar">
        <div>
          {providerMode === "mock" ? <p className="eyebrow">{text.mockDisclaimer}</p> : null}
          <h1>{text.title}</h1>
        </div>
        <button className="escalate" type="button" onClick={() => void handleEscalate()}>
          {text.requestInterpreter}
        </button>
      </header>
      <section className="input-regions" aria-label={text.controls}>
        {(Object.keys(speakerConfig) as Speaker[]).map((key) => (
          <section className="input-region" key={key}>
            <h2>
              <button className="region-select" type="button" aria-pressed={speaker === key} onClick={() => setSpeaker(key)}>
                {key === "doctor" ? `${text.doctor} · ${text.vietnamese}` : `${language === "vi" ? "Người bệnh" : text.patient} · English`}
              </button>
            </h2>
            {speaker === key ? (
              <>
                <button
                  className="talk"
                  type="button"
                  onPointerDown={() => void startRecording(key)}
                  onPointerUp={stopRecording}
                  onPointerCancel={stopRecording}
                >
                  {text.holdToTalk}
                </button>
                <form className="typed" onSubmit={submitTyped}>
                  <label>
                    {text.typedFallback}
                    <input
                      placeholder={text.typedPlaceholder}
                      value={typedText}
                      onChange={(event) => setTypedText(event.target.value)}
                    />
                  </label>
                  <button type="submit">{text.send}</button>
                </form>
              </>
            ) : null}
          </section>
        ))}
      </section>
      <div className="status" role="status">
        <span>{status.startsWith("recording:") ? text.recording.replace("{speaker}", status.endsWith("doctor") ? text.doctor : text.patient) : text[status as "connecting" | "connected" | "disconnected"]}</span>
        {warning ? <strong>{warning}</strong> : null}
      </div>
      {turns.some((turn) => turn.low_confidence) ? (
        <section className="low-confidence" role="alert">
          {text.lowConfidence}
        </section>
      ) : null}
      <section className="confirmations" aria-label={text.confirmations}>
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
                  {text.confirmationRequiredLabel} · {riskText(text, turn.risk_tier)}
                  {turn.risk_tier === "critical" ? ` · ${text.interpreterRecommended}` : ""}
                </p>
                <p lang={turn.src_lang}>{turn.source_text}</p>
                <p lang={turn.tgt_lang}>{turn.translation}</p>
                {turn.readback ? (
                  <div className="readback">
                    <p>
                      <strong>{text.readback}:</strong> <span lang={turn.src_lang}>{turn.readback.back_translation}</span>
                    </p>
                    {turn.readback.entities.length ? (
                      <table>
                        <thead>
                          <tr>
                            <th>{text.entity}</th>
                            <th>{text.source}</th>
                            <th>{text.translation}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {turn.readback.entities.map((entity, index) => (
                            <tr key={`${entity.kind}-${index}`}>
                              <td>{riskKindText(text, entity.kind)}</td>
                              <td lang={turn.src_lang}>{entity.source_text}</td>
                              <td lang={turn.tgt_lang}>{entity.translated_text}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : null}
                    {turn.readback.flags.length ? <p>{text.flags}: {text.riskKind.other}</p> : null}
                  </div>
                ) : null}
                <label className="edit-translation">
                  {text.editTranslation}
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
                  {text.confirm}
                </button>
                <button
                  type="button"
                  onClick={() => void handleConfirm(turn, edits[turn.id] ?? turn.translation)}
                >
                  {text.saveEdit}
                </button>
                <button className="escalate" type="button" onClick={() => void handleEscalate()}>
                  {text.escalate}
                </button>
              </div>
            </article>
          ))}
      </section>
      <Transcript
        language={language}
        turns={turns}
        onFeedback={async (turnId, reason, comment) => {
          await submitFeedback(turnId, { reason, comment });
        }}
      />
    </main>
  );
}

function riskText(text: (typeof copy)[Language]["workspace"], value: string) {
  return text.risk[value as keyof typeof text.risk] ?? text.risk.other;
}

function riskKindText(text: (typeof copy)[Language]["workspace"], value: string) {
  return text.riskKind[value as keyof typeof text.riskKind] ?? text.riskKind.other;
}
