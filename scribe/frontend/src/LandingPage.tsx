import { useRef } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import logoUrl from "./assets/carepath.svg";
import { copyFor } from "./content/strings";
import { scenarios } from "./demo/scenarios";
import type { Language } from "./demo/types";
import LeadForm from "./LeadForm";
import { leadContact, zaloHref } from "./leads";
import { soapDraft } from "./scribe/ScribeShowcase";

gsap.registerPlugin(useGSAP, ScrollTrigger);

interface LandingPageProps {
  language: Language;
  onLanguageChange?: (language: Language) => void;
}

const scribeHref = "/ghi-chep-lam-sang/";

export default function LandingPage({
  language,
  onLanguageChange,
}: LandingPageProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDetailsElement>(null);
  const copy = copyFor(language);
  const landing = copy.landing;

  useGSAP(
    () => {
      const media = gsap.matchMedia();
      media.add(
        "(min-width: 1024px) and (prefers-reduced-motion: no-preference)",
        () => {
          const section = rootRef.current?.querySelector<HTMLElement>(
            ".scribe-story",
          );
          const heading = rootRef.current?.querySelector<HTMLElement>(
            ".scribe-story__heading",
          );
          if (!section || !heading) return;

          ScrollTrigger.create({
            trigger: section,
            start: "top 96px",
            end: "bottom bottom-=96",
            pin: heading,
            pinSpacing: false,
          });

          gsap.utils
            .toArray<HTMLElement>(".scribe-story__visual", rootRef.current)
            .forEach((panel) => {
              gsap
                .timeline({
                  scrollTrigger: {
                    trigger: panel,
                    start: "top 88%",
                    end: "bottom 12%",
                    scrub: true,
                  },
                })
                .fromTo(
                  panel,
                  { filter: "brightness(0.94)", opacity: 0.92, scale: 0.88 },
                  {
                    filter: "brightness(1)",
                    opacity: 1,
                    scale: 1,
                    duration: 0.55,
                    ease: "none",
                  },
                )
                .to(panel, {
                  filter: "brightness(0.96)",
                  opacity: 0.92,
                  duration: 0.45,
                  ease: "none",
                });
            });
        },
      );
      return () => media.revert();
    },
    { scope: rootRef },
  );

  const navLinks = (
    <>
      <a href="#need">{copy.nav.need}</a>
      <a href="#workflow">{copy.nav.workflow}</a>
      <a href="#safety">{copy.nav.safety}</a>
      <a href="#pilot">{copy.nav.pilot}</a>
    </>
  );

  return (
    <div className="site-shell" ref={rootRef}>
      <nav
        className="site-nav"
        aria-label={language === "vi" ? "Điều hướng chính" : "Main navigation"}
      >
        <a className="site-nav__brand" href="#top" aria-label="CarePath">
          <img src={logoUrl} alt="" />
          <span>CarePath</span>
        </a>
        <div className="site-nav__links">{navLinks}</div>
        <details className="site-nav__menu" ref={menuRef}>
          <summary>{copy.nav.menu}</summary>
          <div
            onClick={(event) => {
              if (menuRef.current && (event.target as HTMLElement).closest("a")) {
                menuRef.current.open = false;
              }
            }}
          >
            {navLinks}
          </div>
        </details>
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
        </div>
      </nav>

      <aside
        className="interpreter-status"
        aria-labelledby="interpreter-status-title"
        data-interpreter-status
      >
        <div>
          <strong id="interpreter-status-title">{landing.status.title}</strong>
          <span>{landing.status.state}</span>
        </div>
        <p>{landing.status.body}</p>
      </aside>

      <main className="landing-main" id="top" tabIndex={-1}>
        <section className="scribe-hero" aria-labelledby="scribe-hero-title">
          <h1 className="scribe-hero__title" id="scribe-hero-title">
            {landing.hero.title}
          </h1>
          <div className="scribe-hero__split">
            <div className="scribe-hero__copy">
              <p>{landing.hero.body}</p>
              <div className="scribe-hero__actions">
                <a className="button-link button-link--primary" href={scribeHref}>
                  {landing.hero.primary}
                </a>
                <a className="button-link button-link--secondary" href="#workflow">
                  {landing.hero.secondary}
                </a>
              </div>
            </div>
            <div
              className="scribe-hero__visual"
              aria-label={`${landing.hero.visual.sourceLabel}. ${landing.hero.visual.transcriptLabel}. ${landing.hero.visual.draftLabel}.`}
              role="img"
            >
              <article className="scribe-hero__source">
                <span>{landing.hero.visual.sourceLabel}</span>
                <p lang="vi">{landing.hero.visual.sourceText}</p>
                <i aria-hidden="true" />
              </article>
              <article className="scribe-hero__transcript">
                <span>{landing.hero.visual.transcriptLabel}</span>
                <p>{landing.hero.visual.transcriptText}</p>
              </article>
              <article className="scribe-hero__draft">
                <span>{landing.hero.visual.draftLabel}</span>
                <p>{landing.hero.visual.draftText}</p>
                <strong>{copy.scribe.status}</strong>
              </article>
            </div>
          </div>
        </section>

        <section className="process-marquee" aria-label={landing.process.label}>
          <p className="sr-only">{landing.process.label}</p>
          <div className="process-marquee__track" aria-hidden="true">
            {[0, 1].map((copyIndex) => (
              <div className="process-marquee__group" key={copyIndex}>
                {landing.process.items.map((item) => (
                  <span key={`${copyIndex}-${item}`}>
                    {item}
                    <i />
                  </span>
                ))}
              </div>
            ))}
          </div>
        </section>

        <section className="need-section" id="need" aria-labelledby="need-title">
          <header className="landing-heading">
            <h2 id="need-title">{landing.problem.title}</h2>
            <p>{landing.problem.body}</p>
          </header>
          <div className="need-bento">
            <article className="need-bento__burden">
              <div>
                <h3>{landing.problem.duringTitle}</h3>
                <p>{landing.problem.duringBody}</p>
              </div>
              <div>
                <h3>{landing.problem.afterTitle}</h3>
                <p>{landing.problem.afterBody}</p>
              </div>
            </article>
            <article className="need-bento__workflow">
              <h3>{landing.problem.workflowTitle}</h3>
              <p>{landing.problem.workflowBody}</p>
            </article>
            <article className="need-bento__review">
              <h3>{landing.problem.reviewTitle}</h3>
              <p>{landing.problem.reviewBody}</p>
            </article>
          </div>
        </section>

        <section
          className="workflow-section"
          id="workflow"
          aria-labelledby="workflow-title"
        >
          <header className="landing-heading landing-heading--wide">
            <h2 id="workflow-title">{landing.workflow.title}</h2>
            <p>{landing.workflow.body}</p>
          </header>
          <div className="workflow-accordion">
            {landing.workflow.stages.map((stage, index) => (
              <details key={stage.title} open={index === 0}>
                <summary>{stage.title}</summary>
                <p>{stage.body}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="scribe-story" aria-labelledby="story-title">
          <div className="scribe-story__heading">
            <h2 id="story-title">
              {landing.story.titleStart}{" "}
              <span className="inline-carepath-mark" aria-hidden="true">
                <img src={logoUrl} alt="" />
              </span>{" "}
              {landing.story.titleEnd}
            </h2>
            <p>{landing.story.body}</p>
          </div>
          <div className="scribe-story__gallery">
            <article className="scribe-story__visual">
              <span>{landing.story.rawTitle}</span>
              <blockquote lang="vi">{landing.story.rawText}</blockquote>
              <p>{landing.story.rawDetail}</p>
            </article>
            <article className="scribe-story__visual scribe-story__visual--corrected">
              <span>{landing.story.correctedTitle}</span>
              <blockquote>{landing.story.correctedText}</blockquote>
              <p>{landing.story.correctedDetail}</p>
            </article>
            <article className="scribe-story__visual scribe-story__visual--draft">
              <span>{landing.story.draftTitle}</span>
              <dl>
                {soapDraft.slice(0, 3).map((row) => (
                  <div key={row.key}>
                    <dt>{copy.scribe.soapLabels[row.key]}</dt>
                    <dd lang="vi">{row.text}</dd>
                  </div>
                ))}
              </dl>
              <p>{landing.story.draftDetail}</p>
            </article>
          </div>
        </section>

        <section
          className="landing-safety"
          id="safety"
          aria-labelledby="landing-safety-title"
        >
          <header>
            <h2 id="landing-safety-title">{landing.safety.title}</h2>
            <p>{landing.safety.body}</p>
          </header>
          <div>
            {landing.safety.items.map((item) => (
              <article key={item.title}>
                <h3>{item.title}</h3>
                <p>{item.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="landing-action" id="pilot" tabIndex={-1}>
          <div className="landing-action__copy">
            <h2>{landing.action.title}</h2>
            <p>{landing.action.body}</p>
            <a className="button-link button-link--light" href={scribeHref}>
              {landing.action.primary}
            </a>
          </div>
          <div className="landing-action__form">
            <header>
              <h3>{landing.action.pilotTitle}</h3>
              <p>{landing.action.pilotBody}</p>
              <small>{landing.action.pilotNote}</small>
            </header>
            <LeadForm
              clinic=""
              specialty=""
              scenario={scenarios[0]}
              transcript=""
              language={language}
              interest="scribe"
              hideInterestField
            />
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
        <div>
          <a href={`mailto:${leadContact.email}`}>{copy.footer.contact}</a>
          <a href={zaloHref}>Zalo · {leadContact.phone}</a>
        </div>
      </footer>
    </div>
  );
}
