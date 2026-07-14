import {
  DragEvent,
  FormEvent,
  Fragment,
  ReactNode,
  useEffect,
  useRef,
  useState,
} from "react";
import logoUrl from "../assets/carepath.svg";
import { copyFor } from "../content/strings";

// Same-origin by default: the combined API serves this site and /api/v1/*.
const API_BASE: string = import.meta.env.VITE_API_BASE ?? "";
const TEAM_CODE: string = import.meta.env.VITE_TEAM_CODE ?? "";

type ToolState = "idle" | "loading" | "error" | "result";
type HealthState = "checking" | "ready" | "demo" | "degraded" | "down";
type FailureKind = "unsupported" | "oversize" | "rateLimit" | "asr" | "llm" | "offline" | "unknown";

interface SoapDraft {
  subjective?: string;
  objective?: string;
  assessment?: string;
  plan?: string;
  review_required?: boolean;
  missing_information?: string[];
}

interface SoapResponse {
  raw_transcript?: string;
  corrected_transcript?: string;
  retrieved_terms?: string[];
  soap?: SoapDraft;
  metadata?: { latency_ms?: number };
}

const isBullet = (line: string) => /^[-*•]\s+/.test(line);
const isNumbered = (line: string) => /^\d+[.)]\s+/.test(line);
const stripMarker = (line: string) => line.replace(/^([-*•]|\d+[.)])\s+/, "");

function boldSegments(line: string): ReactNode {
  const parts = line.split(/\*\*(.+?)\*\*/g);
  return parts.map((part, index) =>
    index % 2 === 1 ? <strong key={index}>{part}</strong> : (
      <Fragment key={index}>{part}</Fragment>
    ),
  );
}

// Port of apps/web renderRich: plain lines become paragraphs, bullet or
// numbered runs become lists, **bold** is honored. React escapes everything.
export function RichText({ text }: { text: string | undefined }) {
  const lines = (text ?? "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length === 0) return <p>-</p>;

  const blocks: ReactNode[] = [];
  let index = 0;
  while (index < lines.length) {
    if (isBullet(lines[index]) || isNumbered(lines[index])) {
      const items: string[] = [];
      while (
        index < lines.length &&
        (isBullet(lines[index]) || isNumbered(lines[index]))
      ) {
        items.push(stripMarker(lines[index]));
        index += 1;
      }
      blocks.push(
        <ul key={`list-${index}`}>
          {items.map((item, itemIndex) => (
            <li key={itemIndex}>{boldSegments(item)}</li>
          ))}
        </ul>,
      );
    } else {
      blocks.push(<p key={`p-${index}`}>{boldSegments(lines[index])}</p>);
      index += 1;
    }
  }
  return <>{blocks}</>;
}

export function classifyFailure(status: number, detail: string): FailureKind {
  const message = detail.toLowerCase();
  if (status === 429) return "rateLimit";
  if (status === 503) return "asr";
  if (status === 502) return "llm";
  if (message.includes("unsupported file")) return "unsupported";
  if (message.includes("too large")) return "oversize";
  return "unknown";
}

class ScribeRequestError extends Error {
  constructor(readonly kind: FailureKind, detail: string) {
    super(detail);
  }
}

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(0)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

interface ScribeToolProps {
  backHref?: string;
}

export default function ScribeTool({
  backHref = "#top",
}: ScribeToolProps) {
  const copy = copyFor("vi");
  const labels = copy.scribeTool;
  const [state, setState] = useState<ToolState>("idle");
  const [health, setHealth] = useState<HealthState>("checking");
  const [file, setFile] = useState<File | null>(null);
  const [context, setContext] = useState("");
  const [dragging, setDragging] = useState(false);
  const [errorKind, setErrorKind] = useState<FailureKind>("unknown");
  const [result, setResult] = useState<SoapResponse | null>(null);
  const [doneSteps, setDoneSteps] = useState(0);
  const [copyState, setCopyState] = useState<"idle" | "done" | "failed">("idle");
  const fileInput = useRef<HTMLInputElement>(null);
  const stepTimers = useRef<number[]>([]);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/api/v1/health`)
      .then(async (response) => {
        if (!response.ok) throw new Error(String(response.status));
        const data = await response.json();
        if (cancelled) return;
        const ready = Boolean(data.asr_ready && data.llm_ready);
        const mock =
          String(data.asr_provider).includes("mock") ||
          String(data.llm_provider) === "offline";
        setHealth(mock ? "demo" : ready ? "ready" : "degraded");
      })
      .catch(() => {
        if (!cancelled) setHealth("down");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => () => stepTimers.current.forEach(window.clearTimeout), []);

  function pickFile(selected: File | null) {
    setFile(selected);
    if (!selected && fileInput.current) fileInput.current.value = "";
  }

  function onDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setDragging(false);
    const dropped = event.dataTransfer.files?.[0];
    if (dropped) pickFile(dropped);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) return;

    const body = new FormData();
    body.append("audio", file);
    if (context.trim()) body.append("encounter_context", context.trim());

    setState("loading");
    setDoneSteps(0);
    stepTimers.current.forEach(window.clearTimeout);
    stepTimers.current = [
      window.setTimeout(() => setDoneSteps(1), 1400),
      window.setTimeout(() => setDoneSteps(2), 3200),
    ];

    try {
      const response = await fetch(`${API_BASE}/api/v1/soap-notes`, {
        method: "POST",
        body,
        headers: TEAM_CODE ? { "X-Team-Code": TEAM_CODE } : undefined,
      });
      const raw = await response.text();
      let data: unknown = null;
      try {
        data = raw ? JSON.parse(raw) : null;
      } catch {
        /* non-JSON error body */
      }
      if (!response.ok) {
        throw new ScribeRequestError(classifyFailure(response.status, raw), raw);
      }
      setResult(data as SoapResponse);
      setDoneSteps(3);
      setState("result");
      setCopyState("idle");
    } catch (error) {
      console.error("Scribe draft request failed", error);
      setErrorKind(error instanceof ScribeRequestError ? error.kind : "offline");
      setState("error");
    } finally {
      stepTimers.current.forEach(window.clearTimeout);
      stepTimers.current = [];
    }
  }

  async function copySoap() {
    const soap = result?.soap;
    if (!soap) return;
    const plain = (value: string | undefined) => (value || "-").replace(/\*\*/g, "");
    const text = [
      labels.copyHeading,
      "",
      `S - ${copy.scribe.soapLabels.s}:\n${plain(soap.subjective)}`,
      "",
      `O - ${copy.scribe.soapLabels.o}:\n${plain(soap.objective)}`,
      "",
      `A - ${copy.scribe.soapLabels.a}:\n${plain(soap.assessment)}`,
      "",
      `P - ${copy.scribe.soapLabels.p}:\n${plain(soap.plan)}`,
    ].join("\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopyState("done");
      window.setTimeout(() => setCopyState("idle"), 1600);
    } catch {
      setCopyState("failed");
    }
  }

  const missing = (result?.soap?.missing_information ?? []).filter(Boolean);
  const latencySeconds =
    result?.metadata?.latency_ms != null
      ? (result.metadata.latency_ms / 1000).toFixed(1)
      : null;
  const soapRows: Array<{ key: "s" | "o" | "a" | "p"; text?: string }> = [
    { key: "s", text: result?.soap?.subjective },
    { key: "o", text: result?.soap?.objective },
    { key: "a", text: result?.soap?.assessment },
    { key: "p", text: result?.soap?.plan },
  ];

  return (
    <div className="site-shell">
      <nav className="site-nav" aria-label="Điều hướng chính">
        <a className="site-nav__brand" href={backHref} aria-label={labels.back}>
          <img src={logoUrl} alt="" />
          <span className="product-breadcrumb">
            <strong>CarePath</strong>
            <span aria-hidden="true">/</span>
            <span>{labels.title}</span>
          </span>
        </a>
        <div className="site-nav__actions">
          <span className="product-shell-status">
            Công cụ thí điểm · Cần bác sĩ duyệt
          </span>
          <a className="nav-cta" href={backHref}>{labels.back}</a>
        </div>
      </nav>

      <main className="tool-shell">
        <header className="tool-header">
          <p className="kicker">{labels.helper}</p>
          <h1>{labels.title}</h1>
          <p className="tool-header__intro">{labels.intro}</p>
          <p className={`health-badge health-badge--${health}`}>
            <span aria-hidden="true" className="health-badge__dot" />
            {labels.health[health]}
          </p>
        </header>

        {state === "idle" && (
          <form className="scribe-panel tool-panel" onSubmit={submit}>
            <div className="tool-start-guide">
              <h2>Ba bước để tạo bản nháp</h2>
              <ol>
              {labels.preStartSteps.map((step, index) => (
                <li key={step}>
                  <span aria-hidden="true">{index + 1}</span>
                  {step}
                </li>
              ))}
              </ol>
              <p>{labels.uploadNotice}</p>
              <a href="/#demo">Xem ca khám mẫu trước</a>
            </div>
            <label
              className={dragging ? "dropzone is-drag" : "dropzone"}
              onDragEnter={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={(event) => {
                event.preventDefault();
                setDragging(false);
              }}
              onDrop={onDrop}
            >
              <strong>{labels.dropzone}</strong>
              <span>{labels.dropzoneHint}</span>
              <input
                accept="audio/*,.wav,.mp3,.m4a,.aac,.flac,.ogg,.oga,.opus,.webm"
                onChange={(event) => pickFile(event.target.files?.[0] ?? null)}
                ref={fileInput}
                type="file"
              />
            </label>
            {file && (
              <p className="file-chip">
                <span>
                  {file.name} · {formatBytes(file.size)}
                </span>
                <button onClick={() => pickFile(null)} type="button">
                  {labels.removeFile}
                </button>
              </p>
            )}
            <label className="tool-context">
              {labels.contextLabel}
              <textarea
                maxLength={500}
                onChange={(event) => setContext(event.target.value)}
                value={context}
              />
            </label>
            <button className="button button--primary" disabled={!file} type="submit">
              {labels.submit}
            </button>
          </form>
        )}

        {state === "loading" && (
          <div className="scribe-panel tool-panel">
            <ol className="progress-rail progress-rail--tool" aria-label={labels.progressLabel}>
              {labels.steps.map((step, index) => (
                <li className={index < doneSteps ? "is-complete" : ""} key={step}>
                  <span aria-hidden="true">
                    {index < doneSteps ? <i className="progress-check" /> : index + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ol>
          </div>
        )}

        {state === "error" && (
          <div className="scribe-panel tool-panel tool-error" role="alert">
            <strong>{labels.errorTitle}</strong>
            <p>{labels.errors[errorKind]}</p>
            <button
              className="button button--secondary"
              onClick={() => setState("idle")}
              type="button"
            >
              {labels.retry}
            </button>
          </div>
        )}

        {state === "result" && (
          <section aria-label={labels.resultTitle} className="scribe-panel">
            <div className="scribe-panel__header">
              <p className="demo__brand">{labels.resultTitle}</p>
              {latencySeconds && (
                <p className="demo__disclosure">
                  {labels.processedIn.replace("{seconds}", latencySeconds)}
                </p>
              )}
            </div>
            <div className="scribe-doc">
              <p className="scribe-status">{labels.draftLabel}</p>
              <dl className="soap-note">
                {soapRows.map((row) => (
                  <div key={row.key}>
                    <dt>
                      <span aria-hidden="true">{row.key.toUpperCase()}</span>
                      {copy.scribe.soapLabels[row.key]}
                    </dt>
                    <dd lang="vi">
                      <RichText text={row.text || labels.emptyTranscript} />
                    </dd>
                  </div>
                ))}
              </dl>
              <div className="tool-missing">
                <strong>{labels.missingTitle}</strong>
                {missing.length > 0 ? (
                  <ul>
                    {missing.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : <p>{labels.emptyMissing}</p>}
              </div>
              <div className="tool-actions">
                <button className="button button--primary" onClick={copySoap} type="button">
                  {copyState === "done"
                    ? labels.copied
                    : copyState === "failed"
                      ? labels.copyFailed
                      : labels.copy}
                </button>
                <button
                  className="button button--secondary"
                  onClick={() => {
                    pickFile(null);
                    setContext("");
                    setResult(null);
                    setState("idle");
                  }}
                  type="button"
                >
                  {labels.newNote}
                </button>
              </div>
            </div>
          </section>
        )}

        <p className="tool-disclaimer">{labels.disclaimer}</p>
      </main>
    </div>
  );
}
