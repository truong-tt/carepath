import { useState, type CSSProperties } from "react";
import logoUrl from "./assets/carepath.svg";
import { LANDING, type Lang } from "./content/landing";
import { copyFor } from "./content/strings";
import { scenarios } from "./demo/scenarios";
import LeadForm from "./LeadForm";
import "./landing.css";
import { leadContact, zaloHref } from "./leads";

const visitHref = "/kham-song-ngu/";
const scribeHref = "/ghi-chep-lam-sang/";

export default function LandingPage() {
  const [lang, setLang] = useState<Lang>("vi");
  const t = LANDING[lang];
  const footer = copyFor("vi").footer;

  return (
    <div className="landing" lang={lang}>
      <nav className="p-nav" aria-label={t.navAria}>
        <a className="p-nav__brand" href="#top" aria-label="CarePath">
          <img src={logoUrl} alt="" />
          <span>CarePath</span>
        </a>
        <div className="p-nav__links">
          {t.nav.map((item) => (
            <a key={item.href} href={item.href}>
              {item.label}
            </a>
          ))}
        </div>
        <div className="p-nav__end">
          <button
            type="button"
            className="p-lang"
            onClick={() => setLang(lang === "vi" ? "en" : "vi")}
            aria-label={t.langToggleAria}
          >
            {t.langToggle}
          </button>
          <a className="p-cta" href={visitHref}>
            {t.navCta}
          </a>
        </div>
      </nav>

      <main id="top" tabIndex={-1}>
        {/* The document leads. A visitor meets the patient's problem — a piece
            of paper in a language they don't have — before being told about it. */}
        <section className="p-wrap p-hero" aria-labelledby="hero-title">
          <div className="p-hero__claim">
            <h1 id="hero-title">
              {t.heroLead}
              <em>{t.heroMark}</em>
            </h1>
            <p className="p-hero__body">{t.heroBody}</p>
            <p className="p-hero__actions">
              <a className="p-cta" href={visitHref}>
                {t.heroPrimary}
              </a>
              <a className="p-cta p-cta--ghost" href="#problem">
                {t.heroSecondary}
              </a>
            </p>
          </div>

          <div className="p-hero__doc">
            <span className="p-label">{t.docLabel}</span>
            <figure className="p-doc">
            <figcaption className="p-doc__head">
              <span className="p-doc__org">{t.docOrg}</span>
              <span className="p-doc__title">{t.docTitle}</span>
              <span className="p-doc__meta">
                {t.docMeta.map((item) => (
                  <span key={item}>{item}</span>
                ))}
              </span>
            </figcaption>
            <ol className="p-doc__rows">
              {t.docRows.map((row, index) => (
                <li className="p-row" key={row.vi}>
                  <span className="p-row__no">{index + 1}</span>
                  <span className="p-row__vi" lang="vi">
                    {row.vi}
                    <span
                      className="p-row__en"
                      lang="en"
                      style={{ "--i": index } as CSSProperties}
                    >
                      {row.en}
                    </span>
                  </span>
                </li>
              ))}
            </ol>
            <div className="p-doc__foot">
              <span className="p-seal" aria-hidden="true">
                {t.docSeal}
              </span>
              <span>{t.docFoot}</span>
            </div>
            </figure>
          </div>
        </section>

        {/* One committed field, one comparison. Two numbers that only mean
            something next to each other do not belong in separate boxes. */}
        <section className="p-field" id="problem" aria-labelledby="problem-title">
          <div className="p-wrap p-section">
            <div className="p-section__head">
              <span className="p-label">{t.problemLabel}</span>
              <h2 id="problem-title">{t.problemTitle}</h2>
              <p className="p-lede">{t.problemBody}</p>
            </div>

            <div className="p-compare">
              <div className="p-compare__side p-compare__side--base">
                <strong className="p-compare__fig">{t.compareBase.figure}</strong>
                <span className="p-compare__cap">{t.compareBase.caption}</span>
              </div>
              <div className="p-compare__side p-compare__side--risk">
                <strong className="p-compare__fig">{t.compareRisk.figure}</strong>
                <span className="p-compare__cap">{t.compareRisk.caption}</span>
              </div>
            </div>

            {/* The comparison is the strongest claim on the page and it is not
                ours. It carries its citation next to it, not in a footer. */}
            <p className="p-cite">{t.compareSource}</p>

            {t.problemNotes.map((note) => (
              <p className="p-note" key={note.lead}>
                <b>{note.lead}</b>
                {note.body}
              </p>
            ))}
          </div>
        </section>

        {/* The argument the page was missing: an interpreter covers the
            conversation, and all three of the moments the literature names
            happen after it, on paper. Numbered as a sequence because it is
            one — this is a timeline, not three features. */}
        <section className="p-wrap p-section" id="moments" aria-labelledby="moments-title">
          <div className="p-section__head">
            <span className="p-label">{t.momentsLabel}</span>
            <h2 id="moments-title">{t.momentsTitle}</h2>
          </div>
          <ol className="p-moments">
            {t.moments.map((moment) => (
              <li key={moment.when}>
                <h3>{moment.when}</h3>
                <p>{moment.body}</p>
              </li>
            ))}
          </ol>
          <p className="p-moments__note">{t.momentsNote}</p>
        </section>

        <section className="p-field" id="try" aria-labelledby="try-title">
          <div className="p-wrap p-section">
            <div className="p-section__head">
              <span className="p-label">{t.tryLabel}</span>
              <h2 id="try-title">{t.tryTitle}</h2>
              <p className="p-lede">{t.tryBody}</p>
            </div>
            <ul className="p-try">
              {t.tryItems.map((item) => (
                <li key={item.title}>
                  <h3>{item.title}</h3>
                  <p>{item.body}</p>
                </li>
              ))}
            </ul>
            <a className="p-cta p-try__cta" href="/thu-nghiem/">
              {t.tryCta}
            </a>
          </div>
        </section>

        <section className="p-wrap p-section" id="how" aria-labelledby="how-title">
          <div className="p-section__head">
            <span className="p-label">{t.howLabel}</span>
            <h2 id="how-title">{t.howTitle}</h2>
          </div>
          <ol className="p-steps">
            {t.howSteps.map((step) => (
              <li key={step.title}>
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* Measured results as a results table, with the limits carried in the
            same structure — the journal convention this page borrows from. */}
        <section className="p-wrap p-section" id="evidence" aria-labelledby="evidence-title">
          <div className="p-section__head">
            <span className="p-label">{t.evidenceLabel}</span>
            <h2 id="evidence-title">{t.evidenceTitle}</h2>
            <p className="p-lede">{t.evidenceBody}</p>
            <p className="p-lede">
              <b>{t.priceNote.lead}</b>
              {t.priceNote.body}
            </p>
          </div>

          <table className="p-table">
            <caption>{t.tableCaption}</caption>
            <thead>
              <tr>
                {t.tableHead.map((head) => (
                  <th key={head} scope="col">
                    {head}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {t.tableRows.map((row) => (
                <tr key={row.metric}>
                  <th scope="row">{row.metric}</th>
                  <td>
                    <span className="p-figure">{row.figure}</span>
                  </td>
                  <td>{row.note}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="p-limits">
            <h3>{t.limitsTitle}</h3>
            <ul>
              {t.limits.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </section>

        <section className="p-wrap p-section" aria-labelledby="safety-title">
          <div className="p-section__head">
            <span className="p-label">{t.safetyLabel}</span>
            <h2 id="safety-title">{t.safetyTitle}</h2>
          </div>
          <ul className="p-refuse">
            {t.safetyItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>

        <section className="p-field" id="start" aria-labelledby="start-title">
          <div className="p-wrap p-section">
            <div className="p-section__head">
              <span className="p-label">{t.startLabel}</span>
              <h2 id="start-title">{t.startTitle}</h2>
              <p className="p-lede">{t.startBody}</p>
            </div>
            <div className="p-start">
              <div className="p-start__actions">
                <a className="p-cta" href={visitHref}>
                  {t.startCta}
                </a>
                <a className="p-cta p-cta--ghost" href={scribeHref}>
                  {t.startScribe}
                </a>
              </div>
              <details className="p-pilot">
                <summary>{t.pilotSummary}</summary>
                <div>
                  {/* `interest="scribe"` was left over from the two-product
                      site. This page is about the bilingual visit, and a pilot
                      enquiry arriving tagged as the wrong product routes the
                      lead wrong. The selector is visible again so the clinic
                      says which one it wants. */}
                  <LeadForm
                    language="vi"
                    interest="both"
                    scenario={scenarios[0]}
                    clinic=""
                    specialty=""
                    transcript=""
                  />
                </div>
              </details>
            </div>
          </div>
        </section>
      </main>

      <footer className="p-foot">
        <strong>{footer.promise}</strong>
        <p>{footer.honesty}</p>
        <div className="p-foot__links">
          <a href={`mailto:${leadContact.email}`}>{footer.contact}</a>
          <a href={zaloHref}>Zalo · {leadContact.phone}</a>
        </div>
      </footer>
    </div>
  );
}
