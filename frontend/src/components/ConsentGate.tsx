import { useState } from "react";

import { copy, type Language } from "../copy";
import { DemoPreview } from "./DemoPreview";
import { OnboardingFrame } from "./OnboardingFrame";

export type ConsentPayload = {
  ai_disclosure: boolean;
  interpreter_right: boolean;
  recorded_at: string;
  scope: "translation_aid";
};

type ConsentGateProps = {
  error: string | null;
  isSubmitting: boolean;
  language?: Language;
  onConsent: (payload: ConsentPayload) => void;
};

export function ConsentGate({ error, isSubmitting, language = "vi", onConsent }: ConsentGateProps) {
  const [aiDisclosure, setAiDisclosure] = useState(false);
  const [interpreterRight, setInterpreterRight] = useState(false);
  const [consentSubmitted, setConsentSubmitted] = useState(false);
  const bothChecked = aiDisclosure && interpreterRight;
  const canStart = bothChecked && !isSubmitting;
  const text = copy[language].consent;
  const otherLang = language === "vi" ? "en" : "vi";
  const companion = copy[otherLang].consent;

  return (
    <OnboardingFrame
      consentSubmitted={consentSubmitted}
      kicker={text.eyebrow}
      language={language}
      title={text.heading}
      titleId="consent-title"
    >
      <section className="consent" aria-labelledby="consent-title">
        <div className="consent-intro" lang={language}>
          <p>{text.description}</p>
          <p lang={otherLang}>{companion.description}</p>
        </div>
        <p className="consent-reminder">
          {text.limitation}
          <br />
          <span lang={otherLang}>{companion.limitation}</span>
        </p>
        <DemoPreview language={language} />
        <form
          className="consent-actions"
          onSubmit={(event) => {
            event.preventDefault();
            if (!canStart) {
              return;
            }
            setConsentSubmitted(true);
            onConsent({
              ai_disclosure: true,
              interpreter_right: true,
              recorded_at: new Date().toISOString(),
              scope: "translation_aid",
            });
          }}
        >
          <fieldset>
            <legend>{text.acknowledgements}</legend>
            <label lang={language}>
              <input
                checked={aiDisclosure}
                type="checkbox"
                onChange={(event) => setAiDisclosure(event.target.checked)}
              />
              <span className="consent-choice-copy">
                {text.aiDisclosure}
                <span lang={otherLang}>{companion.aiDisclosure}</span>
              </span>
            </label>
            <label lang={language}>
              <input
                checked={interpreterRight}
                type="checkbox"
                onChange={(event) => setInterpreterRight(event.target.checked)}
              />
              <span className="consent-choice-copy">
                {text.interpreterRight}
                <span lang={otherLang}>{companion.interpreterRight}</span>
              </span>
            </label>
          </fieldset>
          {error ? <p className="error" role="alert">{error}</p> : null}
          <div className="consent-start">
            <button className="primary" disabled={!canStart} type="submit">
              {isSubmitting ? text.starting : error ? text.retry : text.start}
            </button>
            <p className={`consent-start__hint${bothChecked ? " consent-start__hint--ready" : ""}`} lang={language}>
              {bothChecked ? text.startReadyHint : text.startHint}
              <span lang={otherLang}>{bothChecked ? companion.startReadyHint : companion.startHint}</span>
            </p>
          </div>
        </form>
      </section>
    </OnboardingFrame>
  );
}
