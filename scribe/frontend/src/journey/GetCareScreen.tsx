import { useCallback, useMemo, useState, type FormEvent } from "react";
import logoUrl from "../assets/carepath.svg";
import { JOURNEY } from "../content/journey";
import {
  addDocuments,
  patchEpisode,
  type EpisodeDocument,
  type VisitBrief,
} from "../episode/episode";
import { PatientSheet } from "../paperwork/PaperworkScreen";
import DocumentReview from "../visit/DocumentReview";
import { riskLabel } from "../visit/riskLabels";
import { isGated, spokenText, type VisitTurn } from "../visit/types";
import { GateCard, TurnCard } from "../visit/VisitScreen";
import { matchProviders, matchReason, storable, type CuratedProvider } from "./providers";
import {
  confirmScripted,
  SCRIPTED_DOCUMENT,
  SCRIPTED_FOLLOW_UP,
  SCRIPTED_VISIT,
} from "./scripted";
import "./journey.css";

/**
 * The care journey: need → clinic → brief → visit → paperwork.
 *
 * This route makes no network request at all. Not as a fallback and not as a
 * demo mode bolted onto a live path — every stage is genuinely client-side, so
 * the pitch completes on a venue network that does not exist. The two stages
 * that mirror live tools link straight to them.
 *
 * What is NOT re-implemented here: the gate. `GateCard`, `TurnCard`,
 * `DocumentReview` and `PatientSheet` are the components the clinic uses, and
 * `isGated` from visit/types.ts is the predicate the server's own statuses feed.
 * A line is withheld on this screen for exactly the reason it is withheld in a
 * real consultation.
 */

type Stage = "intake" | "providers" | "brief" | "visit" | "paperwork" | "done";

interface Intake {
  location: string;
  language: string;
  careNeed: string;
  timing: string;
  insurance: boolean;
}

const EMPTY_INTAKE: Intake = {
  location: "Hanoi",
  language: "English",
  careNeed: "",
  timing: JOURNEY.intake.timingOptions[0],
  insurance: false,
};

const EMMA_INTAKE: Intake = {
  location: "Hanoi",
  language: "English",
  careNeed: "itchy red rash on both arms since yesterday",
  timing: "Today",
  insurance: true,
};

const EMMA_BRIEF: VisitBrief = {
  concern: "Itchy red rash on both arms",
  since: "Yesterday morning",
  history: "Nothing relevant. No previous skin problems.",
  medications: "None",
  allergies: "Sulfa drugs",
  questions: "Is this an allergy? Can I still swim? Should I stay out of the sun?",
  insurance: "Travel insurance — claim documents needed",
};

const EMMA_BRIEF_VI: Partial<VisitBrief> = {
  concern: "Nổi mẩn đỏ, ngứa ở hai cánh tay",
  since: "Từ sáng hôm qua",
  history: "Không có gì đáng kể. Chưa từng có vấn đề về da.",
  medications: "Không dùng thuốc gì",
  allergies: "Dị ứng thuốc nhóm sulfa",
  questions: "Có phải dị ứng không? Có bơi được không? Có cần tránh nắng không?",
  insurance: "Có bảo hiểm du lịch — cần giấy tờ để yêu cầu bồi thường",
};

const BRIEF_ORDER = [
  "concern",
  "since",
  "history",
  "medications",
  "allergies",
  "questions",
  "insurance",
] as const;

/** A brief built from what the patient typed, with no clinical interpretation. */
function briefFrom(intake: Intake): VisitBrief {
  return {
    concern: intake.careNeed,
    since: "",
    history: "",
    medications: "",
    allergies: "",
    questions: "",
    insurance: intake.insurance ? "Yes — travel or health insurance" : "No",
  };
}

function Bar() {
  return (
    <nav className="p-nav" aria-label={JOURNEY.brand}>
      <a className="p-nav__brand" href="/">
        <img src={logoUrl} alt="" width={28} height={16} />
        <span>{JOURNEY.brand}</span>
      </a>
      <div className="p-nav__end">
        <a className="p-nav__back" href="/">
          {JOURNEY.navBack}
        </a>
      </div>
    </nav>
  );
}

function Steps({ current }: { current: number }) {
  return (
    <ol className="j-steps" aria-label="Care journey progress">
      {JOURNEY.steps.map((step, index) => (
        <li
          key={step}
          className={`j-steps__item${index === current ? " is-current" : ""}${
            index < current ? " is-done" : ""
          }`}
          aria-current={index === current ? "step" : undefined}
        >
          <span className="j-steps__ord">{String(index + 1).padStart(2, "0")}</span>
          <span className="j-steps__label">{step}</span>
        </li>
      ))}
    </ol>
  );
}

function Head({ label, title, lede }: { label: string; title: string; lede: string }) {
  return (
    <header className="p-reg j-head">
      <span className="p-reg__mark p-mark">{label}</span>
      <h1 className="p-reg__vi">{title}</h1>
      <p className="p-reg__en p-lede">{lede}</p>
    </header>
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

export default function GetCareScreen() {
  const [stage, setStage] = useState<Stage>("intake");
  const [intake, setIntake] = useState<Intake>(EMPTY_INTAKE);
  const [error, setError] = useState<string | null>(null);
  const [provider, setProvider] = useState<CuratedProvider | null>(null);
  const [brief, setBrief] = useState<VisitBrief>(briefFrom(EMPTY_INTAKE));
  const [briefVi, setBriefVi] = useState<Partial<VisitBrief>>({});
  const [editing, setEditing] = useState(false);
  const [visitTurns, setVisitTurns] = useState<VisitTurn[]>(SCRIPTED_VISIT);
  const [docTurns, setDocTurns] = useState<VisitTurn[]>(SCRIPTED_DOCUMENT);

  const providers = useMemo(() => matchProviders(intake.careNeed), [intake.careNeed]);

  const seedExample = useCallback(() => {
    setIntake(EMMA_INTAKE);
    setBrief(EMMA_BRIEF);
    setBriefVi(EMMA_BRIEF_VI);
    setError(null);
  }, []);

  const submitIntake = (event: FormEvent) => {
    event.preventDefault();
    if (!intake.careNeed.trim()) {
      setError(JOURNEY.intake.needRequired);
      return;
    }
    setError(null);
    // A brief the patient already edited (or seeded) is theirs; do not overwrite
    // it just because they came back and changed a field on the intake.
    setBrief((current) => (current.concern ? current : briefFrom(intake)));
    patchEpisode({
      location: intake.location,
      careNeed: intake.careNeed,
      timing: intake.timing,
      insurance: intake.insurance,
      locale: "en",
      status: "planning",
      source: "scripted",
    });
    setStage("providers");
  };

  const chooseProvider = (chosen: CuratedProvider) => {
    setProvider(chosen);
    patchEpisode({ provider: storable(chosen), status: "planning" });
    setStage("brief");
  };

  const acceptBrief = () => {
    patchEpisode({ visitBrief: brief, visitBriefVi: briefVi, status: "prepared" });
    setStage("visit");
  };

  const confirmVisitTurn = (turn: VisitTurn, edited?: string) =>
    setVisitTurns((current) => confirmScripted(current, turn.id, edited));

  const confirmDocTurn = (turn: VisitTurn, edited?: string) =>
    setDocTurns((current) => confirmScripted(current, turn.id, edited));

  const escalate = () => {
    patchEpisode({
      status: "escalated",
      escalation: {
        reason: JOURNEY.episode.escalate.reasons[0],
        requestedAt: new Date().toISOString(),
      },
    });
    window.location.href = "/my-carepath/";
  };

  const finishPaperwork = () => {
    const released = docTurns.filter((turn) => !isGated(turn));
    const lines: EpisodeDocument[] = released.map((turn) => ({
      id: turn.id,
      kind: "prescription",
      vi: turn.source_text,
      en: spokenText(turn),
      isMedication: turn.risk_spans.some((span) =>
        ["drug_name", "dose_number"].includes(span.kind),
      ),
      source: "scripted",
    }));
    addDocuments(lines);
    patchEpisode({ status: "post_visit", followUp: SCRIPTED_FOLLOW_UP });
    setStage("done");
  };

  const gatedVisit = visitTurns.filter(isGated);
  const heldDocs = docTurns.filter(isGated);
  const releasedDocs = docTurns.filter((turn) => !isGated(turn));

  return (
    <div className="landing journey">
      <Bar />
      <main className="p-wrap j-main">
        {stage !== "done" ? (
          <Steps current={["intake", "providers", "brief", "visit", "paperwork"].indexOf(stage)} />
        ) : null}

        {stage === "intake" ? (
          <>
            <Head
              label={JOURNEY.intake.label}
              title={JOURNEY.intake.title}
              lede={JOURNEY.intake.lede}
            />
            <p className="j-disclaim">{JOURNEY.intake.disclaimer}</p>

            <form className="j-form" onSubmit={submitIntake}>
              <label className="j-field">
                <span>{JOURNEY.intake.city}</span>
                <input
                  value={intake.location}
                  onChange={(e) => setIntake({ ...intake, location: e.target.value })}
                />
                <small>{JOURNEY.intake.cityHint}</small>
              </label>

              <label className="j-field">
                <span>{JOURNEY.intake.language}</span>
                <input
                  value={intake.language}
                  onChange={(e) => setIntake({ ...intake, language: e.target.value })}
                />
              </label>

              <label className="j-field j-field--wide">
                <span>{JOURNEY.intake.need}</span>
                <textarea
                  value={intake.careNeed}
                  rows={3}
                  placeholder={JOURNEY.intake.needPlaceholder}
                  onChange={(e) => setIntake({ ...intake, careNeed: e.target.value })}
                />
              </label>

              <fieldset className="j-field j-field--wide j-radios">
                <legend>{JOURNEY.intake.timing}</legend>
                {JOURNEY.intake.timingOptions.map((option) => (
                  <label key={option} className="j-radio">
                    <input
                      type="radio"
                      name="timing"
                      value={option}
                      checked={intake.timing === option}
                      onChange={() => setIntake({ ...intake, timing: option })}
                    />
                    <span>{option}</span>
                  </label>
                ))}
              </fieldset>

              <label className="j-field j-field--wide j-check">
                <input
                  type="checkbox"
                  checked={intake.insurance}
                  onChange={(e) => setIntake({ ...intake, insurance: e.target.checked })}
                />
                <span>
                  {JOURNEY.intake.insurance}
                  <small>{JOURNEY.intake.insuranceHint}</small>
                </span>
              </label>

              {error ? (
                <p className="j-error" role="alert">
                  {error}
                </p>
              ) : null}

              <div className="j-actions">
                <button type="submit" className="p-cta">
                  {JOURNEY.intake.submit}
                </button>
                <button type="button" className="p-cta p-cta--ghost" onClick={seedExample}>
                  {JOURNEY.intake.example}
                </button>
              </div>
              <p className="j-fine">{JOURNEY.intake.exampleNote}</p>
            </form>
          </>
        ) : null}

        {stage === "providers" ? (
          <>
            <Head {...JOURNEY.providers} />
            <p className="j-curated">{JOURNEY.providers.curated}</p>

            <ul className="p-list j-providers">
              {providers.map((item) => (
                <li className="p-reg p-reg--ruled" key={item.id}>
                  <span className="p-reg__mark p-mark">{item.district}</span>
                  <div className="p-reg__vi">
                    <h2>{item.name}</h2>
                    <p className="j-provider__focus">{item.focus}</p>
                    {matchReason(item, intake.careNeed) ? (
                      <p className="j-fine">{matchReason(item, intake.careNeed)}</p>
                    ) : null}
                  </div>
                  <div className="p-reg__en">
                    <dl className="j-provider__facts">
                      <dt>{JOURNEY.providers.hours}</dt>
                      <dd>{item.hours}</dd>
                      <dt>{JOURNEY.providers.languages}</dt>
                      <dd>{item.languages.join(", ")}</dd>
                    </dl>
                    <p className="j-fine">{item.note}</p>
                    <button type="button" className="p-cta" onClick={() => chooseProvider(item)}>
                      {JOURNEY.providers.choose}
                    </button>
                  </div>
                </li>
              ))}
            </ul>

            <button
              type="button"
              className="j-link p-indent"
              onClick={() => setStage("intake")}
            >
              {JOURNEY.providers.back}
            </button>
          </>
        ) : null}

        {stage === "brief" ? (
          <>
            <Head {...JOURNEY.brief} />
            {provider ? <p className="j-curated">{provider.name} · {provider.district}</p> : null}

            <ol className="p-list j-brief">
              {BRIEF_ORDER.map((key) => {
                const field = JOURNEY.brief.fields[key];
                const vi = briefVi[key];
                return (
                  <li className="p-reg p-reg--ruled" key={key}>
                    <span className="p-reg__mark p-mark">{field.en}</span>
                    <div className="p-reg__vi">
                      {editing ? (
                        <>
                          <label className="sr-only" htmlFor={`brief-${key}`}>
                            {field.en}
                          </label>
                          <textarea
                            id={`brief-${key}`}
                            rows={2}
                            value={brief[key]}
                            onChange={(e) =>
                              setBrief((current) => ({ ...current, [key]: e.target.value }))
                            }
                          />
                        </>
                      ) : (
                        <p className="j-brief__value">{brief[key] || JOURNEY.brief.empty}</p>
                      )}
                    </div>
                    <div className="p-reg__en">
                      <span className="j-brief__vi-label">{field.vi}</span>
                      {vi ? (
                        <p className="j-brief__value" lang="vi">
                          {vi}
                        </p>
                      ) : (
                        <p className="j-brief__pending">{JOURNEY.brief.untranslated}</p>
                      )}
                    </div>
                  </li>
                );
              })}
            </ol>

            <div className="j-actions p-indent">
              <button type="button" className="p-cta" onClick={acceptBrief}>
                {JOURNEY.brief.save}
              </button>
              <button
                type="button"
                className="p-cta p-cta--ghost"
                onClick={() => setEditing((value) => !value)}
              >
                {editing ? JOURNEY.brief.done : JOURNEY.brief.edit}
              </button>
            </div>
          </>
        ) : null}

        {stage === "visit" ? (
          <>
            <Head {...JOURNEY.visit} />
            <p className="j-curated">
              {JOURNEY.visit.scripted}{" "}
              <a href="/kham-song-ngu/">{JOURNEY.visit.live}</a>
            </p>

            <p className={gatedVisit.length > 0 ? "j-gatecount is-held" : "j-gatecount"} role="status">
              {gatedVisit.length > 0
                ? JOURNEY.visit.waiting(gatedVisit.length)
                : JOURNEY.visit.cleared}
            </p>

            {gatedVisit.map((turn) => (
              <GateCard
                key={turn.id}
                turn={turn}
                onConfirm={confirmVisitTurn}
                onEscalate={escalate}
                busy={false}
              />
            ))}

            <div className="visit-columns j-columns">
              {(["patient", "doctor"] as const).map((who) => {
                const isPatient = who === "patient";
                return (
                  <section className="visit-column" key={who}>
                    <h2 className="visit-column__title">
                      {isPatient ? JOURNEY.visit.patientColumn : JOURNEY.visit.clinicianColumn}
                    </h2>
                    <div className="visit-column__stream">
                      {visitTurns.map((turn) => (
                        <TurnCard
                          key={turn.id}
                          turn={turn}
                          side={isPatient ? "en" : "vi"}
                          maskedLabel={isPatient ? JOURNEY.visit.masked : undefined}
                          patientView={isPatient}
                        />
                      ))}
                    </div>
                  </section>
                );
              })}
            </div>

            <aside className="j-principle">
              <p className="j-principle__claim">{JOURNEY.visit.principle}</p>
              <p className="j-fine">{JOURNEY.visit.principleBody}</p>
            </aside>

            <div className="j-actions p-indent">
              <button
                type="button"
                className="p-cta"
                onClick={() => {
                  patchEpisode({ status: "in_visit" });
                  setStage("paperwork");
                }}
              >
                {JOURNEY.visit.next}
              </button>
            </div>
          </>
        ) : null}

        {stage === "paperwork" ? (
          <>
            <Head {...JOURNEY.paperwork} />
            <p className="j-curated">
              {JOURNEY.paperwork.scripted}{" "}
              <a href="/dich-giay-to/">{JOURNEY.paperwork.live}</a>
            </p>

            <DocumentReview
              turns={heldDocs}
              onConfirm={confirmDocTurn}
              busy={false}
              renderChips={(turn) => <Chips turn={turn} />}
            />

            <PatientSheet turns={releasedDocs} copy={JOURNEY.paperwork} />

            <div className="j-actions p-indent">
              <button type="button" className="p-cta" onClick={finishPaperwork}>
                {JOURNEY.paperwork.finish}
              </button>
            </div>
          </>
        ) : null}

        {stage === "done" ? (
          <>
            <Head {...JOURNEY.done} />
            <div className="j-actions p-indent">
              <a className="p-cta" href="/my-carepath/">
                {JOURNEY.done.cta}
              </a>
            </div>
          </>
        ) : null}
      </main>
    </div>
  );
}
