"use client";

import {
  Fragment,
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import "./tool.css";

// Port of apps/web/app/index.html + app.js, plus in-browser recording
// (MediaRecorder, no deps), mobile-first layout, team-code bypass and
// friendly 429/size-limit errors. API contract: apps/api/carepath/main.py.

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? ""; // empty => same-origin (local uvicorn)
const API = {
  health: `${API_BASE}/api/v1/health`,
  soap: `${API_BASE}/api/v1/soap-notes`,
};

const MAX_UPLOAD_BYTES = 25 * 1024 * 1024; // keep in sync with main.py
const LONG_AUDIO_SECONDS = 20 * 60;
const TEAM_CODE_KEY = "carepath_team_code";

const ALLOWED_SUFFIXES = [".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".oga", ".opus", ".webm"];

type View = "idle" | "loading" | "error" | "result";
type RecState = "idle" | "recording" | "paused";

interface SoapData {
  subjective?: string;
  objective?: string;
  assessment?: string;
  plan?: string;
  review_required?: boolean;
  missing_information?: string[];
}
interface SoapResponse {
  soap?: SoapData;
  metadata?: { latency_ms?: number };
}

// ---------- Helpers ----------
const fmtBytes = (n: number) => {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
};

const fmtClock = (totalSeconds: number) => {
  const s = Math.floor(totalSeconds);
  const mm = Math.floor(s / 60);
  const ss = String(s % 60).padStart(2, "0");
  if (mm < 60) return `${String(mm).padStart(2, "0")}:${ss}`;
  return `${Math.floor(mm / 60)}:${String(mm % 60).padStart(2, "0")}:${ss}`;
};

const fmtWait = (seconds: number) => {
  if (seconds < 90) return `${Math.max(1, Math.round(seconds))} giây`;
  if (seconds < 90 * 60) return `${Math.ceil(seconds / 60)} phút`;
  return `${Math.ceil(seconds / 3600)} giờ`;
};

const recordingExt = (mimeType: string) => {
  const m = mimeType.toLowerCase();
  if (m.includes("mp4") || m.includes("aac")) return "m4a"; // iOS Safari
  if (m.includes("ogg")) return "ogg";
  return "webm"; // Android / desktop Chrome & Firefox
};

// Read audio duration from a blob URL; null when the browser can't tell
// (MediaRecorder webm blobs often report Infinity — skip those).
const probeDuration = (url: string) =>
  new Promise<number | null>((resolve) => {
    const audio = document.createElement("audio");
    audio.preload = "metadata";
    audio.onloadedmetadata = () =>
      resolve(Number.isFinite(audio.duration) ? audio.duration : null);
    audio.onerror = () => resolve(null);
    audio.src = url;
  });

// ---------- Lightweight SOAP markdown renderer (bullets + bold) ----------
const isBullet = (l: string) => /^[-*•]\s+/.test(l);
const isNumbered = (l: string) => /^\d+[.)]\s+/.test(l);
const stripMarker = (l: string) => l.replace(/^([-*•]|\d+[.)])\s+/, "");

function inlineMd(s: string): ReactNode[] {
  // Split on **bold** — odd indexes are the bold captures. Pure React nodes,
  // no innerHTML, so injection is impossible by construction.
  return s.split(/\*\*(.+?)\*\*/g).map((part, i) => (i % 2 ? <strong key={i}>{part}</strong> : part));
}

function RichText({ text }: { text?: string | null }) {
  const raw = (text ?? "").trim();
  if (!raw) return null;
  const lines = raw.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  const blocks: ReactNode[] = [];
  let i = 0;
  while (i < lines.length) {
    if (isBullet(lines[i]) || isNumbered(lines[i])) {
      const numbered = isNumbered(lines[i]);
      const items: ReactNode[] = [];
      while (i < lines.length && (isBullet(lines[i]) || isNumbered(lines[i]))) {
        items.push(<li key={i}>{inlineMd(stripMarker(lines[i]))}</li>);
        i++;
      }
      blocks.push(
        <ul key={`l${i}`} className={"soap-list" + (numbered ? " soap-list--num" : "")}>
          {items}
        </ul>
      );
    } else {
      blocks.push(<p key={`p${i}`}>{inlineMd(lines[i])}</p>);
      i++;
    }
  }
  return <>{blocks}</>;
}

const accent = (v: string) => ({ "--accent": `var(${v})` }) as CSSProperties;

const SOAP_SECTIONS = [
  { key: "S", ac: "--c-s", title: "Chủ quan", en: "Bệnh sử · Subjective", field: "subjective" as const },
  { key: "O", ac: "--c-o", title: "Khách quan", en: "Khám · Objective", field: "objective" as const },
  { key: "A", ac: "--c-a", title: "Đánh giá", en: "Chẩn đoán · Assessment", field: "assessment" as const },
  { key: "P", ac: "--c-p", title: "Kế hoạch", en: "Plan", field: "plan" as const },
];

const STEP_LABELS = ["Phiên âm", "Hiệu chỉnh thuật ngữ", "Soạn bệnh án SOAP"];

export default function ToolClient() {
  const [view, setView] = useState<View>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [isDrag, setIsDrag] = useState(false);
  const [context, setContext] = useState("");
  const [teamCode, setTeamCode] = useState("");
  const [longAudio, setLongAudio] = useState(false);

  // Recording
  const [recSupported, setRecSupported] = useState(false);
  const [recState, setRecState] = useState<RecState>("idle");
  const [recError, setRecError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Result / error / progress
  const [errorMsg, setErrorMsg] = useState("");
  const [result, setResult] = useState<SoapResponse | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [stepsDone, setStepsDone] = useState(false);
  const [copyLabel, setCopyLabel] = useState("Sao chép");

  // Health badge
  const [health, setHealth] = useState({
    dot: "health-dot--unknown",
    text: "Đang kết nối…",
    title: "Đang kiểm tra trạng thái hệ thống…",
  });

  const audioInputRef = useRef<HTMLInputElement>(null);
  const resultRef = useRef<HTMLElement>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startedAtRef = useRef(0);
  const accumRef = useRef(0);
  const stepTimersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  // ---------- Init ----------
  useEffect(() => {
    setRecSupported(
      typeof MediaRecorder !== "undefined" && !!navigator.mediaDevices?.getUserMedia
    );
    try {
      setTeamCode(localStorage.getItem(TEAM_CODE_KEY) ?? "");
    } catch {
      /* private mode */
    }

    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(API.health);
        if (!res.ok) throw new Error(String(res.status));
        const data = await res.json();
        if (cancelled) return;
        const ready = data.asr_ready && data.llm_ready;
        const mock =
          String(data.asr_provider).includes("mock") || String(data.llm_provider) === "offline";
        setHealth({
          dot: ready ? (mock ? "health-dot--degraded" : "health-dot--ok") : "health-dot--degraded",
          text: mock ? "Chế độ demo" : ready ? "Hệ thống sẵn sàng" : "Một phần dịch vụ chưa sẵn sàng",
          title: mock ? "Chế độ demo" : ready ? "Hệ thống sẵn sàng" : "Một phần dịch vụ chưa sẵn sàng",
        });
      } catch {
        if (cancelled) return;
        setHealth({
          dot: "health-dot--down",
          text: "Mất kết nối máy chủ",
          title: "Không gọi được /api/v1/health",
        });
      }
    })();

    return () => {
      cancelled = true;
      stopTimer();
      stepTimersRef.current.forEach(clearTimeout);
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Revoke stale preview URLs.
  useEffect(() => () => { if (previewUrl) URL.revokeObjectURL(previewUrl); }, [previewUrl]);

  const saveTeamCode = (value: string) => {
    setTeamCode(value);
    try {
      if (value.trim()) localStorage.setItem(TEAM_CODE_KEY, value.trim());
      else localStorage.removeItem(TEAM_CODE_KEY);
    } catch {
      /* private mode */
    }
  };

  // ---------- File selection ----------
  const selectFile = useCallback(async (f: File | null, opts?: { preview?: string; durationSec?: number }) => {
    setFileError(null);
    setLongAudio(false);
    if (previewUrl && !opts?.preview) {
      setPreviewUrl(null);
    }
    if (!f) {
      setFile(null);
      if (audioInputRef.current) audioInputRef.current.value = "";
      return;
    }
    const suffix = ("." + (f.name.split(".").pop() ?? "")).toLowerCase();
    if (!ALLOWED_SUFFIXES.includes(suffix) && !f.type.startsWith("audio/")) {
      setFile(null);
      setFileError(`Định dạng không được hỗ trợ. Hãy dùng tệp âm thanh (${ALLOWED_SUFFIXES.join(", ")}).`);
      return;
    }
    if (f.size > MAX_UPLOAD_BYTES) {
      setFile(null);
      setFileError(`Tệp ${fmtBytes(f.size)} vượt quá giới hạn 25 MB. Hãy chọn bản ghi ngắn hơn hoặc nén lại.`);
      return;
    }
    setFile(f);
    if (opts?.preview) setPreviewUrl(opts.preview);

    // Long-audio heads-up: free-tier CPU is slow, the request stays open.
    let duration = opts?.durationSec ?? null;
    if (duration == null) {
      const url = URL.createObjectURL(f);
      duration = await probeDuration(url);
      URL.revokeObjectURL(url);
    }
    if (duration != null && duration > LONG_AUDIO_SECONDS) setLongAudio(true);
  }, [previewUrl]);

  // ---------- Recording ----------
  const stopTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
  };

  const startTimer = () => {
    startedAtRef.current = performance.now();
    timerRef.current = setInterval(() => {
      setElapsed(accumRef.current + (performance.now() - startedAtRef.current) / 1000);
    }, 500);
  };

  const startRecording = async () => {
    setRecError(null);
    setFileError(null);
    void selectFile(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
      });
      const mime = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"].find(
        (t) => MediaRecorder.isTypeSupported(t)
      );
      const rec = new MediaRecorder(stream, {
        ...(mime ? { mimeType: mime } : {}),
        audioBitsPerSecond: 48_000, // honored where supported; iOS picks its own
      });
      streamRef.current = stream;
      recorderRef.current = rec;
      chunksRef.current = [];
      accumRef.current = 0;
      setElapsed(0);

      rec.ondataavailable = (e) => { if (e.data.size) chunksRef.current.push(e.data); };
      rec.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        const type = rec.mimeType || mime || "audio/webm";
        const ext = recordingExt(type);
        const blob = new Blob(chunksRef.current, { type });
        // Name the Blob by real mimeType so the server suffix check passes.
        const f = new File([blob], `recording.${ext}`, { type });
        const url = URL.createObjectURL(blob);
        const seconds = accumRef.current;
        setRecState("idle");
        void selectFile(f, { preview: url, durationSec: seconds });
      };

      rec.start(1000); // timeslice: keep chunks flowing even if the tab hiccups
      setRecState("recording");
      startTimer();
    } catch {
      setRecError("Không truy cập được micro. Hãy cấp quyền micro cho trình duyệt, hoặc tải tệp lên bên dưới.");
    }
  };

  const pauseRecording = () => {
    const rec = recorderRef.current;
    if (!rec || rec.state !== "recording") return;
    rec.pause();
    accumRef.current += (performance.now() - startedAtRef.current) / 1000;
    stopTimer();
    setRecState("paused");
  };

  const resumeRecording = () => {
    const rec = recorderRef.current;
    if (!rec || rec.state !== "paused") return;
    rec.resume();
    startTimer();
    setRecState("recording");
  };

  const stopRecording = () => {
    const rec = recorderRef.current;
    if (!rec || rec.state === "inactive") return;
    if (rec.state === "recording") {
      accumRef.current += (performance.now() - startedAtRef.current) / 1000;
    }
    stopTimer();
    rec.stop();
  };

  const reRecord = () => {
    void selectFile(null);
    setPreviewUrl(null);
    void startRecording();
  };

  // ---------- Progress stepper (cosmetic) ----------
  const startStepper = () => {
    stepTimersRef.current.forEach(clearTimeout);
    setStepsDone(false);
    setActiveStep(0);
    stepTimersRef.current = [
      setTimeout(() => setActiveStep(1), 1400),
      setTimeout(() => setActiveStep(2), 3200),
    ];
  };

  const finishStepper = () => {
    stepTimersRef.current.forEach(clearTimeout);
    setStepsDone(true);
  };

  // ---------- Submit ----------
  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    const body = new FormData();
    body.append("audio", file);
    const ctx = context.trim();
    if (ctx) body.append("encounter_context", ctx);

    const headers: Record<string, string> = {};
    if (teamCode.trim()) headers["X-Team-Code"] = teamCode.trim();

    setView("loading");
    startStepper();

    try {
      const res = await fetch(API.soap, { method: "POST", body, headers });
      const raw = await res.text();
      let data: unknown = null;
      try { data = raw ? JSON.parse(raw) : null; } catch { /* non-JSON error body */ }

      if (!res.ok) {
        const detail = (data as { detail?: unknown } | null)?.detail;
        if (res.status === 429) {
          const d = detail as { message?: string; retry_after_seconds?: number } | undefined;
          const msg = d?.message ?? "Bạn đã đạt giới hạn dùng thử của demo.";
          const wait = d?.retry_after_seconds;
          throw new Error(wait ? `${msg} Thử lại sau khoảng ${fmtWait(wait)}.` : msg);
        }
        const msg =
          typeof detail === "string"
            ? detail
            : (detail as { message?: string } | undefined)?.message ?? raw ?? `HTTP ${res.status}`;
        throw new Error(msg);
      }

      finishStepper();
      setResult(data as SoapResponse);
      setCopyLabel("Sao chép");
      setView("result");
      requestAnimationFrame(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
    } catch (err) {
      setErrorMsg(err instanceof Error && err.message ? err.message : "Lỗi không xác định.");
      setView("error");
    }
  };

  const onNew = () => {
    void selectFile(null);
    setPreviewUrl(null);
    setContext("");
    setResult(null);
    setView("idle");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // ---------- Copy ----------
  const onCopy = async () => {
    const s = result?.soap;
    if (!s) return;
    const md = (v?: string) => (v || "-").replace(/\*\*/g, "");
    const text = [
      "BỆNH ÁN SOAP (bản nháp, cần bác sĩ kiểm tra)",
      "",
      `S - Chủ quan:\n${md(s.subjective)}`,
      "",
      `O - Khách quan:\n${md(s.objective)}`,
      "",
      `A - Đánh giá:\n${md(s.assessment)}`,
      "",
      `P - Kế hoạch:\n${md(s.plan)}`,
    ].join("\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopyLabel("Đã sao chép ✓");
      setTimeout(() => setCopyLabel("Sao chép"), 1600);
    } catch {
      setCopyLabel("Không sao chép được");
    }
  };

  // ---------- Derived ----------
  const missing = (result?.soap?.missing_information ?? []).filter(Boolean);
  const meta = result?.metadata ?? {};
  const metaBits: string[] = [];
  if (meta.latency_ms != null) metaBits.push(`Xử lý trong ${(meta.latency_ms / 1000).toFixed(1)}s`);
  const recActive = recState === "recording" || recState === "paused";

  return (
    <div className="page">
      {/* Top bar */}
      <header className="topbar">
        <a className="brand brand-link" href="/" aria-label="CarePath, về trang chủ">
          <span className="brand-mark">
            <img src="/assets/carepath-mark.png" alt="CarePath" width={79} height={38} />
          </span>
          <div className="brand-text">
            <span className="brand-name"><span className="nm-care">Care</span><span className="nm-path">Path</span></span>
            <span className="brand-sub">Trợ lý ghi chép y khoa AI</span>
          </div>
        </a>
        <div className="topbar-right">
          <a className="back-home" href="/">
            <svg viewBox="0 0 24 24" width={16} height={16} fill="none" stroke="currentColor" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M19 12H5" /><path d="m12 19-7-7 7-7" />
            </svg>
            <span>Trang chủ</span>
          </a>
          <div className="health" title={health.title}>
            <span className={`health-dot ${health.dot}`}></span>
            <span className="health-text">{health.text}</span>
          </div>
        </div>
      </header>

      <main>
        {/* Intro */}
        <section className="hero reveal reveal-1">
          <span className="eyebrow">Trợ lý y khoa · AI Scribe</span>
          <h1>Từ bản ghi âm buổi khám đến <span className="hl">bệnh án SOAP</span></h1>
          <p>Ghi âm ngay trên điện thoại hoặc tải lên bản ghi cuộc trò chuyện giữa bác sĩ và bệnh nhân. CarePath sẽ phiên âm, hiệu chỉnh thuật ngữ y khoa Việt-Anh và soạn bản nháp bệnh án SOAP để bác sĩ kiểm tra.</p>
        </section>

        {/* Upload / record card */}
        {view === "idle" && (
          <section className="card upload-card reveal reveal-2">
            <form onSubmit={onSubmit}>
              {/* ---- In-browser recording (feature-detected) ---- */}
              {recSupported && (
                <div className="recorder">
                  {!recActive && !previewUrl && (
                    <button type="button" className="rec-btn" onClick={startRecording} aria-label="Bắt đầu ghi âm">
                      <svg viewBox="0 0 24 24" width={30} height={30} fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <rect x="9" y="2" width="6" height="12" rx="3" /><path d="M5 10a7 7 0 0 0 14 0" /><line x1="12" y1="19" x2="12" y2="22" />
                      </svg>
                    </button>
                  )}
                  {!recActive && !previewUrl && (
                    <div className="rec-copy">
                      <span className="rec-title">Ghi âm buổi khám</span>
                      <span className="rec-hint">Bấm nút micro để ghi trực tiếp trên máy này.</span>
                    </div>
                  )}

                  {recActive && (
                    <div className="rec-live" role="status">
                      <span className={"rec-dot" + (recState === "paused" ? " rec-dot--paused" : "")} aria-hidden="true"></span>
                      <span className="rec-time">{fmtClock(elapsed)}</span>
                      <span className="rec-state">{recState === "paused" ? "Đang tạm dừng" : "Đang ghi âm…"}</span>
                      <div className="rec-controls">
                        {recState === "recording" ? (
                          <button type="button" className="btn btn-ghost btn-sm" onClick={pauseRecording}>Tạm dừng</button>
                        ) : (
                          <button type="button" className="btn btn-ghost btn-sm" onClick={resumeRecording}>Tiếp tục</button>
                        )}
                        <button type="button" className="btn btn-sm rec-stop" onClick={stopRecording}>Dừng &amp; dùng bản ghi</button>
                      </div>
                      {elapsed > LONG_AUDIO_SECONDS && (
                        <p className="rec-warn">Bản ghi đã dài hơn 20 phút — máy chủ demo xử lý có thể mất vài phút.</p>
                      )}
                    </div>
                  )}

                  {previewUrl && !recActive && (
                    <div className="rec-preview">
                      <audio controls src={previewUrl} className="rec-audio"></audio>
                      <button type="button" className="btn btn-ghost btn-sm" onClick={reRecord}>Ghi lại</button>
                    </div>
                  )}

                  {recError && <p className="upload-error" role="alert">{recError}</p>}
                </div>
              )}

              {recSupported && !recActive && (
                <div className="upload-divider" aria-hidden="true"><span>hoặc tải tệp lên</span></div>
              )}

              {/* ---- File upload (kept for desktop; on phones the picker also
                       offers voice memos / files) ---- */}
              {!recActive && (
                <label
                  className={"dropzone" + (isDrag ? " is-drag" : "")}
                  htmlFor="audioInput"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); audioInputRef.current?.click(); }
                  }}
                  onDragEnter={(e) => { e.preventDefault(); setIsDrag(true); }}
                  onDragOver={(e) => { e.preventDefault(); setIsDrag(true); }}
                  onDragLeave={(e) => { e.preventDefault(); setIsDrag(false); }}
                  onDrop={(e) => {
                    e.preventDefault();
                    setIsDrag(false);
                    const f = e.dataTransfer?.files?.[0];
                    if (f) void selectFile(f);
                  }}
                >
                  <input
                    id="audioInput"
                    ref={audioInputRef}
                    type="file"
                    accept="audio/*,.wav,.mp3,.m4a,.aac,.flac,.ogg,.oga,.opus,.webm"
                    hidden
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) void selectFile(f);
                    }}
                  />
                  <span className="dropzone-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" width={34} height={34} fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 16V4" /><path d="m7 9 5-5 5 5" /><path d="M5 16v3a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-3" />
                    </svg>
                  </span>
                  <span className="dropzone-title">Kéo thả tệp âm thanh vào đây, hoặc bấm để chọn</span>
                  <span className="dropzone-hint">Hỗ trợ WAV, MP3, M4A, OGG, FLAC · tối đa 25 MB</span>
                </label>
              )}

              {fileError && <p className="upload-error" role="alert">{fileError}</p>}

              {file && !recActive && (
                <div className="file-chip">
                  <span className="file-chip-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" width={18} height={18} fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
                      <path d="M9 18V5l12-2v13" /><circle cx="6" cy="18" r="3" /><circle cx="18" cy="16" r="3" />
                    </svg>
                  </span>
                  <span className="file-chip-name">{file.name}</span>
                  <span className="file-chip-size">{fmtBytes(file.size)}</span>
                  <button type="button" className="file-chip-clear" aria-label="Bỏ tệp" onClick={() => { void selectFile(null); setPreviewUrl(null); }}>&times;</button>
                </div>
              )}

              {longAudio && !recActive && (
                <p className="upload-warn">Bản ghi dài hơn 20 phút — máy chủ demo xử lý có thể mất vài phút, hãy giữ trang mở.</p>
              )}

              {!recActive && (
                <>
                  <div className="field">
                    <label htmlFor="contextInput">Bối cảnh buổi khám <span className="muted">(tùy chọn)</span></label>
                    <input
                      id="contextInput"
                      type="text"
                      placeholder="VD: Phòng khám nội tổng quát, bệnh nhân nam 54 tuổi"
                      value={context}
                      onChange={(e) => setContext(e.target.value)}
                    />
                  </div>

                  <details className="teamcode">
                    <summary>Mã nội bộ <span className="muted">(dành cho đội ngũ CarePath)</span></summary>
                    <div className="field teamcode-field">
                      <input
                        type="text"
                        placeholder="Nhập mã được cấp"
                        autoComplete="off"
                        spellCheck={false}
                        value={teamCode}
                        onChange={(e) => saveTeamCode(e.target.value)}
                        aria-label="Mã nội bộ"
                      />
                      {teamCode.trim() && (
                        <p className="teamcode-hint">Mã được lưu trên máy này và gửi kèm mỗi yêu cầu — không giới hạn lượt chạy.</p>
                      )}
                    </div>
                  </details>

                  <button type="submit" className="btn btn-primary" disabled={!file}>
                    <span className="btn-label">Tạo bệnh án SOAP</span>
                    <span className="btn-icon" aria-hidden="true">→</span>
                  </button>
                </>
              )}
            </form>
          </section>
        )}

        {/* Progress */}
        {view === "loading" && (
          <section className="card progress-card">
            <div className="stepper">
              {STEP_LABELS.map((label, i) => (
                <Fragment key={label}>
                  {i > 0 && <span className="step-line"></span>}
                  <div className={"step" + (stepsDone || i < activeStep ? " is-done" : i === activeStep ? " is-active" : "")}>
                    <span className="step-dot"></span>
                    <span className="step-label">{label}</span>
                  </div>
                </Fragment>
              ))}
            </div>
            <p className="progress-note">
              {longAudio
                ? "Bản ghi dài — quá trình xử lý có thể mất vài phút. Vui lòng giữ trang mở."
                : "Đang xử lý… quá trình này có thể mất vài giây tùy độ dài bản ghi."}
            </p>
          </section>
        )}

        {/* Error */}
        {view === "error" && (
          <section className="card error-card">
            <strong>Đã xảy ra lỗi.</strong>
            <span>{errorMsg}</span>
            <button type="button" className="btn btn-ghost" onClick={() => setView("idle")}>Thử lại</button>
          </section>
        )}

        {/* Result */}
        {view === "result" && result && (
          <section className="result in" ref={resultRef}>
            <div className="result-head">
              <h2>Bệnh án SOAP <span className="muted">(bản nháp)</span></h2>
              <div className="result-actions">
                <button type="button" className="btn btn-ghost btn-sm" onClick={onCopy}>{copyLabel}</button>
                <button type="button" className="btn btn-ghost btn-sm" onClick={onNew}>Tạo bệnh án mới</button>
              </div>
            </div>

            {result.soap?.review_required !== false && (
              <div className="banner banner-review">
                <svg viewBox="0 0 24 24" width={18} height={18} fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <span>Bản nháp do AI tạo, <strong>cần bác sĩ kiểm tra</strong> trước khi đưa vào hồ sơ bệnh án.</span>
              </div>
            )}

            <div className="card soap-card">
              <div className="soap-inner">
                {SOAP_SECTIONS.map((s) => (
                  <article key={s.key} className="soap-section" style={accent(s.ac)}>
                    <div className="soap-badge">{s.key}</div>
                    <div className="soap-body">
                      <h3>{s.title} <span className="muted">/ {s.en}</span></h3>
                      <div className="soap-text"><RichText text={result.soap?.[s.field]} /></div>
                    </div>
                  </article>
                ))}
              </div>
            </div>

            {missing.length > 0 && (
              <div className="card missing-card">
                <h3>Thông tin còn thiếu</h3>
                <ul className="chips">
                  {missing.map((m) => <li key={m}>{m}</li>)}
                </ul>
              </div>
            )}

            <p className="meta-line">{metaBits.length ? `${metaBits.join(" · ")} · CarePath` : "CarePath"}</p>
          </section>
        )}
      </main>

      <footer className="footer">
        <span>CarePath · Bản demo cho nhân viên y tế Việt Nam</span>
        <span className="footer-disclaimer">Không dùng cho chẩn đoán lâm sàng chính thức.</span>
      </footer>
    </div>
  );
}
