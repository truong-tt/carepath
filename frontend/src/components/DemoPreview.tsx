import { useState } from "react";

import { copy, type Language } from "../copy";

const moments = ["normal", "lowConfidence", "blocked"] as const;

export function DemoPreview({ language }: { language: Language }) {
  const [step, setStep] = useState<number | null>(null);
  const text = copy[language].demo;
  const workspace = copy[language].workspace;
  const moment = step === null ? null : moments[step];
  const source = moment === "normal" ? text.normalSource : moment === "lowConfidence" ? text.lowSource : text.blockedSource;
  const translation = moment === "normal" ? text.normalTranslation : moment === "lowConfidence" ? text.lowTranslation : text.blockedTranslation;

  return (
    <section className="demo-preview" aria-labelledby="demo-title">
      <p className="eyebrow">{text.eyebrow}</p>
      <h2 id="demo-title">{text.heading}</h2>
      <p className="consent-reminder">{workspace.mockDisclaimer}</p>
      {moment ? (
        <div className={`demo-preview__turn ${moment}`} aria-live="polite">
          <p className="meta">{text.step.replace("{current}", String((step ?? 0) + 1))}</p>
          <strong>{text[moment]}</strong>
          <p lang={language === "vi" ? "vi" : "en"}>{source}</p>
          <p lang={language === "vi" ? "en" : "vi"}>{translation}</p>
          {moment === "lowConfidence" ? <p>{workspace.lowConfidence}</p> : null}
          {moment === "blocked" ? <p>{workspace.confirmationRequired}</p> : null}
        </div>
      ) : null}
      <button
        type="button"
        onClick={() => setStep((current) => current === null ? 0 : current === moments.length - 1 ? null : current + 1)}
      >
        {step === null ? text.start : step === moments.length - 1 ? text.restart : text.next}
      </button>
    </section>
  );
}
