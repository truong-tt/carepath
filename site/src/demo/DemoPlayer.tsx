import { FormEvent, useEffect, useMemo, useState } from "react";
import { copyFor } from "../content/strings";
import { getScenario, scenarios } from "./scenarios";
import { buildTranscript } from "./transcript";
import type { DemoTurn, Language, PlaybackState } from "./types";

const TURN_DELAY_MS = 4000;

interface DemoPlayerProps {
  language?: Language;
  scenarioId?: string;
  clinicName?: string;
  specialty?: string;
  onScenarioChange?: (scenarioId: string) => void;
  onClinicNameChange?: (clinicName: string) => void;
  onSpecialtyChange?: (specialty: string) => void;
  onTranscriptChange?: (transcript: string) => void;
}

function downloadText(filename: string, content: string) {
  const url = URL.createObjectURL(
    new Blob([content], { type: "text/plain;charset=utf-8" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function DemoPlayer({
  language = "vi",
  scenarioId: controlledScenarioId,
  clinicName = "Phòng khám Đa khoa An Bình",
  specialty = "Nội tổng quát",
  onScenarioChange,
  onClinicNameChange,
  onSpecialtyChange,
  onTranscriptChange,
}: DemoPlayerProps) {
  const labels = copyFor(language).demo;
  const [localScenarioId, setLocalScenarioId] = useState(scenarios[0].id);
  const scenarioId = controlledScenarioId ?? localScenarioId;
  const scenario = useMemo(() => getScenario(scenarioId), [scenarioId]);
  const [revealedCount, setRevealedCount] = useState(0);
  const [state, setState] = useState<PlaybackState>("idle");
  const [confirmedIds, setConfirmedIds] = useState<string[]>([]);
  const [corrections, setCorrections] = useState<Record<string, string>>({});
  const [editValue, setEditValue] = useState("");
  const [customInput, setCustomInput] = useState("");
  const [customTurns, setCustomTurns] = useState<DemoTurn[]>([]);

  const revealedTurns = scenario.turns.slice(0, revealedCount);
  const pendingTurn =
    state === "awaiting-confirmation"
      ? scenario.turns[revealedCount - 1]
      : undefined;

  function reset(nextScenarioId = scenarioId) {
    if (onScenarioChange) {
      onScenarioChange(nextScenarioId);
    } else {
      setLocalScenarioId(nextScenarioId);
    }
    setRevealedCount(0);
    setState("idle");
    setConfirmedIds([]);
    setCorrections({});
    setEditValue("");
    setCustomTurns([]);
  }

  function advance() {
    if (
      state === "awaiting-confirmation" ||
      state === "escalated" ||
      state === "complete"
    ) {
      return;
    }
    const turn = scenario.turns[revealedCount];
    if (!turn) {
      setState("complete");
      return;
    }

    const nextCount = revealedCount + 1;
    setRevealedCount(nextCount);
    if (turn.escalation) {
      setState("escalated");
    } else if (turn.readback) {
      setEditValue(turn.en);
      setState("awaiting-confirmation");
    } else if (nextCount === scenario.turns.length) {
      setState("complete");
    }
  }

  useEffect(() => {
    if (state !== "playing") return;
    const timer = window.setTimeout(advance, TURN_DELAY_MS);
    return () => window.clearTimeout(timer);
  });

  function confirmPending() {
    if (!pendingTurn) return;
    setCorrections((current) => ({
      ...current,
      [pendingTurn.id]: editValue.trim() || pendingTurn.en,
    }));
    setConfirmedIds((current) => [...current, pendingTurn.id]);
    setState(
      revealedCount === scenario.turns.length ? "complete" : "playing",
    );
  }

  function submitCustom(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = customInput.trim();
    if (!text) return;
    setCustomTurns((current) => [
      ...current,
      {
        id: `custom-${current.length + 1}`,
        speaker: "patient",
        sourceLanguage: "vi",
        vi: text,
        en: labels.customResponse,
        riskTier: "low",
        riskSpans: [],
      },
    ]);
    setCustomInput("");
  }

  const allTranscriptTurns = [...revealedTurns, ...customTurns];
  const transcriptText = buildTranscript(
    scenario,
    allTranscriptTurns,
    corrections,
    language,
  );

  useEffect(() => {
    onTranscriptChange?.(transcriptText);
  }, [onTranscriptChange, transcriptText]);

  const progress = [
    true,
    revealedCount > 0,
    confirmedIds.length > 0 || state === "escalated" || state === "complete",
    state === "complete",
  ];

  return (
    <section className="demo" aria-labelledby="demo-title">
      <header className="demo__header">
        <div>
          <p className="demo__brand">CarePath Translate</p>
          <h2 id="demo-title">{clinicName} — Demo</h2>
          <p className="demo__specialty">{specialty}</p>
          <p className="demo__disclosure">
            {labels.disclosure}
          </p>
        </div>
        <span className="demo__privacy">{labels.privacy}</span>
      </header>

      <div className="demo-customization">
        <label>
          {labels.clinic}
          <input
            value={clinicName}
            maxLength={120}
            onChange={(event) => onClinicNameChange?.(event.target.value)}
          />
        </label>
        <label>
          {labels.specialty}
          <input
            value={specialty}
            maxLength={100}
            onChange={(event) => onSpecialtyChange?.(event.target.value)}
          />
        </label>
      </div>

      <div className="scenario-picker" aria-label={labels.chooseScenario}>
        {scenarios.map((item) => (
          <button
            className={item.id === scenarioId ? "scenario is-selected" : "scenario"}
            key={item.id}
            onClick={() => reset(item.id)}
            type="button"
          >
            <strong>{item.title[language]}</strong>
            <span>{item.summary[language]}</span>
          </button>
        ))}
      </div>

      <ol className="progress-rail" aria-label={language === "vi" ? "Tiến độ bản mô phỏng" : "Simulation progress"}>
        {labels.progress.map(
          (label, index) => (
            <li className={progress[index] ? "is-complete" : ""} key={label}>
              <span
                aria-hidden="true"
                className={progress[index] ? "progress-check" : ""}
              >
                {progress[index] ? "" : index + 1}
              </span>
              {label}
            </li>
          ),
        )}
      </ol>

      <div className="demo__controls">
        {state !== "playing" ? (
          <button
            className="button button--primary"
            onClick={() => setState("playing")}
            type="button"
            disabled={
              state === "awaiting-confirmation" ||
              state === "escalated" ||
              state === "complete"
            }
          >
            {state === "idle" ? labels.start : labels.continue}
          </button>
        ) : (
          <button
            className="button button--secondary"
            onClick={() => setState("paused")}
            type="button"
          >
            {labels.pause}
          </button>
        )}
        <button
          className="button button--secondary"
          onClick={advance}
          type="button"
          disabled={
            state === "awaiting-confirmation" ||
            state === "escalated" ||
            state === "complete"
          }
        >
          {labels.next}
        </button>
        <button
          className="button button--text"
          onClick={() => reset()}
          type="button"
        >
          {labels.replay}
        </button>
      </div>

      <div className="transcript" aria-live="polite">
        {revealedTurns.length === 0 ? (
          <p className="transcript__empty">{labels.empty}</p>
        ) : (
          revealedTurns.map((turn) => {
            const blocked =
              (turn.id === pendingTurn?.id || turn.escalation) &&
              !confirmedIds.includes(turn.id);
            return (
              <article className={`turn turn--${turn.riskTier}`} key={turn.id}>
                <header>
                  <strong>
                    {turn.speaker === "doctor" ? labels.doctor : labels.patient}
                  </strong>
                  <span>{labels.tiers[turn.riskTier]}</span>
                </header>
                <div className="turn__columns">
                  <p lang="vi">{turn.vi}</p>
                  <p lang="en">
                    {blocked
                      ? labels.blocked
                      : corrections[turn.id] ?? turn.en}
                  </p>
                </div>
                {turn.riskSpans.length > 0 && (
                  <ul className="risk-list" aria-label={labels.riskDetails}>
                    {turn.riskSpans.map((span, index) => (
                      <li key={`${span.kind}-${index}`}>{span.kind}: {span.vi}</li>
                    ))}
                  </ul>
                )}
              </article>
            );
          })
        )}
        {customTurns.map((turn) => (
          <article className="turn turn--custom" key={turn.id}>
            <header>
              <strong>{labels.customTitle}</strong>
              <span>{labels.simulation}</span>
            </header>
            <div className="turn__columns">
              <p>{turn.vi}</p>
              <p>{turn.en}</p>
            </div>
          </article>
        ))}
      </div>

      {pendingTurn?.readback && (
        <section className="readback" aria-labelledby="readback-title">
          <p className="readback__flag">{labels.blockedFlag}</p>
          <h3 id="readback-title">{labels.readbackTitle}</h3>
          <table>
            <thead>
              <tr>
                <th>{labels.entityType}</th>
                <th>{labels.source}</th>
                <th>{labels.translation}</th>
              </tr>
            </thead>
            <tbody>
              {pendingTurn.readback.entities.map((entity) => (
                <tr key={`${entity.kind}-${entity.sourceText}`}>
                  <td>{labels.entityKinds[entity.kind] ?? entity.kind}</td>
                  <td>{entity.sourceText}</td>
                  <td>{entity.translatedText}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <label>
            {labels.editTranslation}
            <textarea
              value={editValue}
              onChange={(event) => setEditValue(event.target.value)}
            />
          </label>
          <div className="readback__actions">
            <button
              className="button button--primary"
              onClick={confirmPending}
              type="button"
            >
              {labels.confirm}
            </button>
            <button
              className="button button--danger"
              onClick={() => setState("escalated")}
              type="button"
            >
              {labels.interpreter}
            </button>
          </div>
        </section>
      )}

      {state === "escalated" && (
        <section className="escalation" role="alert">
          <p>{labels.escalationStopped}</p>
          <h3>{labels.escalationTitle}</h3>
          <p>{labels.escalationBody}</p>
          <button
            className="button button--primary"
            onClick={() => setState("complete")}
            type="button"
          >
            {labels.escalationConfirm}
          </button>
        </section>
      )}

      <form className="custom-input" onSubmit={submitCustom}>
        <label htmlFor="custom-line">{labels.customLabel}</label>
        <div>
          <input
            id="custom-line"
            value={customInput}
            onChange={(event) => setCustomInput(event.target.value)}
            placeholder={labels.customPlaceholder}
          />
          <button className="button button--secondary" type="submit">
            {labels.customAdd}
          </button>
        </div>
        <small>{labels.customNote}</small>
      </form>

      {state === "complete" && (
        <button
          className="button button--download"
          onClick={() =>
            downloadText(
              `carepath-translate-${scenario.id}.txt`,
              transcriptText,
            )
          }
          type="button"
        >
          {labels.download}
        </button>
      )}
    </section>
  );
}
