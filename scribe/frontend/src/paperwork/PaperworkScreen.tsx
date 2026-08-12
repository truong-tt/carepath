import { useCallback, useEffect, useRef, useState } from "react";
import { PAPERWORK } from "../content/paperwork";
import { useDemoCapability } from "../demo/useDemoCapability";
import DocumentCapture from "../visit/DocumentCapture";
import DocumentReview from "../visit/DocumentReview";
import { riskLabel } from "../visit/riskLabels";
import { isGated, spokenText, type VisitTurn } from "../visit/types";
import { confirmTurn, startVisit } from "../visit/useVisitSocket";
import "./paperwork.css";

/**
 * Translate a Vietnamese medical document, as its own task.
 *
 * The reader already existed and already ran every line through the risk engine
 * and the clinician gate — but it was mounted inside the doctor's column of a
 * started visit, so translating a prescription meant opening an interpreted
 * consultation first. This screen is the front door it was missing.
 *
 * It composes three endpoints that already exist and adds no fourth:
 *
 *   POST /api/sessions                     -> a session id (consent only)
 *   POST /api/v1/visits/{id}/documents     -> the lines, already gated
 *   POST /api/turns/{id}/confirm           -> one line released
 *
 * There is deliberately NO WebSocket and NO microphone here. `useVisitSocket`
 * carries speech turns and is never opened; nothing on this route touches audio.
 * That absence is what makes a public paperwork door safe, so it is asserted in
 * the e2e suite rather than left as an implementation detail.
 */
export default function PaperworkScreen({ backHref }: { backHref: string }) {
  const capability = useDemoCapability();
  const [visitId, setVisitId] = useState<string | null>(null);
  const [consented, setConsented] = useState(false);
  const [starting, setStarting] = useState(false);
  const [turns, setTurns] = useState<VisitTurn[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reading, setReading] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const startedAt = useRef(0);

  // Translation is one call per line at roughly 13s/line on the live provider,
  // so a six-line prescription is over a minute. A spinner alone reads as a
  // hang; the elapsed count is what makes the wait legible as work.
  useEffect(() => {
    if (!reading) {
      setElapsed(0);
      return;
    }
    startedAt.current = Date.now();
    const timer = window.setInterval(() => {
      setElapsed(Math.round((Date.now() - startedAt.current) / 1000));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [reading]);

  const begin = useCallback(async () => {
    setStarting(true);
    setError(null);
    try {
      // Patient context is optional here: reading a document does not need an
      // age or a presenting complaint, and asking for them would be collecting
      // more than the task requires.
      setVisitId(await startVisit({}));
    } catch {
      setError(PAPERWORK.errors.start);
    } finally {
      setStarting(false);
    }
  }, []);

  const onTurns = useCallback((incoming: VisitTurn[]) => {
    setReading(false);
    setError(null);
    setTurns((current) => [...current, ...incoming]);
  }, []);

  const onConfirm = useCallback(async (turn: VisitTurn, edited?: string) => {
    setBusy(true);
    setError(null);
    try {
      const confirmed = await confirmTurn(turn.id, edited);
      setTurns((current) => current.map((t) => (t.id === confirmed.id ? confirmed : t)));
    } catch {
      setError(PAPERWORK.errors.confirm);
    } finally {
      setBusy(false);
    }
  }, []);

  const held = turns.filter(isGated);
  const released = turns.filter((turn) => !isGated(turn));

  if (capability === "off") {
    return (
      <div className="paper">
        <Bar backHref={backHref} />
        <main className="p-wrap paper__main">
          <section className="paper__notice paper__notice--off">
            <h2>{PAPERWORK.offlineTitle}</h2>
            <p>{PAPERWORK.offlineBody}</p>
            <a className="p-cta" href="mailto:tranth3truong@gmail.com">
              {PAPERWORK.offlineCta}
            </a>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="paper">
      <Bar backHref={backHref} />
      <main className="p-wrap paper__main">
        <header className="p-reg paper__head">
          <span className="p-reg__mark p-mark">{PAPERWORK.label}</span>
          <h1 className="p-reg__vi">{PAPERWORK.title}</h1>
          <p className="p-reg__en p-lede">{PAPERWORK.lede}</p>
        </header>

        {visitId === null ? (
          <section className="paper__consent" aria-label={PAPERWORK.consentCta}>
            <label className="paper__consent-check">
              <input
                type="checkbox"
                checked={consented}
                onChange={(event) => setConsented(event.target.checked)}
              />
              <span>{PAPERWORK.consent}</span>
            </label>
            <button
              type="button"
              className="p-cta paper__cta"
              disabled={!consented || starting}
              onClick={() => void begin()}
            >
              {PAPERWORK.consentCta}
            </button>
            <p className="paper__fine">{PAPERWORK.consentNote}</p>
          </section>
        ) : (
          <>
            <section className="paper__capture" aria-label={PAPERWORK.emptyTitle}>
              <DocumentCapture
                visitId={visitId}
                onTurns={onTurns}
                disabled={reading}
                onStart={() => setReading(true)}
                onFail={() => setReading(false)}
              />
              {turns.length === 0 && !reading ? (
                <p className="paper__fine">{PAPERWORK.emptyBody}</p>
              ) : null}
            </section>

            {reading ? (
              <p className="paper__wait" role="status">
                <span className="paper__spin" aria-hidden="true" />
                <span>
                  {PAPERWORK.waiting}
                  <span className="paper__elapsed">{PAPERWORK.elapsed(elapsed)}</span>
                  {elapsed >= 15 ? (
                    <span className="paper__elapsed">{PAPERWORK.waitingSlow}</span>
                  ) : null}
                </span>
              </p>
            ) : null}

            {error ? (
              <p className="paper__error" role="alert">
                {error}
              </p>
            ) : null}

            <DocumentReview
              turns={held}
              onConfirm={(turn, edited) => void onConfirm(turn, edited)}
              busy={busy}
              renderChips={(turn) => <Chips turn={turn} />}
            />

            <PatientSheet turns={released} />
          </>
        )}
      </main>
    </div>
  );
}

function Bar({ backHref }: { backHref: string }) {
  return (
    <nav className="p-nav" aria-label={PAPERWORK.title}>
      <a className="p-nav__brand" href={backHref}>
        <span>CarePath</span>
      </a>
      <div className="p-nav__end">
        <a className="p-nav__back" href={backHref}>
          {PAPERWORK.navBack}
        </a>
      </div>
    </nav>
  );
}

function Chips({ turn }: { turn: VisitTurn }) {
  const kinds = [...new Set(turn.risk_spans.map((span) => span.kind))];
  if (kinds.length === 0) return null;
  return (
    <ul className="paper__chips">
      {kinds.map((kind) => (
        <li key={kind}>{riskLabel(kind).vi}</li>
      ))}
    </ul>
  );
}

/**
 * The sheet the patient is actually handed.
 *
 * Built from released turns only, so a line the clinician has not confirmed
 * cannot reach it — the gate decides what is here, not this component. Rendered
 * on the shared register (DEC-0022) so a held line is the right column left
 * empty, at the same grid position it occupies on the landing page and the demo
 * hub. Held lines are not listed here at all: their absence from this sheet IS
 * the withholding.
 */
function PatientSheet({ turns }: { turns: VisitTurn[] }) {
  return (
    <section className="paper__sheet" aria-labelledby="sheet-title">
      <div className="p-reg paper__sheet-head">
        <span className="p-reg__mark p-mark">{PAPERWORK.sheetTitle}</span>
        <p className="p-reg__wide paper__fine">
          {turns.length > 0 ? PAPERWORK.sheetReady(turns.length) : PAPERWORK.sheetEmpty}
        </p>
      </div>

      {turns.length > 0 ? (
        <ol className="paper__rows">
          {turns.map((turn, index) => (
            <li className={`p-reg p-reg--ruled${index === 0 ? " p-reg--top" : ""}`} key={turn.id}>
              <span className="p-reg__mark p-ord">{String(index + 1).padStart(2, "0")}</span>
              <span className="p-reg__vi paper__vi" lang="vi">
                {turn.source_text}
              </span>
              <span className="p-reg__en paper__en" lang="en">
                {spokenText(turn)}
              </span>
            </li>
          ))}
        </ol>
      ) : null}

      <p className="paper__fine paper__sheet-note" id="sheet-title">
        {PAPERWORK.sheetNote}
      </p>
    </section>
  );
}
