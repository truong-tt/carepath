import { useState } from "react";

import { copy, type Language } from "../copy";
import { DemoPreview } from "./DemoPreview";

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
  const canStart = aiDisclosure && interpreterRight && !isSubmitting;
  const text = copy[language].consent;
  const companion = copy[language === "vi" ? "en" : "vi"].consent;

  return (
    <main className="page" lang={language}>
      <section className="consent" aria-labelledby="consent-title">
        <div lang={language}>
          <p className="eyebrow">{text.eyebrow}</p>
          <h1 id="consent-title">{text.heading}</h1>
          <p>{text.description}</p>
          <p lang={language === "vi" ? "en" : "vi"}>{companion.description}</p>
        </div>
        <div lang={language}>
          <p className="eyebrow">{text.steps}</p>
          <ol className="consent-steps">
            <li>{text.doctorSpeaks}</li>
            <li>{text.aiToPatient}</li>
            <li>{text.patientSpeaks}</li>
            <li>{text.aiToDoctor}</li>
          </ol>
          <p className="consent-reminder">
            {text.limitation}
            <br />
            <span lang={language === "vi" ? "en" : "vi"}>{companion.limitation}</span>
          </p>
        </div>
        <DemoPreview language={language} />
        <form
          className="consent-actions"
          onSubmit={(event) => {
            event.preventDefault();
            if (!canStart) {
              return;
            }
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
              {text.aiDisclosure} <span lang={language === "vi" ? "en" : "vi"}>{companion.aiDisclosure}</span>
            </label>
            <label lang={language}>
              <input
                checked={interpreterRight}
                type="checkbox"
                onChange={(event) => setInterpreterRight(event.target.checked)}
              />
              {text.interpreterRight} <span lang={language === "vi" ? "en" : "vi"}>{companion.interpreterRight}</span>
            </label>
          </fieldset>
          {error ? <p className="error" role="alert">{error}</p> : null}
          <button disabled={!canStart} type="submit">
            {isSubmitting ? text.starting : error ? text.retry : text.start}
          </button>
        </form>
      </section>
    </main>
  );
}
