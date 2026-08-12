import { useCallback, useEffect, useRef, useState } from "react";
import logoUrl from "../assets/carepath.svg";
import ConversationPanel from "./ConversationPanel";
import { DEMO } from "../content/demo";
import { isGated, type VisitTurn } from "../visit/types";
import { riskLabel } from "../visit/riskLabels";
import { useDemoCapability } from "./useDemoCapability";
import "./demo.css";

const MAX_BYTES = 4 * 1024 * 1024;

type Phase =
  | { kind: "idle" }
  | { kind: "running"; sample: boolean; since: number }
  | { kind: "done"; sample: boolean; turns: VisitTurn[] }
  | { kind: "error"; message: string };

interface DemoResponse {
  turns?: VisitTurn[];
  sample?: boolean;
  remaining?: number;
  error?: string;
}

/** Map a transport failure onto copy a Vietnamese doctor can act on. */
function messageFor(status: number, body: DemoResponse | null): string {
  if (status === 429) return DEMO.errors.quota;
  if (status === 413) return DEMO.errors.tooLarge;
  if (status === 422) return DEMO.errors.unreadable;
  if (body?.error) return body.error;
  return DEMO.errors.upstream;
}

function ElapsedNotice({ since, sample }: { since: number; sample: boolean }) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const id = window.setInterval(() => setSeconds(Math.round((Date.now() - since) / 1000)), 1000);
    return () => window.clearInterval(id);
  }, [since]);

  return (
    <p className="d-wait" role="status" aria-live="polite">
      <span className="d-wait__spin" aria-hidden="true" />
      <span>
        <b>{sample ? DEMO.waiting.sample : DEMO.waiting.upload}</b>
        {!sample && (
          <>
            {" "}
            <span className="d-wait__slow">{DEMO.waiting.uploadSlow}</span>
          </>
        )}
        {seconds > 2 && <span className="d-wait__elapsed">{DEMO.waiting.elapsed(seconds)}</span>}
      </span>
    </p>
  );
}

/**
 * One translated line.
 *
 * The gated state is the point of the demo, so it is rendered as a withholding
 * — seal rule, the English replaced by the waiting notice — rather than as a
 * badge next to text the patient supposedly cannot see. Showing the English
 * anyway with a warning label would demonstrate the opposite of the product.
 */
function TurnRow({ turn, doctorView }: { turn: VisitTurn; doctorView: boolean }) {
  const gated = isGated(turn);
  const kinds = [...new Set(turn.risk_spans.map((span) => span.kind))];

  return (
    <li className={`d-row${gated ? " is-gated" : ""}`}>
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
}

function DocumentPanel({
  panel,
  allowSample,
  allowUpload,
}: {
  panel: { label: string; title: string; body: string; uploadCta: string; uploadHint: string };
  allowSample: boolean;
  allowUpload: boolean;
}) {
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });
  const [remaining, setRemaining] = useState<number | null>(null);
  const [doctorView, setDoctorView] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const run = useCallback(async (file: File | null) => {
    const sample = file === null;
    if (file && file.size > MAX_BYTES) {
      setPhase({ kind: "error", message: DEMO.errors.tooLarge });
      return;
    }
    if (file && !file.type.startsWith("image/")) {
      setPhase({ kind: "error", message: DEMO.errors.notImage });
      return;
    }

    setPhase({ kind: "running", sample, since: Date.now() });

    const form = new FormData();
    // Sample mode ignores the bytes; send a placeholder so the multipart shape
    // matches the real endpoint and only one code path exists here.
    form.append("image", file ?? new File([new Uint8Array([0])], "sample.png", { type: "image/png" }));

    try {
      const response = await fetch(`/api/demo/document${sample ? "?sample=1" : ""}`, {
        method: "POST",
        body: form,
      });
      let body: DemoResponse | null = null;
      try {
        body = (await response.json()) as DemoResponse;
      } catch {
        body = null;
      }

      if (!response.ok) {
        setPhase({ kind: "error", message: messageFor(response.status, body) });
        return;
      }
      if (typeof body?.remaining === "number") setRemaining(body.remaining);

      const turns = body?.turns ?? [];
      if (turns.length === 0) {
        setPhase({ kind: "error", message: DEMO.errors.empty });
        return;
      }
      setPhase({ kind: "done", sample, turns });
    } catch {
      setPhase({ kind: "error", message: DEMO.errors.upstream });
    } finally {
      if (fileRef.current) fileRef.current.value = "";
    }
  }, []);

  const busy = phase.kind === "running";

  return (
    <section className="d-panel" aria-label={panel.title}>
      <div className="d-panel__head">
        <span className="p-label">{panel.label}</span>
        <h2>{panel.title}</h2>
        <p className="d-panel__body">{panel.body}</p>
      </div>

      <div className="d-actions">
        {allowSample && (
          <button
            type="button"
            className="p-cta d-cta"
            onClick={() => void run(null)}
            disabled={busy}
          >
            {DEMO.panels.prescription.sampleCta}
          </button>
        )}
        {allowUpload && (
          <>
            <button
              type="button"
              className="p-cta p-cta--ghost d-cta"
              onClick={() => fileRef.current?.click()}
              disabled={busy}
            >
              {panel.uploadCta}
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              className="d-file"
              aria-label={panel.uploadCta}
              onChange={(event) => void run(event.target.files?.[0] ?? null)}
            />
          </>
        )}
        {remaining !== null && <span className="d-remaining">{DEMO.remaining(remaining)}</span>}
      </div>

      {allowUpload ? (
        <p className="d-hint">{panel.uploadHint}</p>
      ) : (
        !allowSample && <p className="d-notice d-notice--inline">{DEMO.capability.uploadUnavailable}</p>
      )}

      {busy && <ElapsedNotice since={phase.since} sample={phase.sample} />}

      {phase.kind === "error" && (
        <p className="d-error" role="alert">
          {phase.message}
        </p>
      )}

      {phase.kind === "done" && (
        <div className="d-result">
          <p className="d-result__head">
            <span className={phase.sample ? "d-badge d-badge--sample" : "d-badge"}>
              {phase.sample ? DEMO.sampleBadge : DEMO.liveBadge}
            </span>
            <button
              type="button"
              className="d-toggle"
              aria-pressed={doctorView}
              onClick={() => setDoctorView((value) => !value)}
            >
              {doctorView ? DEMO.hideDoctorView : DEMO.showDoctorView}
            </button>
          </p>
          {phase.sample && <p className="d-note">{DEMO.sampleNote}</p>}
          {doctorView && <p className="d-note">{DEMO.doctorViewNote}</p>}
          <ul className="d-rows">
            {phase.turns.map((turn) => (
              <TurnRow key={turn.id} turn={turn} doctorView={doctorView} />
            ))}
          </ul>
          <p className="d-disclaim">{DEMO.resultDisclaimer}</p>
        </div>
      )}
    </section>
  );
}

export default function DemoHub({ backHref = "/" }: { backHref?: string }) {
  const capability = useDemoCapability();

  return (
    <div className="landing demo">
      <nav className="p-nav" aria-label={DEMO.label}>
        <a className="p-nav__brand" href={backHref}>
          <img src={logoUrl} alt="" width={28} height={16} />
          <span>CarePath</span>
        </a>
        <a className="p-nav__back" href={backHref}>
          {DEMO.navBack}
        </a>
      </nav>

      <main className="p-wrap d-main">
        <header className="d-head">
          <span className="p-label">{DEMO.label}</span>
          <h1>{DEMO.title}</h1>
          <p className="p-lede">{DEMO.lede}</p>
        </header>

        {/* Limits before the first run, not in a footer after it. */}
        <section className="d-limits" aria-label={DEMO.limitsTitle}>
          <h2 className="d-limits__title">{DEMO.limitsTitle}</h2>
          <ul>
            {DEMO.limits.map((limit) => (
              <li key={limit}>{limit}</li>
            ))}
          </ul>
        </section>

        {capability === "checking" && <p className="d-wait">{DEMO.capability.checking}</p>}

        {capability === "sample" && (
          <p className="d-notice">
            <b>{DEMO.capability.sampleOnly.title}</b> {DEMO.capability.sampleOnly.body}
          </p>
        )}

        {capability === "off" ? (
          <section className="d-notice d-notice--off">
            <h2>{DEMO.capability.offline.title}</h2>
            <p>{DEMO.capability.offline.body}</p>
            <a className="p-cta d-cta" href="mailto:tranth3truong@gmail.com">
              {DEMO.capability.offline.cta}
            </a>
          </section>
        ) : (
          capability !== "checking" && (
            <>
              <DocumentPanel
                panel={DEMO.panels.prescription}
                allowSample
                allowUpload={capability === "full"}
              />
              <DocumentPanel
                panel={DEMO.panels.discharge}
                allowSample={false}
                allowUpload={capability === "full"}
              />
              {/* Only on the live reader. In scripted mode the canned map
                  covers the scenario and nothing else, so anything a visitor
                  actually types comes back as a "[vi->en] …" echo — a
                  placeholder presented as a translation. docs/deploy.md names
                  this as the reason demo mode is not for a public URL; hiding
                  the panel is what makes it safe for one. */}
              {capability === "full" && <ConversationPanel />}
            </>
          )
        )}
      </main>
    </div>
  );
}
