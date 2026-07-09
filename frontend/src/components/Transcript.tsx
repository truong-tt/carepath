import { useState } from "react";

import type { TranscriptTurn } from "../types";

type TranscriptProps = {
  turns: TranscriptTurn[];
  onFeedback?: (turnId: string, reason: string, comment: string) => Promise<void>;
};

export function Transcript({ turns, onFeedback }: TranscriptProps) {
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
    <section className="transcript" aria-label="Bilingual transcript">
      <div className="transcript-head">
        <h2>Transcript</h2>
        <span>{turns.length} turns</span>
      </div>
      {turns.length === 0 ? <p className="empty">No turns yet.</p> : null}
      {turns.map((turn) => {
        const blocked =
          turn.requires_confirmation || turn.status === "awaiting_confirm" || turn.status === "blocked";
        return (
          <article className="turn" key={turn.id}>
            <div>
              <p className="meta">
                {turn.seq}. {turn.speaker} · {turn.src_lang} to {turn.tgt_lang}
              </p>
              <p>{highlightText(turn.source_text, turn)}</p>
            </div>
            <div>
              <p className="meta">
                {turn.risk_tier} · {turn.status}
                {turn.low_confidence ? " · low confidence" : ""}
                {turn.requires_confirmation ? " · confirmation required" : ""}
              </p>
              <p>
                {blocked
                  ? "Blocked pending doctor confirmation."
                  : highlightText(turn.corrected_text || turn.translation, turn)}
              </p>
              {turn.risk_spans.length ? (
                <ul className="risk-list" aria-label="Risk spans">
                  {turn.risk_spans.map((span, index) => (
                    <li className={`risk-badge ${span.severity}`} key={`${span.kind}-${index}`}>
                      {span.severity}: {span.kind}
                    </li>
                  ))}
                </ul>
              ) : null}
              {onFeedback ? (
                <div className="feedback">
                  <button type="button" onClick={() => setOpenFeedback(turn.id)}>
                    Flag translation
                  </button>
                  {savedTurn === turn.id ? <span>Feedback saved.</span> : null}
                  {openFeedback === turn.id ? (
                    <form
                      onSubmit={(event) => {
                        event.preventDefault();
                        void submit(turn.id);
                      }}
                    >
                      <label>
                        Reason
                        <select value={reason} onChange={(event) => setReason(event.target.value)}>
                          <option value="wrong_term">Wrong term</option>
                          <option value="wrong_meaning">Wrong meaning</option>
                          <option value="missing">Missing content</option>
                          <option value="other">Other</option>
                        </select>
                      </label>
                      <label>
                        Comment
                        <input value={comment} onChange={(event) => setComment(event.target.value)} />
                      </label>
                      <button type="submit">Submit feedback</button>
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

function highlightText(text: string, turn: TranscriptTurn) {
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
      <mark className={`risk-mark ${span.severity}`} title={`${span.severity}: ${span.kind}`}>
        <span className="sr-only">{span.severity} risk: </span>
        {text.slice(start, end)}
      </mark>
      {text.slice(end)}
    </>
  );
}
