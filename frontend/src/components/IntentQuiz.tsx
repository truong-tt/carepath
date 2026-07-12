import { useState } from "react";

import { copy, type Language } from "../copy";
import { OnboardingFrame } from "./OnboardingFrame";

export type Intent = {
  direction: "vi-en" | "en-vi";
  role: "doctor" | "clinic_staff";
};

const defaults: Intent = { role: "doctor", direction: "vi-en" };

function storedIntent(): Intent {
  return {
    role: localStorage.getItem("carepath-onboarding-role") === "clinic_staff" ? "clinic_staff" : "doctor",
    direction: localStorage.getItem("carepath-onboarding-direction") === "en-vi" ? "en-vi" : "vi-en",
  };
}

function OptionCard({ name, checked, onChange, label, recommended }: {
  name: string;
  checked: boolean;
  onChange: () => void;
  label: string;
  recommended?: string;
}) {
  return (
    <div className={`option-card${checked ? " option-card--selected" : ""}`}>
      <label className="option-card__label">
        <input checked={checked} name={name} type="radio" onChange={onChange} />
        <span className="option-card__text">{label}</span>
      </label>
      {recommended ? <span aria-hidden="true" className="option-card__badge">{recommended}</span> : null}
    </div>
  );
}

export function IntentQuiz({ language, onComplete }: { language: Language; onComplete: (intent: Intent) => void }) {
  const [step, setStep] = useState(0);
  const [intent, setIntent] = useState(storedIntent);
  const text = copy[language].intent;
  const kicker = text.moment;

  function complete(nextIntent = intent) {
    localStorage.setItem("carepath-onboarding-role", nextIntent.role);
    localStorage.setItem("carepath-onboarding-direction", nextIntent.direction);
    onComplete(nextIntent);
  }

  const isRole = step === 0;
  const titleId = isRole ? "intent-role-title" : "intent-direction-title";

  return (
    <OnboardingFrame
      kicker={kicker}
      language={language}
      title={isRole ? text.roleQuestion : text.directionQuestion}
      titleId={titleId}
    >
      <section className="intent-quiz" aria-labelledby={titleId}>
        <fieldset className="option-cards" aria-labelledby={titleId}>
          {isRole ? (
            <>
              <OptionCard checked={intent.role === "doctor"} label={text.doctor} name="role" recommended={text.recommended} onChange={() => setIntent((current) => ({ ...current, role: "doctor" }))} />
              <OptionCard checked={intent.role === "clinic_staff"} label={text.clinicStaff} name="role" onChange={() => setIntent((current) => ({ ...current, role: "clinic_staff" }))} />
            </>
          ) : (
            <>
              <OptionCard checked={intent.direction === "vi-en"} label={text.viToEn} name="direction" recommended={text.recommended} onChange={() => setIntent((current) => ({ ...current, direction: "vi-en" }))} />
              <OptionCard checked={intent.direction === "en-vi"} label={text.enToVi} name="direction" onChange={() => setIntent((current) => ({ ...current, direction: "en-vi" }))} />
            </>
          )}
        </fieldset>
        <button className="primary" type="button" onClick={() => (isRole ? setStep(1) : complete())}>{text.continue}</button>
        <button className="text-button" type="button" onClick={() => complete(defaults)}>{text.skip}</button>
      </section>
    </OnboardingFrame>
  );
}
