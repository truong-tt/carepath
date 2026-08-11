import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import DocumentCapture from "./DocumentCapture";
import DocumentReview from "./DocumentReview";
import {
  AlertIcon,
  ClipboardIcon,
  DocumentIcon,
  DoseIcon,
  DropIcon,
  GaugeIcon,
  NoIcon,
  PillIcon,
  PinIcon,
  RepeatIcon,
  SidesIcon,
  SpeechIcon,
} from "./icons";
import { riskLabel, SEVERITY_LABELS, type RiskIcon, type RiskSeverity } from "./riskLabels";
import { cancelSpeech, listenOnce, speak, speechSupported, type SpeechSession } from "./speech";
import {
  canSpeakTurn,
  isGated,
  spokenText,
  type PatientContext,
  type VisitNote,
  type VisitTurn,
} from "./types";
import {
  confirmTurn,
  escalateVisit,
  finishVisit,
  startVisit,
  useVisitSocket,
} from "./useVisitSocket";
import VisitReview from "./VisitReview";
import "./visit.css";

// The gate card said "Bệnh nhân nói" for every turn, so a dose the doctor had
// just spoken was attributed back to the patient — and a prescription line to
// nobody. Doses come from the doctor, so this was wrong on the common case.
const GATE_SOURCE_LABELS: Record<string, string> = {
  doctor: "Bác sĩ nói",
  patient: "Bệnh nhân nói",
  document: "Giấy tờ ghi",
};

const DOCTOR = { speaker: "doctor", lang: "vi" } as const;
const PATIENT = { speaker: "patient", lang: "en" } as const;

function confidencePercent(turn: VisitTurn): number {
  return Math.round(Math.min(turn.asr_confidence, turn.mt_confidence) * 100);
}

const GLYPHS = {
  alert: AlertIcon,
  pill: PillIcon,
  dose: DoseIcon,
  repeat: RepeatIcon,
  route: DropIcon,
  sides: SidesIcon,
  pin: PinIcon,
  clipboard: ClipboardIcon,
  no: NoIcon,
  speech: SpeechIcon,
  gauge: GaugeIcon,
} as const;

function RiskGlyph({ name }: { name: RiskIcon }) {
  const Glyph = GLYPHS[name];
  return <Glyph className="visit-glyph" />;
}

function EntityChips({ turn }: { turn: VisitTurn }) {
  // Risk spans are computed against the machine translation and are not
  // recomputed when the clinician rewrites it. Showing them on a corrected turn
  // would contradict the text right above -- e.g. a "15 mg" chip under a
  // translation the clinician just changed to 500 mg.
  if (turn.status === "corrected") return null;
  const seen = new Set<string>();
  const entities = turn.risk_spans.filter((span) => {
    if (riskLabel(span.kind).group !== "entity" || seen.has(span.kind)) return false;
    seen.add(span.kind);
    return true;
  });
  if (entities.length === 0) return null;
  return (
    <ul className="visit-chips" aria-label="Thông tin y khoa được nhận diện">
      {entities.map((span) => {
        const label = riskLabel(span.kind);
        return (
          <li key={span.kind} className="visit-chip">
            <RiskGlyph name={label.icon} />
            <span className="visit-chip__term">{span.term}</span>
            <span className="visit-chip__kind">{label.vi}</span>
          </li>
        );
      })}
    </ul>
  );
}

function GateCard({
  turn,
  onConfirm,
  onEscalate,
  busy,
}: {
  turn: VisitTurn;
  onConfirm: (turn: VisitTurn, edited?: string) => void;
  onEscalate: () => void;
  busy: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(spokenText(turn));
  const checks = turn.risk_spans.filter((span) => riskLabel(span.kind).group === "check");

  return (
    <article className={`visit-gate visit-gate--${turn.risk_tier}`} aria-live="polite">
      <h3 className="visit-gate__title">
        <AlertIcon className="visit-glyph" /> Cần bác sĩ xác nhận
        <span className="visit-gate__tier">
          {SEVERITY_LABELS[turn.risk_tier as RiskSeverity]?.vi ?? turn.risk_tier}
        </span>
      </h3>
      <p className="visit-gate__note">
        Bệnh nhân chưa nghe và chưa nhìn thấy nội dung này.
      </p>

      <dl className="visit-gate__facts">
        <dt>{GATE_SOURCE_LABELS[turn.speaker] ?? "Nội dung gốc"}</dt>
        <dd>{turn.source_text}</dd>
        <dt>Bản dịch đề xuất</dt>
        <dd>
          {editing ? (
            <textarea
              className="visit-gate__edit"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              rows={3}
              aria-label="Sửa bản dịch"
            />
          ) : (
            spokenText(turn)
          )}
        </dd>
        {turn.readback?.back_translation ? (
          <>
            <dt>Dịch ngược để đối chiếu</dt>
            <dd>{turn.readback.back_translation}</dd>
          </>
        ) : null}
        <dt>Độ tin cậy nhận dạng</dt>
        <dd className={turn.low_confidence ? "visit-gate__low" : undefined}>
          {confidencePercent(turn)}%
          {turn.low_confidence ? " — thấp, cần kiểm tra kỹ" : ""}
        </dd>
      </dl>

      {checks.length > 0 ? (
        <ul className="visit-gate__checks">
          {checks.map((span) => (
            <li key={span.kind}>
              <RiskGlyph name={riskLabel(span.kind).icon} /> {riskLabel(span.kind).vi}
              {span.term ? <span className="visit-gate__term"> ({span.term})</span> : null}
            </li>
          ))}
        </ul>
      ) : null}

      <div className="visit-gate__actions">
        <button
          type="button"
          className="button button--primary"
          disabled={busy}
          onClick={() => onConfirm(turn, editing ? draft : undefined)}
        >
          {editing ? "Lưu bản sửa và đọc" : "Xác nhận và đọc cho bệnh nhân"}
        </button>
        {!editing ? (
          <button type="button" className="button button--secondary" onClick={() => setEditing(true)}>
            Sửa
          </button>
        ) : null}
        <button type="button" className="button button--secondary" onClick={onEscalate}>
          Cần phiên dịch viên
        </button>
      </div>
    </article>
  );
}

function TurnCard({ turn, side }: { turn: VisitTurn; side: "vi" | "en" }) {
  const showsSource = turn.src_lang.startsWith(side);
  const isDocument = turn.speaker === "document";
  // A column shows original speech when the turn was spoken in that language,
  // and the translation otherwise. Masking the translation side of a gated turn
  // is what "the patient never saw it" means concretely in the UI.
  if (isGated(turn) && !showsSource) {
    return (
      <article className="visit-turn visit-turn--masked">
        <p className="visit-turn__masked">Đang chờ bác sĩ xác nhận…</p>
      </article>
    );
  }
  const text = showsSource ? turn.source_text : spokenText(turn);
  return (
    <article className={`visit-turn visit-turn--${turn.speaker}`}>
      {isDocument ? (
        <p className="visit-turn__origin">
          <DocumentIcon className="visit-glyph" /> Từ giấy tờ
        </p>
      ) : null}
      <p className="visit-turn__text">{text}</p>
      {/* Documents are Vietnamese source in the Vietnamese column, so gating
          chips on "showing a translation" would hide them exactly where the
          extracted medicine and dose matter most. */}
      {!showsSource || isDocument ? <EntityChips turn={turn} /> : null}
      <p className="visit-turn__meta">
        {confidencePercent(turn)}%
        {turn.status === "corrected" ? " · bác sĩ đã sửa" : ""}
        {turn.status === "confirmed" ? " · bác sĩ đã xác nhận" : ""}
      </p>
    </article>
  );
}

// An accidental refresh mid-consultation must not lose the visit. The turns
// already live on the server, and reconnecting replays them, so remembering the
// id is all that is needed. sessionStorage, not localStorage: the visit should
// not outlive the browser tab.
const VISIT_KEY = "carepath.visitId";

export default function VisitScreen({ backHref = "/" }: { backHref?: string }) {
  const [visitId, setVisitId] = useState<string | null>(
    () => window.sessionStorage?.getItem(VISIT_KEY) ?? null,
  );
  const [context, setContext] = useState<PatientContext>({ age: "", sex: "", reason: "" });
  const [consented, setConsented] = useState(false);
  const [starting, setStarting] = useState(false);
  const [recording, setRecording] = useState<"doctor" | "patient" | null>(null);
  const [typed, setTyped] = useState({ doctor: "", patient: "" });
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<VisitNote | null>(null);
  const [finishing, setFinishing] = useState(false);
  const [escalated, setEscalated] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const sessionRef = useRef<SpeechSession | null>(null);

  const {
    turns,
    connection,
    error,
    pending,
    sendTurn,
    replaceTurn,
    addTurns,
    setOnTurn,
    clearError,
  } = useVisitSocket(visitId);

  // Speak only what the fail-closed rule allows, and only for new turns.
  useEffect(() => {
    setOnTurn((turn) => {
      if (canSpeakTurn(turn, escalated)) speak(spokenText(turn), turn.tgt_lang);
    });
    return () => setOnTurn(null);
  }, [setOnTurn, escalated]);

  const handleStart = async (event: FormEvent) => {
    event.preventDefault();
    setStarting(true);
    try {
      const id = await startVisit({ ...context });
      window.sessionStorage?.setItem(VISIT_KEY, id);
      setVisitId(id);
    } catch {
      setNotice("Không tạo được ca khám. Kiểm tra kết nối rồi thử lại.");
    } finally {
      setStarting(false);
    }
  };

  const startListening = useCallback(
    (who: "doctor" | "patient") => {
      const { lang, speaker } = who === "doctor" ? DOCTOR : PATIENT;
      setRecording(who);
      sessionRef.current = listenOnce(lang, {
        onResult: ({ transcript, confidence }) =>
          sendTurn(speaker, lang, transcript, confidence),
        onError: (code) =>
          setNotice(
            code === "not-allowed"
              ? "Trình duyệt chưa cho phép dùng micro. Hãy gõ nội dung bên dưới."
              : "Không nhận được giọng nói. Hãy thử lại hoặc gõ nội dung.",
          ),
        onEnd: () => {
          setRecording(null);
          sessionRef.current = null;
        },
      });
      if (!sessionRef.current) setRecording(null);
    },
    [sendTurn],
  );

  const stopListening = useCallback(() => sessionRef.current?.stop(), []);

  const submitTyped = (who: "doctor" | "patient") => (event: FormEvent) => {
    event.preventDefault();
    const text = typed[who].trim();
    if (!text) return;
    const { lang, speaker } = who === "doctor" ? DOCTOR : PATIENT;
    sendTurn(speaker, lang, text);
    setTyped((current) => ({ ...current, [who]: "" }));
  };

  const handleConfirm = async (turn: VisitTurn, edited?: string) => {
    setBusy(true);
    try {
      const updated = await confirmTurn(turn.id, edited);
      const patched: VisitTurn = { ...updated, requires_confirmation: false, low_confidence: false };
      replaceTurn(patched);
      if (canSpeakTurn(patched, escalated)) speak(spokenText(patched), patched.tgt_lang);
    } catch {
      setNotice("Không xác nhận được. Nội dung vẫn chưa gửi cho bệnh nhân.");
    } finally {
      setBusy(false);
    }
  };

  const handleEscalate = async () => {
    setEscalated(true);
    cancelSpeech();
    if (visitId) await escalateVisit(visitId);
    setNotice("Đã yêu cầu phiên dịch viên. Hệ thống ngừng đọc cho bệnh nhân.");
  };

  const handleFinish = async () => {
    if (!visitId) return;
    setFinishing(true);
    try {
      setNote(await finishVisit(visitId));
    } catch {
      setNotice("Chưa tạo được hồ sơ. Hãy thử lại.");
    } finally {
      setFinishing(false);
    }
  };

  const startNewVisit = () => {
    window.sessionStorage?.removeItem(VISIT_KEY);
    setVisitId(null);
    setNote(null);
    setEscalated(false);
    setNotice(null);
  };

  if (note) {
    return (
      <VisitReview
        note={note}
        onBack={() => setNote(null)}
        onNewVisit={startNewVisit}
        backHref={backHref}
      />
    );
  }

  if (!visitId) {
    return (
      <main className="visit visit--start">
        <a className="visit__back" href={backHref}>
          ← Trang chủ
        </a>
        <h1>Khám bệnh nhân nước ngoài</h1>
        <p className="visit__lead">
          Bác sĩ nói tiếng Việt, bệnh nhân nói tiếng Anh. CarePath dịch hai chiều trong lúc khám,
          và tạo bệnh án cùng bản tóm tắt cho bệnh nhân khi kết thúc.
        </p>
        <form className="visit-start" onSubmit={handleStart}>
          <label>
            Tuổi
            <input
              value={context.age}
              onChange={(e) => setContext({ ...context, age: e.target.value })}
              inputMode="numeric"
              placeholder="34"
            />
          </label>
          <label>
            Giới tính
            <input
              value={context.sex}
              onChange={(e) => setContext({ ...context, sex: e.target.value })}
              placeholder="nam"
            />
          </label>
          <label>
            Lý do khám
            <input
              value={context.reason}
              onChange={(e) => setContext({ ...context, reason: e.target.value })}
              placeholder="nổi mẩn da"
            />
          </label>
          <label className="visit-start__consent">
            <input
              type="checkbox"
              checked={consented}
              onChange={(e) => setConsented(e.target.checked)}
            />
            <span>
              Bệnh nhân đã được thông báo rằng CarePath là công cụ hỗ trợ dịch có thể sai, bác sĩ
              vẫn chịu trách nhiệm chuyên môn, và bệnh nhân có quyền yêu cầu phiên dịch viên.
            </span>
          </label>
          <button
            type="submit"
            className="button button--primary"
            disabled={!consented || starting}
          >
            {starting ? "Đang tạo…" : "Bắt đầu khám"}
          </button>
          <p className="visit-start__privacy">
            Micro chỉ bật khi bác sĩ bấm giữ. Giọng nói được nhận dạng ngay trên máy này và không
            được gửi đi hay lưu lại.
          </p>
        </form>
        {notice ? <p className="visit__notice">{notice}</p> : null}
      </main>
    );
  }

  const gatedTurns = turns.filter(isGated);
  const canFinish = turns.length > 0 && !finishing;

  return (
    <main className="visit">
      <header className="visit__bar">
        <h1>Khám bệnh nhân nước ngoài</h1>
        <p className="visit__status">
          <span className={`visit__dot visit__dot--${connection}`} aria-hidden="true" />
          {connection === "open" ? "Đang khám" : "Đang kết nối…"}
          {context.age || context.reason ? (
            <span className="visit__context">
              {" · "}
              {[context.sex, context.age && `${context.age} tuổi`, context.reason]
                .filter(Boolean)
                .join(" · ")}
            </span>
          ) : null}
        </p>
        <button
          type="button"
          className="button button--primary"
          onClick={handleFinish}
          disabled={!canFinish}
        >
          {finishing ? "Đang tạo hồ sơ…" : "Kết thúc và tạo hồ sơ"}
        </button>
      </header>

      {escalated ? (
        <p className="visit__escalated">
          Đã yêu cầu phiên dịch viên. Hệ thống không đọc cho bệnh nhân nữa.
        </p>
      ) : null}
      {notice ? (
        <p className="visit__notice" role="status">
          {notice}{" "}
          <button type="button" className="visit__dismiss" onClick={() => setNotice(null)}>
            Đóng
          </button>
        </p>
      ) : null}
      {error ? (
        <p className="visit__notice" role="alert">
          {error.message}{" "}
          <button type="button" className="visit__dismiss" onClick={clearError}>
            Đóng
          </button>
        </p>
      ) : null}

      <DocumentReview
        turns={gatedTurns.filter((turn) => turn.speaker === "document")}
        onConfirm={handleConfirm}
        busy={busy}
        renderChips={(turn) => <EntityChips turn={turn} />}
      />

      {gatedTurns
        .filter((turn) => turn.speaker !== "document")
        .map((turn) => (
          <GateCard
            key={turn.id}
            turn={turn}
            onConfirm={handleConfirm}
            onEscalate={handleEscalate}
            busy={busy}
          />
        ))}

      <div className="visit-columns">
        {(["patient", "doctor"] as const).map((who) => {
          const isPatient = who === "patient";
          const side = isPatient ? "en" : "vi";
          return (
            <section className="visit-column" key={who} aria-label={isPatient ? "Bệnh nhân" : "Bác sĩ"}>
              <h2 className="visit-column__title">
                {isPatient ? "Bệnh nhân · English" : "Bác sĩ · Tiếng Việt"}
              </h2>
              <div className="visit-column__stream">
                {turns.map((turn) => (
                  <TurnCard key={turn.id} turn={turn} side={side} />
                ))}
                {pending ? <p className="visit-turn__pending">Đang dịch…</p> : null}
              </div>
              <div className="visit-column__input">
                {speechSupported() ? (
                  <button
                    type="button"
                    className={`visit-mic${recording === who ? " visit-mic--on" : ""}`}
                    onMouseDown={() => startListening(who)}
                    onMouseUp={stopListening}
                    onTouchStart={() => startListening(who)}
                    onTouchEnd={stopListening}
                    onKeyDown={(e) => {
                      if (e.key === " " || e.key === "Enter") {
                        e.preventDefault();
                        if (recording !== who) startListening(who);
                      }
                    }}
                    onKeyUp={(e) => {
                      if (e.key === " " || e.key === "Enter") stopListening();
                    }}
                  >
                    {recording === who ? "Đang nghe…" : "Giữ để nói"}
                  </button>
                ) : null}
                <form onSubmit={submitTyped(who)} className="visit-typed">
                  <label className="sr-only" htmlFor={`typed-${who}`}>
                    {isPatient ? "Gõ tiếng Anh" : "Gõ tiếng Việt"}
                  </label>
                  <input
                    id={`typed-${who}`}
                    value={typed[who]}
                    onChange={(e) => setTyped({ ...typed, [who]: e.target.value })}
                    placeholder={isPatient ? "Type in English" : "Gõ tiếng Việt"}
                  />
                  <button type="submit" className="button button--secondary">
                    Gửi
                  </button>
                </form>
                {/* Paper is Vietnamese, so capture sits with the clinician. */}
                {!isPatient ? (
                  <DocumentCapture
                    visitId={visitId}
                    onTurns={addTurns}
                    disabled={connection !== "open"}
                  />
                ) : null}
              </div>
            </section>
          );
        })}
      </div>
    </main>
  );
}
