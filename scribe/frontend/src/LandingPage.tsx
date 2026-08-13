import { useEffect, useState, type CSSProperties } from "react";
import logoUrl from "./assets/carepath.svg";
import { LANDING, type Lang } from "./content/landing";
import { copyFor } from "./content/strings";
import { scenarios } from "./demo/scenarios";
import LeadForm from "./LeadForm";
import "./landing.css";
import { leadContact, zaloHref } from "./leads";

const getCareHref = "/get-care/";
const visitHref = "/kham-song-ngu/";
const paperworkHref = "/dich-giay-to/";
const scribeHref = "/ghi-chep-lam-sang/";

/* The refusals were marked with a `✕` from `content:` — a Unicode glyph
   rendering at whatever weight the platform happened to supply, unrelated to
   the type around it. One drawn mark instead, at the stroke weight the rules
   use. */
function RefuseMark() {
  return (
    <svg
      className="p-refuse__mark"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="square"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M3 3 L13 13 M13 3 L3 13" />
    </svg>
  );
}

export default function LandingPage() {
  // English first: the primary reader is a foreign patient, or someone judging
  // whether this helps one. Vietnamese is one click away and complete.
  const [lang, setLang] = useState<Lang>("en");
  const t = LANDING[lang];

  // The document root has to agree with what is on screen, or a screen reader
  // announces English prose with Vietnamese phonemes.
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);
  const footer = copyFor("vi").footer;
  // A held row carries no `en` key at all, so the tuple is a union of two
  // shapes. Widened once here rather than narrowed at every use.
  const docRows: readonly { vi: string; en?: string }[] = t.docRows;

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
          <a className="p-cta" href={getCareHref}>
            {t.navCta}
          </a>
        </div>
      </nav>

      <main id="top" tabIndex={-1}>
        {/* The document leads. A visitor meets the patient's problem — a piece
            of paper in a language they don't have — before being told about it,
            and meets it split across the spine, so the two lines whose English
            is being withheld are visible as gaps in the first viewport. */}
        <section className="p-wrap p-hero" aria-labelledby="hero-title">
          <div className="p-reg">
            <div className="p-hero__claim">
              <h1 id="hero-title">
                {t.heroLead}
                <em>{t.heroMark}</em>
              </h1>
              <p className="p-hero__body">{t.heroBody}</p>
              <p className="p-hero__actions">
                <a className="p-cta" href={getCareHref}>
                  {t.heroPrimary}
                </a>
                {/* The second door, not a second-class one. Someone already
                    holding Vietnamese paper does not need the journey's first
                    four steps and should not have to walk through them. */}
                <a className="p-cta p-cta--ghost" href={paperworkHref}>
                  {t.heroSecondary}
                </a>
              </p>
            </div>
            {/* The sheet's identity sits in the right register, bottom-aligned
                to the claim — so it heads the column its own lines are about to
                fill, and the two halves of the first viewport are one object
                rather than a headline with an empty half beside it. */}
            <div className="p-reg__en p-hero__sheet">
              <span className="p-mark">{t.docLabel}</span>
              <span className="p-doc__org">{t.docOrg}</span>
              <span className="p-doc__title">{t.docTitle}</span>
              <span className="p-doc__meta">
                {t.docMeta.map((item) => (
                  <span key={item}>{item}</span>
                ))}
              </span>
            </div>
          </div>

          <figure className="p-doc">
            <ol className="p-doc__rows">
              {docRows.map((row, index) => (
                <li
                  className={`p-reg p-reg--ruled${index === 0 ? " p-reg--top" : ""}`}
                  key={row.vi}
                >
                  <span className="p-reg__mark p-ord">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span className="p-reg__vi p-row__vi" lang="vi">
                    {row.vi}
                  </span>
                  {/* A held row has no English at all — not hidden, absent.
                      What sits in the cell is the edge of the gap and the
                      reason for it, never a stand-in for the missing string. */}
                  {row.en ? (
                    <span
                      className="p-reg__en p-row__en"
                      lang="en"
                      style={{ "--i": index } as CSSProperties}
                    >
                      {row.en}
                    </span>
                  ) : (
                    <span className="p-reg__en p-held">
                      <span className="p-held__mark">{t.docHeldMark}</span>
                      <span className="p-held__why">{t.docHeldNote}</span>
                    </span>
                  )}
                </li>
              ))}
            </ol>

            <figcaption className="p-reg p-doc__foot">
              <span className="p-reg__mark">
                <span className="p-seal" aria-hidden="true">
                  {t.docSeal}
                </span>
              </span>
              <p className="p-reg__wide">{t.docFoot}</p>
            </figcaption>
          </figure>
        </section>

        {/* The spine, immediately after the document. A visitor who has just
            seen a withheld prescription line needs to know what surrounds it
            before they are given evidence about it. Six numbered steps, not six
            feature cards: the order is the argument. */}
        <section className="p-wrap p-section" id="journey" aria-labelledby="journey-title">
          <div className="p-reg p-section__head">
            <span className="p-reg__mark p-mark">{t.journeyLabel}</span>
            <h2 className="p-reg__wide" id="journey-title">
              {t.journeyTitle}
            </h2>
          </div>
          <ol className="p-list">
            {t.journeySteps.map((step, index) => (
              <li className="p-reg p-reg--ruled" key={step.title}>
                <span className="p-reg__mark p-ord">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="p-reg__vi">{step.title}</h3>
                <p className="p-reg__en">{step.body}</p>
              </li>
            ))}
          </ol>
          <p className="p-moments__note p-indent">{t.journeyNote}</p>
        </section>

        {/* One committed field, one comparison. Two numbers that only mean
            something next to each other belong either side of the rule the
            whole page uses to mean exactly that. */}
        <section className="p-field" id="problem" aria-labelledby="problem-title">
          <div className="p-wrap p-section">
            <div className="p-reg p-section__head">
              <span className="p-reg__mark p-mark">{t.problemLabel}</span>
              <h2 className="p-reg__vi" id="problem-title">
                {t.problemTitle}
              </h2>
              <p className="p-reg__en p-lede">{t.problemBody}</p>
            </div>

            <div className="p-reg p-reg--ruled p-reg--top">
              <span className="p-reg__mark p-mark" aria-hidden="true" />
              <div className="p-reg__vi p-compare p-compare--base">
                <strong className="p-compare__fig">{t.compareBase.figure}</strong>
                <span className="p-compare__cap">{t.compareBase.caption}</span>
              </div>
              <div className="p-reg__en p-compare p-compare--risk">
                <strong className="p-compare__fig">{t.compareRisk.figure}</strong>
                <span className="p-compare__cap">{t.compareRisk.caption}</span>
              </div>
            </div>

            <ul className="p-list">
              {t.problemNotes.map((note) => (
                <li className="p-reg p-reg--ruled" key={note.lead}>
                  <span className="p-reg__mark p-mark" aria-hidden="true" />
                  <p className="p-reg__vi p-note">
                    <b>{note.lead}</b>
                  </p>
                  <p className="p-reg__en p-note">{note.body}</p>
                </li>
              ))}
            </ul>

            {/* The comparison is the strongest claim on the page and it is not
                ours. It carries its citation next to it, not in a footer. */}
            <p className="p-cite p-indent">{t.compareSource}</p>
          </div>
        </section>

        {/* The statistics say harm is likelier. The clock says what it looks
            like from inside. One is evidence, the other is why anyone would
            care — and neither works alone, so they sit next to each other. */}
        <section className="p-wrap p-section" id="emma" aria-labelledby="emma-title">
          <div className="p-reg p-section__head">
            <span className="p-reg__mark p-mark">{t.timelineLabel}</span>
            <h2 className="p-reg__wide" id="emma-title">
              {t.timelineTitle}
            </h2>
          </div>
          <ol className="p-list">
            {t.timeline.map((beat) => (
              <li className="p-reg p-reg--ruled" key={beat.when}>
                <span className="p-reg__mark p-ord">{beat.when}</span>
                <p className="p-reg__wide">{beat.body}</p>
              </li>
            ))}
          </ol>
          <p className="p-moments__note p-indent">{t.timelineNote}</p>
        </section>

        {/* The argument the page was missing: an interpreter covers the
            conversation, and all three of the moments the literature names
            happen after it, on paper. Numbered as a sequence because it is
            one — this is a timeline, not three features. */}
        <section className="p-wrap p-section" id="moments" aria-labelledby="moments-title">
          <div className="p-reg p-section__head">
            <span className="p-reg__mark p-mark">{t.momentsLabel}</span>
            <h2 className="p-reg__wide" id="moments-title">
              {t.momentsTitle}
            </h2>
          </div>
          <ol className="p-list">
            {t.moments.map((moment, index) => (
              <li className="p-reg p-reg--ruled" key={moment.when}>
                <span className="p-reg__mark p-ord">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="p-reg__vi">{moment.when}</h3>
                <p className="p-reg__en">{moment.body}</p>
              </li>
            ))}
          </ol>
          <p className="p-moments__note p-indent">{t.momentsNote}</p>
        </section>

        <section className="p-field" id="try" aria-labelledby="try-title">
          <div className="p-wrap p-section">
            <div className="p-reg p-section__head">
              <span className="p-reg__mark p-mark">{t.tryLabel}</span>
              <h2 className="p-reg__vi" id="try-title">
                {t.tryTitle}
              </h2>
              <p className="p-reg__en p-lede">{t.tryBody}</p>
            </div>
            <ul className="p-list">
              {t.tryItems.map((item) => (
                <li className="p-reg p-reg--ruled" key={item.title}>
                  <span className="p-reg__mark p-mark" aria-hidden="true" />
                  <h3 className="p-reg__vi">{item.title}</h3>
                  <p className="p-reg__en">{item.body}</p>
                </li>
              ))}
            </ul>
            <p className="p-try__cta p-indent">
              <a className="p-cta" href={getCareHref}>
                {t.tryCta}
              </a>{" "}
              <a className="p-cta p-cta--ghost" href="/thu-nghiem/">
                {t.trySecondary}
              </a>
            </p>
          </div>
        </section>

        <section className="p-wrap p-section" id="how" aria-labelledby="how-title">
          <div className="p-reg p-section__head">
            <span className="p-reg__mark p-mark">{t.howLabel}</span>
            <h2 className="p-reg__wide" id="how-title">
              {t.howTitle}
            </h2>
          </div>
          <ol className="p-list">
            {t.howSteps.map((step, index) => (
              <li className="p-reg p-reg--ruled" key={step.title}>
                <span className="p-reg__mark p-ord">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="p-reg__vi">{step.title}</h3>
                <p className="p-reg__en">{step.body}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* Measured results as a results table, with the limits carried in the
            same structure — the journal convention this page borrows from. */}
        <section className="p-wrap p-section" id="evidence" aria-labelledby="evidence-title">
          <div className="p-reg p-section__head">
            <span className="p-reg__mark p-mark">{t.evidenceLabel}</span>
            <h2 className="p-reg__vi" id="evidence-title">
              {t.evidenceTitle}
            </h2>
            <div className="p-reg__en">
              <p className="p-lede">{t.evidenceBody}</p>
              <p className="p-lede">
                <b>{t.priceNote.lead}</b>
                {t.priceNote.body}
              </p>
            </div>
          </div>

          <table className="p-table p-indent">
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

          <div className="p-reg p-limits">
            <span className="p-reg__mark p-mark" aria-hidden="true" />
            <div className="p-reg__wide">
              <h3>{t.limitsTitle}</h3>
              <ul>
                {t.limits.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* Single statements, one per row, so no spine is drawn here. An empty
            right register has one meaning on this page and this is not it. */}
        <section className="p-wrap p-section" aria-labelledby="safety-title">
          <div className="p-reg p-section__head">
            <span className="p-reg__mark p-mark">{t.safetyLabel}</span>
            <h2 className="p-reg__wide" id="safety-title">
              {t.safetyTitle}
            </h2>
          </div>
          <ul className="p-list">
            {t.safetyItems.map((item) => (
              <li className="p-reg p-reg--ruled" key={item}>
                <span className="p-reg__mark">
                  <RefuseMark />
                </span>
                <span className="p-reg__wide p-refuse__text">{item}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="p-field" id="start" aria-labelledby="start-title">
          <div className="p-wrap p-section">
            <div className="p-reg p-section__head">
              <span className="p-reg__mark p-mark">{t.startLabel}</span>
              <h2 className="p-reg__vi" id="start-title">
                {t.startTitle}
              </h2>
              <p className="p-reg__en p-lede">{t.startBody}</p>
            </div>
            <div className="p-reg">
              <span className="p-reg__mark p-mark" aria-hidden="true" />
              <div className="p-reg__wide">
                <div className="p-start__actions">
                  <a className="p-cta" href={getCareHref}>
                    {t.startCta}
                  </a>
                  {/* The page's whole argument is that harm concentrates on
                      paper. Until now every door it opened was a conversation:
                      the document reader existed but was reachable only from
                      inside a started visit. This is the paperwork door. */}
                  <a className="p-cta p-cta--ghost" href={paperworkHref}>
                    {t.startPaperwork}
                  </a>
                  {/* The clinician's doors, named as the clinician's. They are
                      not lesser products; they are for the other person in the
                      room, and labelling them that way is what stops this page
                      reading as four things for sale. */}
                  <a className="p-cta p-cta--ghost" href={visitHref}>
                    {t.startVisit}
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
                      language={lang}
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
