import type { ReactNode } from "react";

import { type Language } from "../copy";
import { OnboardingStepper } from "./OnboardingStepper";

type OnboardingFrameProps = {
  language: Language;
  consentSubmitted?: boolean;
  kicker: string;
  title: string;
  titleId?: string;
  children: ReactNode;
};

/** Shared onboarding layout: compact horizontal stepper, product kicker and
 * screen title, then the screen's own content — used by the intent quiz,
 * consent gate, and device check so they read as one flow. */
export function OnboardingFrame({ language, consentSubmitted = false, kicker, title, titleId, children }: OnboardingFrameProps) {
  return (
    <main className="page onboarding" lang={language}>
      <div className="onboarding-frame">
        <OnboardingStepper consentSubmitted={consentSubmitted} language={language} />
        <div className="onboarding-frame__head">
          <p className="onboarding-kicker">{kicker}</p>
          <h1 className="onboarding-title" id={titleId}>{title}</h1>
        </div>
        {children}
      </div>
    </main>
  );
}
