import { useState } from "react";
import logoUrl from "../assets/carepath.svg";
import { JOURNEY } from "../content/journey";
import {
  clearEpisode,
  loadEpisode,
  patchEpisode,
  type CareEpisode,
} from "../episode/episode";
import "./journey.css";

/**
 * One care episode, read back to the patient.
 *
 * Not a medical record and deliberately not on the way to becoming one. It
 * shows what the patient told a clinician, which clinic, what the clinician
 * confirmed, and what happens next — and it can delete all of it.
 *
 * Like `/get-care/`, this route makes no network request. The one exception it
 * could have made — telling the server about an escalation — is not taken:
 * there is no coordinator service behind it, so posting somewhere would imply a
 * human received it. The escalation is recorded locally and says so.
 */

const BRIEF_ORDER = [
  "concern",
  "since",
  "history",
  "medications",
  "allergies",
  "questions",
  "insurance",
] as const;

function Bar() {
  return (
    <nav className="p-nav" aria-label={JOURNEY.episode.label}>
      <a className="p-nav__brand" href="/">
        <img src={logoUrl} alt="" width={28} height={16} />
        <span>{JOURNEY.brand}</span>
      </a>
      <div className="p-nav__end">
        <a className="p-nav__back" href="/">
          {JOURNEY.episode.navBack}
        </a>
      </div>
    </nav>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="j-section">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function Escalation({
  episode,
  onRequest,
}: {
  episode: CareEpisode;
  onRequest: (reason: string) => void;
}) {
  const [reason, setReason] = useState<string>(JOURNEY.episode.escalate.reasons[0]);
  const copy = JOURNEY.episode.escalate;

  return (
    <section className="j-escalate" aria-labelledby="escalate-title">
      <h2 id="escalate-title">{copy.title}</h2>
      <p className="j-fine">{copy.body}</p>
      <p className="j-curated">{copy.prototype}</p>

      {episode.escalation ? (
        <>
          <dl className="j-facts">
            <dt>Requested</dt>
            <dd>{episode.escalation.reason}</dd>
          </dl>
          <p className="j-fine">{copy.requested}</p>
        </>
      ) : (
        <>
          <fieldset className="j-escalate__reasons">
            <legend className="sr-only">{copy.title}</legend>
            {copy.reasons.map((option) => (
              <label key={option} className="j-radio">
                <input
                  type="radio"
                  name="escalation"
                  value={option}
                  checked={reason === option}
                  onChange={() => setReason(option)}
                />
                <span>{option}</span>
              </label>
            ))}
          </fieldset>
          <button type="button" className="p-cta" onClick={() => onRequest(reason)}>
            {copy.submit}
          </button>
        </>
      )}

      <p className="j-emergency">{copy.emergency}</p>
    </section>
  );
}

export default function MyCarePathScreen() {
  const [episode, setEpisode] = useState<CareEpisode | null>(() => loadEpisode());
  const [cleared, setCleared] = useState(false);
  const copy = JOURNEY.episode;

  const requestPerson = (reason: string) => {
    setEpisode(
      patchEpisode({
        status: "escalated",
        escalation: { reason, requestedAt: new Date().toISOString() },
      }),
    );
  };

  const wipe = () => {
    clearEpisode();
    setEpisode(null);
    setCleared(true);
  };

  if (!episode) {
    return (
      <div className="landing journey">
        <Bar />
        <main className="p-wrap j-main">
          <header className="p-reg j-head">
            <span className="p-reg__mark p-mark">{copy.label}</span>
            <h1 className="p-reg__vi">{cleared ? copy.privacy.cleared : copy.emptyTitle}</h1>
            <p className="p-reg__en p-lede">{copy.emptyBody}</p>
          </header>
          <div className="j-actions p-indent">
            <a className="p-cta" href="/get-care/">
              {copy.emptyCta}
            </a>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="landing journey">
      <Bar />
      <main className="p-wrap j-main">
        <header className="p-reg j-head">
          <span className="p-reg__mark p-mark">{copy.label}</span>
          <h1 className="p-reg__vi">{copy.title}</h1>
          <p className="p-reg__en p-lede">{copy.lede}</p>
        </header>

        <p
          className={`j-status${episode.status === "escalated" ? " is-escalated" : ""}`}
          role="status"
        >
          {copy.status[episode.status]}
        </p>

        <Section title={copy.sections.overview}>
          <dl className="j-facts">
            <dt>What you asked for</dt>
            <dd>{episode.careNeed || "—"}</dd>
            <dt>Where</dt>
            <dd>{episode.location || "—"}</dd>
            <dt>When</dt>
            <dd>{episode.timing || "—"}</dd>
            <dt>Insurance</dt>
            <dd>{episode.insurance ? "Yes" : "No"}</dd>
          </dl>
        </Section>

        {episode.provider ? (
          <Section title={copy.sections.provider}>
            <dl className="j-facts">
              <dt>Name</dt>
              <dd>{episode.provider.name}</dd>
              <dt>District</dt>
              <dd>{episode.provider.district}</dd>
              <dt>Opening hours</dt>
              <dd>{episode.provider.hours}</dd>
              <dt>Languages</dt>
              <dd>{episode.provider.languages.join(", ")}</dd>
            </dl>
            <p className="j-fine">{JOURNEY.providers.curated}</p>
          </Section>
        ) : null}

        {episode.visitBrief ? (
          <Section title={copy.sections.brief}>
            <ol className="p-list j-brief">
              {BRIEF_ORDER.map((key) => {
                const field = JOURNEY.brief.fields[key];
                const vi = episode.visitBriefVi?.[key];
                return (
                  <li className="p-reg p-reg--ruled" key={key}>
                    <span className="p-reg__mark p-mark">{field.en}</span>
                    <p className="p-reg__vi j-brief__value">
                      {episode.visitBrief?.[key] || JOURNEY.brief.empty}
                    </p>
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
          </Section>
        ) : null}

        <Section title={copy.sections.medications}>
          {episode.confirmedMedications.length > 0 ? (
            <>
              <ul className="j-meds">
                {episode.confirmedMedications.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
              <p className="j-fine">{copy.medicationsNote}</p>
            </>
          ) : (
            <p className="j-empty">{copy.noMedications}</p>
          )}
        </Section>

        <Section title={copy.sections.documents}>
          {episode.documents.length > 0 ? (
            <>
              <ol className="p-list j-brief">
                {episode.documents.map((doc, index) => (
                  <li className="p-reg p-reg--ruled" key={doc.id}>
                    <span className="p-reg__mark p-ord">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <p className="p-reg__vi j-brief__value" lang="vi">
                      {doc.vi}
                    </p>
                    <p className="p-reg__en j-brief__value" lang="en">
                      {doc.en}
                    </p>
                  </li>
                ))}
              </ol>
              <p className="j-fine">{copy.documentsNote}</p>
            </>
          ) : (
            <p className="j-empty">{copy.noDocuments}</p>
          )}
        </Section>

        <Section title={copy.sections.followUp}>
          {episode.followUp ? (
            <p className="j-brief__value">{episode.followUp}</p>
          ) : (
            <p className="j-empty">{copy.noFollowUp}</p>
          )}
        </Section>

        <Escalation episode={episode} onRequest={requestPerson} />

        <section className="j-privacy" aria-labelledby="privacy-title">
          <h2 id="privacy-title">{copy.privacy.title}</h2>
          <p className="j-fine">{copy.privacy.body}</p>
          <button type="button" className="p-cta p-cta--ghost" onClick={wipe}>
            {copy.privacy.clear}
          </button>
        </section>
      </main>
    </div>
  );
}
