import { useCallback, useState } from "react";
import logoUrl from "./assets/carepath.svg";
import { copyFor, sources } from "./content/strings";
import DemoPlayer from "./demo/DemoPlayer";
import { getScenario, scenarios } from "./demo/scenarios";
import type { Language } from "./demo/types";
import LeadForm from "./LeadForm";
import ScribeShowcase from "./scribe/ScribeShowcase";

interface LandingPageProps {
  language: Language;
  onLanguageChange?: (language: Language) => void;
}

export default function LandingPage({
  language,
  onLanguageChange,
}: LandingPageProps) {
  const copy = copyFor(language);
  const [clinicName, setClinicName] = useState("Phòng khám Đa khoa An Bình");
  const [specialty, setSpecialty] = useState("Nội tổng quát");
  const [scenarioId, setScenarioId] = useState(scenarios[0].id);
  const [transcript, setTranscript] = useState("");
  const scenario = getScenario(scenarioId);
  const handleTranscriptChange = useCallback((value: string) => {
    setTranscript(value);
  }, []);

  return (
    <div className="site-shell">
      <nav className="site-nav" aria-label={language === "vi" ? "Điều hướng chính" : "Main navigation"}>
        <a className="site-nav__brand" href="#top" aria-label="CarePath">
          <img src={logoUrl} alt="" />
          <span>CarePath</span>
        </a>
        <div className="site-nav__links">
          <a href="#demo">{copy.nav.demo}</a>
          <a href="#scribe">{copy.nav.scribe}</a>
          <a href="#safety">{copy.nav.safety}</a>
          <a href="#process">{copy.nav.process}</a>
          <a href="#cost">{copy.nav.cost}</a>
        </div>
        <div className="site-nav__actions">
          <div className="language-toggle" aria-label={copy.language.label}>
            <button
              aria-pressed={language === "vi"}
              onClick={() => onLanguageChange?.("vi")}
              type="button"
            >
              {copy.language.vi}
            </button>
            <button
              aria-pressed={language === "en"}
              onClick={() => onLanguageChange?.("en")}
              type="button"
            >
              {copy.language.en}
            </button>
          </div>
          <a className="nav-cta" href="#demo">{copy.hero.primaryCta}</a>
        </div>
      </nav>

      <main id="top">
        <section className="hero">
          <div className="hero__copy">
            <h1 className="hero-title">
              {copy.hero.titleBefore} {copy.hero.titleAfter}
            </h1>
            <p className="hero__body">{copy.hero.body}</p>
            <div className="hero__actions">
              <a className="button-link button-link--primary" href="#demo">
                {copy.hero.primaryCta}
              </a>
              <a className="button-link button-link--secondary" href="#safety">
                {copy.hero.secondaryCta}
              </a>
            </div>
            <p className="hero__note">{copy.hero.note}</p>
          </div>
        </section>

        <section className="modules" aria-labelledby="modules-title">
          <h2 className="visually-hidden" id="modules-title">
            {copy.modules.heading}
          </h2>
          <a className="module-tile" href="#demo">
            <h3>{copy.modules.interpreter.name}</h3>
            <p>{copy.modules.interpreter.body}</p>
            <span aria-hidden="true" className="module-tile__arrow">↓</span>
          </a>
          <a className="module-tile module-tile--scribe" href="#scribe">
            <h3>{copy.modules.scribe.name}</h3>
            <p>{copy.modules.scribe.body}</p>
            <span aria-hidden="true" className="module-tile__arrow">↓</span>
          </a>
        </section>

        <section className="demo-stage" id="demo">
          <DemoPlayer
            language={language}
            clinicName={clinicName}
            specialty={specialty}
            scenarioId={scenarioId}
            onClinicNameChange={setClinicName}
            onSpecialtyChange={setSpecialty}
            onScenarioChange={setScenarioId}
            onTranscriptChange={handleTranscriptChange}
          />
        </section>

        <div className="marquee" aria-label={copy.marquee.join(", ")}>
          <div className="marquee__track">
            {[...copy.marquee, ...copy.marquee].map((item, index) => (
              <span key={`${item}-${index}`}>{item}</span>
            ))}
          </div>
        </div>

        <section className="chapter scribe" id="scribe">
          <div className="chapter__intro">
            <p className="kicker">{copy.scribe.kicker}</p>
            <h2>{copy.scribe.title}</h2>
            <p>{copy.scribe.body}</p>
          </div>
          <ScribeShowcase language={language} />
          <p className="scribe-note">{copy.scribe.note}</p>
          <a className="button-link button-link--secondary scribe-cta" href="#/scribe">
            {copy.scribe.cta}
          </a>
        </section>

        <section className="chapter problem" id="problem">
          <div className="chapter__intro">
            <p className="kicker">{copy.problem.kicker}</p>
            <h2>{copy.problem.title}</h2>
            <p>{copy.problem.body}</p>
          </div>
          <div className="evidence-grid">
            <article>
              <strong>{copy.problem.memoryStat}</strong>
              <p>{copy.problem.memoryDetail}</p>
              <a href={sources.research.href} target="_blank" rel="noreferrer">
                Kessels 2003, qua {sources.research.label}
              </a>
            </article>
            <article>
              <strong>{copy.problem.translationStat}</strong>
              <p>{copy.problem.translationDetail}</p>
              <a href={sources.research.href} target="_blank" rel="noreferrer">
                BMJ Quality &amp; Safety 2025, qua {sources.research.label}
              </a>
            </article>
          </div>
          <blockquote>{copy.problem.framing}</blockquote>
        </section>

        <section className="chapter safety" id="safety">
          <div className="chapter__intro">
            <p className="kicker">{copy.safety.kicker}</p>
            <h2>{copy.safety.title}</h2>
            <p>{copy.safety.body}</p>
          </div>
          <div className="safety-grid">
            {copy.safety.items.map((item, index) => (
              <article className="safety-card" key={item.title.vi}>
                <span className="safety-card__number">{String(index + 1).padStart(2, "0")}</span>
                <h3>{item.title[language]}</h3>
                <p>{item.body[language]}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="chapter process" id="process">
          <div className="chapter__intro">
            <p className="kicker">{copy.process.kicker}</p>
            <h2>{copy.process.title}</h2>
          </div>
          <div className="process-list">
            {copy.process.steps.map((step, index) => (
              <article key={step.title}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="chapter cost" id="cost">
          <div className="chapter__intro">
            <p className="kicker">{copy.cost.kicker}</p>
            <h2>{copy.cost.title}</h2>
            <p>{copy.cost.body}</p>
          </div>
          <div className="cost-grid">
            <article className="cost-card">
              <p>{copy.cost.interpreterTitle}</p>
              <strong>{copy.cost.interpreterValue}</strong>
              <p>{copy.cost.interpreterNote}</p>
              <div className="source-links">
                <a href={sources.phuYenRates.href} target="_blank" rel="noreferrer">
                  {sources.phuYenRates.label}
                </a>
                <a href={sources.healthPricing.href} target="_blank" rel="noreferrer">
                  {sources.healthPricing.label}
                </a>
              </div>
            </article>
            <article className="cost-card">
              <p>{copy.cost.incidentTitle}</p>
              <strong>{copy.cost.incidentValue}</strong>
              <p>{copy.cost.incidentNote}</p>
              <a href={sources.ahrqCost.href} target="_blank" rel="noreferrer">
                {sources.ahrqCost.label}
              </a>
            </article>
            <article className="cost-card cost-card--pilot">
              <p>{copy.cost.pilotTitle}</p>
              <strong>{copy.cost.pilotValue}</strong>
              <p>{copy.cost.pilotNote}</p>
            </article>
          </div>
        </section>

        <section className="chapter pilot" id="pilot">
          <div className="pilot__copy">
            <p className="kicker">{copy.pilot.kicker}</p>
            <h2>{copy.pilot.title}</h2>
            <p>{copy.pilot.body}</p>
            <div className="pilot__configuration">
              <span>{clinicName}</span>
              <span>{specialty}</span>
              <span>{scenario.title[language]}</span>
            </div>
            <small>{copy.pilot.transcriptNote}</small>
          </div>
          <LeadForm
            clinic={clinicName}
            specialty={specialty}
            scenario={scenario}
            transcript={transcript}
            language={language}
          />
        </section>
      </main>

      <footer className="site-footer">
        <div>
          <img src={logoUrl} alt="" />
          <strong>{copy.footer.promise}</strong>
        </div>
        <p>{copy.footer.posture}</p>
        <p>{copy.footer.honesty}</p>
        <a href={`mailto:${encodeURIComponent(import.meta.env.VITE_LEAD_EMAIL ?? "")}`}>
          {copy.footer.contact}
        </a>
      </footer>
    </div>
  );
}
