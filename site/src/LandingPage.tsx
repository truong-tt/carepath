import { useRef, useState } from "react";
import logoUrl from "./assets/carepath.svg";
import { copyFor, sources, type ProductKey } from "./content/strings";
import { getScenario, scenarios } from "./demo/scenarios";
import type { Language } from "./demo/types";
import LeadForm from "./LeadForm";
import { leadContact, zaloHref, type ProductInterest } from "./leads";
import { soapDraft } from "./scribe/ScribeShowcase";

interface LandingPageProps {
  language: Language;
  onLanguageChange?: (language: Language) => void;
}

const productOrder: ProductKey[] = ["interpreter", "scribe"];
const interpreterEvidenceTurn = getScenario("allergy").turns[3];

function interpreterHref(language: Language) {
  const href = import.meta.env.VITE_CONSOLE_URL || "/phien-dich-y-khoa/";
  const url = new URL(href, window.location.href);
  if (url.origin !== window.location.origin) url.searchParams.set("lang", language);
  return url.origin === window.location.origin ? `${url.pathname}${url.search}` : url.href;
}

export default function LandingPage({
  language,
  onLanguageChange,
}: LandingPageProps) {
  const menuRef = useRef<HTMLDetailsElement>(null);
  const copy = copyFor(language);
  const [interest, setInterest] = useState<ProductInterest>("both");
  const scenario = scenarios[0];
  const interpreterUrl = interpreterHref(language);
  const scribeHref = "/ghi-chep-lam-sang/";

  const navLinks = (
    <>
      <a href="#products">{copy.nav.interpreter}</a>
      <a href="#products">{copy.nav.scribe}</a>
      <a href="#safety">{copy.nav.safety}</a>
      <a href="#pilot">{copy.nav.pilot}</a>
    </>
  );

  return (
    <div className="site-shell">
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
              if (
                menuRef.current &&
                (event.target as HTMLElement).closest("a")
              ) {
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

      <main id="top" tabIndex={-1}>
        <section className="product-gateway" id="products" aria-labelledby="gateway-title">
          <header className="section-intro section-intro--wide">
            <h1 id="gateway-title">{copy.gateway.heading}</h1>
            <p>{copy.gateway.body}</p>
          </header>
          <div className="product-accordion">
            {productOrder.map((key) => {
              const product = copy.products[key];
              return (
                <a
                  className={`product-accordion__panel product-accordion__panel--${key}`}
                  aria-label={`${product.name}: ${product.cta.open}`}
                  href={key === "interpreter" ? interpreterUrl : scribeHref}
                  key={key}
                >
                  <div className="product-accordion__heading">
                    <h2>{product.name}</h2>
                    <span className="product-accordion__helper">{product.helper}</span>
                    <span className="product-accordion__status">{product.status}</span>
                  </div>
                  <p>{product.body}</p>
                  <p className="product-accordion__timing">{product.timing}</p>
                  <dl>
                    <div>
                      <dt>{copy.gateway.useWhen}</dt>
                      <dd>{product.audience}</dd>
                    </div>
                    <div>
                      <dt>{copy.gateway.input}</dt>
                      <dd>{product.input}</dd>
                    </div>
                    <div>
                      <dt>{copy.gateway.output}</dt>
                      <dd>{product.output}</dd>
                    </div>
                  </dl>
                  <p className="product-accordion__safety">{product.chooserSafety}</p>
                  <strong className="product-accordion__cta">
                    <span aria-hidden="true">{key === "interpreter" ? "↔" : "☷"}</span>
                    {product.cta.open}
                  </strong>
                </a>
              );
            })}
          </div>
        </section>

        <section className="trust-strip" aria-label={copy.safety.title}>
          {copy.safety.trust.map((item) => (
            <article key={item.title}>
              <h2>{item.title}</h2>
              <p>{item.body}</p>
            </article>
          ))}
        </section>

        <section
          className="safety-suite"
          id="safety"
          aria-labelledby="safety-title"
          tabIndex={-1}
        >
          <header className="section-intro section-intro--on-dark">
            <h2 id="safety-title">{copy.safety.title}</h2>
            <p>{copy.safety.body}</p>
          </header>
          <div className="safety-bento">
            {(
              [
                ["shared", copy.safety.shared],
                ["interpreter", copy.safety.interpreter],
                ["scribe", copy.safety.scribe],
              ] as const
            ).map(([key, card]) => (
              <article
                className={`safety-bento__card safety-bento__card--${key}`}
                data-safety-card
                key={key}
              >
                <header>
                  <h3>{card.title}</h3>
                  <p>{card.body}</p>
                </header>
                <ul>
                  {card.items.map((item) => (
                    <li key={item.title.vi}>
                      <strong>{item.title[language]}</strong>
                      <span>{item.body[language]}</span>
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>

        <section className="evidence" aria-labelledby="evidence-title">
          <header className="section-intro">
            <h2 id="evidence-title">{copy.evidence.title}</h2>
            <p>{copy.evidence.body}</p>
            <a href={sources.research.href} target="_blank" rel="noreferrer">
              {copy.evidence.source}
            </a>
          </header>
          <div className="evidence-proof-grid">
            {copy.evidence.items.map((item) => (
              <article className={`evidence-proof evidence-proof--${item.kind}`} key={item.kind}>
                <div className="evidence-proof__copy">
                  <p>{item.kind === "research" ? copy.evidence.researchLabel : copy.evidence.sampleLabel}</p>
                  <h3>{item.title}</h3>
                  <p>{item.body}</p>
                </div>
                <div className="evidence-capture" aria-label={item.detail} role="img">
                  <div className="evidence-capture__bar">
                    <span>CarePath</span>
                    <span>{item.product}</span>
                  </div>
                  <div className="evidence-capture__content">
                    {item.kind === "interpreter" && (
                      <>
                        <div className="evidence-capture__turn">
                          <small>EN · {copy.demo.patient}</small>
                          <p lang="en">{interpreterEvidenceTurn.en}</p>
                        </div>
                        <div className="evidence-capture__turn">
                          <small>VI · {copy.demo.translation}</small>
                          <p lang="vi">{interpreterEvidenceTurn.vi}</p>
                        </div>
                      </>
                    )}
                    {item.kind === "scribe" && (
                      <dl>
                        {soapDraft.slice(0, 2).map((row) => (
                          <div key={row.key}>
                            <dt>{copy.scribe.soapLabels[row.key]}</dt>
                            <dd lang="vi">{row.text}</dd>
                          </div>
                        ))}
                      </dl>
                    )}
                    {item.kind === "research" && (
                      <p className="evidence-capture__source">docs/research.md</p>
                    )}
                    <strong>{item.detail}</strong>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="chapter pilot" id="pilot" tabIndex={-1}>
          <div className="pilot__copy">
            <h2>{copy.pilot.title}</h2>
            <p>{copy.pilot.body}</p>
            <div className="pilot__configuration">
              <span>{copy.form.interestOptions[interest]}</span>
            </div>
            <small>{copy.pilot.transcriptNote}</small>
          </div>
          <LeadForm
            clinic=""
            specialty=""
            scenario={scenario}
            transcript=""
            language={language}
            interest={interest}
            onInterestChange={setInterest}
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
        <div>
          <a href={`mailto:${leadContact.email}`}>{copy.footer.contact}</a>
          <a href={zaloHref}>Zalo · {leadContact.phone}</a>
        </div>
      </footer>
    </div>
  );
}
