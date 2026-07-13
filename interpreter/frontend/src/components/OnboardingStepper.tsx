import { useEffect, useRef } from "react";

import { copy, type Language } from "../copy";

type OnboardingStepperProps = {
  consentSubmitted: boolean;
  language: Language;
};

function hasIntent() {
  return ["doctor", "clinic_staff"].includes(localStorage.getItem("carepath-onboarding-role") ?? "")
    && ["vi-en", "en-vi"].includes(localStorage.getItem("carepath-onboarding-direction") ?? "");
}

function CheckMark() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" width="15" height="15" focusable="false">
      <path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function OnboardingStepper({ consentSubmitted, language }: OnboardingStepperProps) {
  const text = copy[language].stepper;
  const steps = [
    { label: text.language, complete: ["vi", "en"].includes(localStorage.getItem("carepath-demo-language") ?? "") },
    { label: text.about, complete: hasIntent() },
    { label: text.consent, complete: consentSubmitted },
    { label: text.device, complete: false },
    { label: text.start, complete: false },
  ];
  const current = steps.findIndex((step) => !step.complete);
  const previous = useRef<number | null>(null);

  useEffect(() => {
    if (previous.current === current) {
      return;
    }
    if (previous.current !== null) {
      console.debug("carepath:onboarding", "complete", steps[previous.current].label);
    }
    console.debug("carepath:onboarding", "view", steps[current].label);
    previous.current = current;
  }, [current, steps]);

  return (
    <nav className="onboarding-stepper" aria-label={text.label}>
      <ol>
        {steps.map((step, index) => {
          const status = step.complete ? "complete" : index === current ? "current" : "upcoming";
          const state = step.complete ? text.complete : index === current ? text.current : text.upcoming;
          return (
            <li
              className={`onboarding-step onboarding-step--${status}`}
              aria-current={index === current ? "step" : undefined}
              key={step.label}
            >
              <span className="onboarding-step__marker" aria-hidden="true">
                {step.complete ? <CheckMark /> : index + 1}
              </span>
              <span className="onboarding-step__label">{step.label}</span>
              <span className="sr-only">{state}</span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
