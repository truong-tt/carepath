import { useState } from "react";

import { copy, type Language } from "../copy";

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

export function IntentQuiz({ language, onComplete }: { language: Language; onComplete: (intent: Intent) => void }) {
  const [step, setStep] = useState(0);
  const [intent, setIntent] = useState(storedIntent);
  const text = copy[language].intent;

  function complete(nextIntent = intent) {
    localStorage.setItem("carepath-onboarding-role", nextIntent.role);
    localStorage.setItem("carepath-onboarding-direction", nextIntent.direction);
    onComplete(nextIntent);
  }

  if (step === 0) {
    return (
      <main className="page" lang={language}>
        <section className="intent-quiz" aria-labelledby="intent-role-title">
          <fieldset>
            <legend id="intent-role-title">{text.roleQuestion}</legend>
            <label><input checked={intent.role === "doctor"} name="role" type="radio" onChange={() => setIntent((current) => ({ ...current, role: "doctor" }))} />{text.doctor}</label>
            <label><input checked={intent.role === "clinic_staff"} name="role" type="radio" onChange={() => setIntent((current) => ({ ...current, role: "clinic_staff" }))} />{text.clinicStaff}</label>
          </fieldset>
          <button type="button" onClick={() => setStep(1)}>{text.continue}</button>
          <button className="text-button" type="button" onClick={() => complete(defaults)}>{text.skip}</button>
        </section>
      </main>
    );
  }

  return (
    <main className="page" lang={language}>
      <section className="intent-quiz" aria-labelledby="intent-direction-title">
        <fieldset>
          <legend id="intent-direction-title">{text.directionQuestion}</legend>
          <label><input checked={intent.direction === "vi-en"} name="direction" type="radio" onChange={() => setIntent((current) => ({ ...current, direction: "vi-en" }))} />{text.viToEn}</label>
          <label><input checked={intent.direction === "en-vi"} name="direction" type="radio" onChange={() => setIntent((current) => ({ ...current, direction: "en-vi" }))} />{text.enToVi}</label>
        </fieldset>
        <button type="button" onClick={() => complete()}>{text.continue}</button>
        <button className="text-button" type="button" onClick={() => complete(defaults)}>{text.skip}</button>
      </section>
    </main>
  );
}
