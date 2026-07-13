import { useState } from "react";

import { copy, type Language } from "../copy";
import type { TranscriptTurn } from "../types";

type TranscriptProps = {
  language?: Language;
  turns: TranscriptTurn[];
  onFeedback?: (turnId: string, reason: string, comment: string) => Promise<void>;
  onRepeat?: (turn: TranscriptTurn) => void;
  onType?: (turn: TranscriptTurn) => void;
};

export function Transcript({ language = "vi", turns, onFeedback, onRepeat, onType }: TranscriptProps) {
  const text = copy[language].workspace;
  const [openFeedback, setOpenFeedback] = useState<string | null>(null);
  const [reason, setReason] = useState("wrong_term");
  const [comment, setComment] = useState("");
  const [savedTurn, setSavedTurn] = useState<string | null>(null);

  async function submit(turnId: string) {
    if (!onFeedback) {
      return;
    }
    await onFeedback(turnId, reason, comment);
    setSavedTurn(turnId);
    setOpenFeedback(null);
    setComment("");
  }

  return (
    <section className="transcript" aria-label={text.transcript}>
      <div className="transcript-head">
        <h2>{text.transcript}</h2>
        <span>{turns.length} {text.turns}</span>
      </div>
      {turns.length === 0 ? <p className="empty">{text.noTurns}</p> : null}
      {turns.map((turn) => {
        const blocked =
          turn.requires_confirmation || turn.status === "awaiting_confirm" || turn.status === "blocked";
        return (
          <article className="turn" key={turn.id}>
            <div>
              <p className="meta">
                {turn.seq}. {turn.speaker === "doctor" ? text.doctor : text.patient} · {turn.src_lang === "vi" ? text.vietnamese : text.english} → {turn.tgt_lang === "vi" ? text.vietnamese : text.english}
              </p>
              <p lang={blocked ? language : turn.src_lang}>{blocked ? text.patientSafeMask : highlightText(turn.source_text, turn, language)}</p>
            </div>
            <div>
              <p className="meta">
                {riskText(text, turn.risk_tier)} · {statusText(text, turn.status)}
                {turn.low_confidence ? ` · ${text.lowConfidence}` : ""}
                {turn.requires_confirmation ? ` · ${text.confirmationRequiredLabel}` : ""}
              </p>
              <p lang={blocked ? language : turn.tgt_lang}>
                {blocked
                  ? text.blocked
                  : highlightText(turn.corrected_text || turn.translation, turn, language)}
              </p>
              {turn.low_confidence ? (
                <section className="low-confidence" role="alert">
                  <p>{text.lowConfidence}</p>
                  {onRepeat ? <button type="button" onClick={() => onRepeat(turn)}>{text.repeatTurn}</button> : null}
                  {onType ? <button type="button" onClick={() => onType(turn)}>{text.typeTurn}</button> : null}
                </section>
              ) : null}
              {!blocked && turn.risk_spans.length ? (
                <ul className="risk-list" aria-label={text.riskSpans}>
                  {turn.risk_spans.map((span, index) => (
                    <li className={`risk-badge ${span.severity}`} key={`${span.kind}-${index}`}>
                      {riskText(text, span.severity)}: {riskKindText(text, span.kind)}
                    </li>
                  ))}
                </ul>
              ) : null}
              {onFeedback ? (
                <div className="feedback">
                  <button type="button" onClick={() => setOpenFeedback(turn.id)}>
                    {text.feedback}
                  </button>
                  {savedTurn === turn.id ? <span>{text.feedbackSaved}</span> : null}
                  {openFeedback === turn.id ? (
                    <form
                      onSubmit={(event) => {
                        event.preventDefault();
                        void submit(turn.id);
                      }}
                    >
                      <label>
                        {text.reason}
                        <select value={reason} onChange={(event) => setReason(event.target.value)}>
                          <option value="wrong_term">{text.feedbackReason.wrong_term}</option>
                          <option value="wrong_meaning">{text.feedbackReason.wrong_meaning}</option>
                          <option value="missing">{text.feedbackReason.missing}</option>
                          <option value="other">{text.feedbackReason.other}</option>
                        </select>
                      </label>
                      <label>
                        {text.comment}
                        <input value={comment} onChange={(event) => setComment(event.target.value)} />
                      </label>
                      <button type="submit">{text.submitFeedback}</button>
                    </form>
                  ) : null}
                </div>
              ) : null}
            </div>
          </article>
        );
      })}
    </section>
  );
}

function fold(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLocaleLowerCase();
}

function highlightText(text: string, turn: TranscriptTurn, language: Language) {
  const span = turn.risk_spans.find((candidate) => fold(text).includes(fold(candidate.term)));
  if (!span) {
    return text;
  }
  const foldedText = fold(text);
  const foldedTerm = fold(span.term);
  const start = foldedText.indexOf(foldedTerm);
  const end = start + span.term.length;
  return (
    <>
      {text.slice(0, start)}
      <mark className={`risk-mark ${span.severity}`} title={`${riskText(copy[language].workspace, span.severity)}: ${riskKindText(copy[language].workspace, span.kind)}`}>
        <span className="sr-only">{riskText(copy[language].workspace, span.severity)}: </span>
        {text.slice(start, end)}
      </mark>
      {text.slice(end)}
    </>
  );
}

function riskText(text: (typeof copy)[Language]["workspace"], value: string) {
  return text.risk[value as keyof typeof text.risk] ?? text.risk.other;
}

function statusText(text: (typeof copy)[Language]["workspace"], value: string) {
  return text.status[value as keyof typeof text.status] ?? text.status.other;
}

function riskKindText(text: (typeof copy)[Language]["workspace"], value: string) {
  return text.riskKind[value as keyof typeof text.riskKind] ?? text.riskKind.other;
}
