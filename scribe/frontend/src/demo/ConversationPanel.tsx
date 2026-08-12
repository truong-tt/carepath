import { useCallback, useEffect, useRef, useState } from "react";
import { DEMO } from "../content/demo";
import { useVisitSocket } from "../visit/useVisitSocket";
import { isGated, type VisitTurn } from "../visit/types";
import { riskLabel } from "../visit/riskLabels";

const PANEL = DEMO.panels.conversation;

/**
 * Two-way consultation, typed rather than spoken.
 *
 * Deliberately no microphone here. The mic on the real visit screen is gated
 * behind recorded consent, and a public page cannot obtain consent from a
 * patient who is not in the room — so this panel demonstrates the risk gate
 * without ever opening a capture device.
 *
 * The quota is charged when the session is created, because the conversation
 * itself runs over the websocket, which a serverless function cannot proxy.
 */
export default function ConversationPanel() {
  const [visitId, setVisitId] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [doctorView, setDoctorView] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const { turns, connection, error: socketError, pending, sendTurn } = useVisitSocket(visitId);

  const start = useCallback(async (): Promise<string | null> => {
    setStarting(true);
    setError(null);
    try {
      const response = await fetch("/api/demo/session", { method: "POST" });
      const body = (await response.json()) as { visitId?: string; error?: string };
      if (!response.ok || !body.visitId) {
        setError(response.status === 429 ? DEMO.errors.quota : (body.error ?? DEMO.errors.upstream));
        return null;
      }
      setVisitId(body.visitId);
      return body.visitId;
    } catch {
      setError(DEMO.errors.upstream);
      return null;
    } finally {
      setStarting(false);
    }
  }, []);

  // The session is created over HTTP and the socket opens in an effect after
  // `visitId` lands, so the very first line is always typed before there is
  // anything to send it down. Hold it here and flush on open, rather than
  // letting the visitor's first attempt fail with "not connected".
  const [queued, setQueued] = useState<string | null>(null);

  const submit = useCallback(
    async (value: string) => {
      const line = value.trim();
      if (!line) return;
      setText("");
      if (visitId && connection === "open") {
        sendTurn("doctor", "vi", line);
        return;
      }
      setQueued(line);
      if (!visitId) await start();
    },
    [visitId, connection, start, sendTurn],
  );

  useEffect(() => {
    if (queued === null || connection !== "open") return;
    sendTurn("doctor", "vi", queued);
    setQueued(null);
  }, [queued, connection, sendTurn]);

  // Keep focus in the field after a send so a visitor can try several lines.
  useEffect(() => {
    if (!pending) inputRef.current?.focus();
  }, [pending]);

  const busy =
    starting || pending || queued !== null || (visitId !== null && connection === "connecting");

  return (
    <section className="d-panel" aria-label={PANEL.title}>
      <div className="d-panel__head">
        <span className="p-label">{PANEL.label}</span>
        <h2>{PANEL.title}</h2>
        <p className="d-panel__body">{PANEL.body}</p>
      </div>

      <form
        className="d-say"
        onSubmit={(event) => {
          event.preventDefault();
          void submit(text);
        }}
      >
        <label className="d-say__label" htmlFor="demo-say">
          {PANEL.inputLabel}
        </label>
        <div className="d-say__row">
          <input
            id="demo-say"
            ref={inputRef}
            className="d-say__input"
            lang="vi"
            value={text}
            placeholder={PANEL.placeholder}
            onChange={(event) => setText(event.target.value)}
            disabled={busy}
          />
          <button type="submit" className="p-cta d-cta" disabled={busy || !text.trim()}>
            {PANEL.send}
          </button>
        </div>
      </form>

      <div className="d-presets">
        <span className="d-presets__label">{PANEL.presetsLabel}</span>
        <ul>
          {PANEL.presets.map((preset) => (
            <li key={preset}>
              <button type="button" disabled={busy} onClick={() => void submit(preset)}>
                {preset}
              </button>
            </li>
          ))}
        </ul>
      </div>

      {busy && (
        <p className="d-wait" role="status" aria-live="polite">
          <span className="d-wait__spin" aria-hidden="true" />
          <span>{DEMO.waiting.sample}</span>
        </p>
      )}

      {(error || socketError) && (
        <p className="d-error" role="alert">
          {error ?? socketError?.message}
        </p>
      )}

      {turns.length > 0 && (
        <div className="d-result">
          <p className="d-result__head">
            <span className="d-badge">{DEMO.liveBadge}</span>
            <button
              type="button"
              className="d-toggle"
              aria-pressed={doctorView}
              onClick={() => setDoctorView((value) => !value)}
            >
              {doctorView ? DEMO.hideDoctorView : DEMO.showDoctorView}
            </button>
          </p>
          <ul className="d-rows">
            {turns.map((turn: VisitTurn) => {
              const gated = isGated(turn);
              const kinds = [...new Set(turn.risk_spans.map((span) => span.kind))];
              return (
                <li key={turn.id} className={`d-row${gated ? " is-gated" : ""}`}>
                  <p className="d-row__vi" lang="vi">
                    {turn.source_text}
                  </p>
                  {gated && !doctorView ? (
                    <p className="d-row__held">
                      <span className="d-seal">{DEMO.gated}</span>
                      <span className="d-row__heldnote">{DEMO.gatedNote}</span>
                    </p>
                  ) : (
                    <p className="d-row__en" lang="en">
                      {turn.corrected_text || turn.translation}
                    </p>
                  )}
                  {kinds.length > 0 && (
                    <ul className="d-flags">
                      {kinds.map((kind) => (
                        <li key={kind} className={gated ? "is-gated" : undefined}>
                          {riskLabel(kind).vi}
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
          <p className="d-disclaim">{DEMO.resultDisclaimer}</p>
        </div>
      )}
    </section>
  );
}
