import { useRef } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import logoUrl from "./assets/carepath-translate.svg";
import { copyFor, sources } from "./content/strings";
import DemoPlayer from "./demo/DemoPlayer";
import type { Language } from "./demo/types";

gsap.registerPlugin(ScrollTrigger);

interface LandingPageProps {
  language: Language;
}

export default function LandingPage({ language }: LandingPageProps) {
  const copy = copyFor(language);
  const root = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      if (
        typeof window.matchMedia !== "function" ||
        window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ) {
        return;
      }

      gsap.utils.toArray<HTMLElement>(".motion-panel").forEach((panel) => {
        gsap.fromTo(
          panel,
          { opacity: 0.35, scale: 0.88 },
          {
            opacity: 1,
            scale: 1,
            ease: "none",
            scrollTrigger: {
              trigger: panel,
              start: "top 92%",
              end: "center 55%",
              scrub: 0.7,
            },
          },
        );
      });

      gsap.fromTo(
        ".safety-card",
        { y: 90, opacity: 0.35 },
        {
          y: 0,
          opacity: 1,
          stagger: 0.09,
          ease: "power2.out",
          scrollTrigger: {
            trigger: ".safety-grid",
            start: "top 80%",
            end: "bottom 70%",
            scrub: 0.8,
          },
        },
      );
    },
    { scope: root },
  );

  return (
    <div className="site-shell" ref={root}>
      <nav className="site-nav" aria-label={language === "vi" ? "Điều hướng chính" : "Main navigation"}>
        <a className="site-nav__brand" href="#top" aria-label="CarePath Translate">
          <img src={logoUrl} alt="" />
          <span>CarePath Translate</span>
        </a>
        <div className="site-nav__links">
          <a href="#demo">{copy.nav.demo}</a>
          <a href="#safety">{copy.nav.safety}</a>
          <a href="#process">{copy.nav.process}</a>
          <a href="#cost">{copy.nav.cost}</a>
        </div>
        <a className="nav-cta" href="#demo">{copy.hero.primaryCta}</a>
      </nav>

      <main id="top">
        <section className="hero">
          <div className="hero__copy">
            <p className="hero__parent">{copy.hero.parent}</p>
            <h1 className="hero-title">
              {copy.hero.titleBefore}{" "}
              <span className="hero-inline-mark" aria-hidden="true">
                <img src={logoUrl} alt="" />
              </span>{" "}
              {copy.hero.titleAfter}
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
          <div className="hero__signal" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
        </section>

        <section className="demo-stage" id="demo">
          <DemoPlayer />
        </section>

        <div className="marquee" aria-label={copy.marquee.join(", ")}>
          <div className="marquee__track">
            {[...copy.marquee, ...copy.marquee].map((item, index) => (
              <span key={`${item}-${index}`}>{item}</span>
            ))}
          </div>
        </div>

        <section className="chapter problem motion-panel" id="problem">
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
              <article className="motion-panel" key={step.title}>
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
            <article className="cost-card motion-panel">
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
            <article className="cost-card motion-panel">
              <p>{copy.cost.incidentTitle}</p>
              <strong>{copy.cost.incidentValue}</strong>
              <p>{copy.cost.incidentNote}</p>
              <a href={sources.ahrqCost.href} target="_blank" rel="noreferrer">
                {sources.ahrqCost.label}
              </a>
            </article>
            <article className="cost-card cost-card--pilot motion-panel">
              <p>{copy.cost.pilotTitle}</p>
              <strong>{copy.cost.pilotValue}</strong>
              <p>{copy.cost.pilotNote}</p>
            </article>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div>
          <img src={logoUrl} alt="" />
          <strong>{copy.footer.promise}</strong>
        </div>
        <p>{copy.footer.posture}</p>
        <p>{copy.footer.honesty}</p>
        <a href="mailto:">{copy.footer.contact}</a>
      </footer>
    </div>
  );
}
