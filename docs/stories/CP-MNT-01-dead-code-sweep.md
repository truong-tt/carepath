# CP-MNT-01 Sweep the Retired Two-Product Site

## Status

implemented

## Lane

tiny

## Product contract

`styles.css` contains no rulesets that nothing renders.

## Scope

- Delete CSS rulesets in `scribe/frontend/src/styles.css` orphaned by the
  retired Scribe-led marketing site and two-product gateway, and by the
  `ScribeShowcase.tsx` deleted in CP-UX-17.
- Deletion only. No rule is edited, no selector is renamed, no value changes.

Out of scope, and deliberately not done — see Findings:

- Trimming the unread sections of `src/content/strings.ts`.

## Acceptance criteria

1. No ruleset remains whose every class selector is unreferenced by any
   `className`, `classList` or query-selector usage in the app.
2. The Impeccable detector reports zero findings.
3. Every existing test passes, unchanged.
4. **No screenshot changes.** A deletion sweep is correct exactly when nothing
   moves.

## Validation

```powershell
npm.cmd --prefix scribe/frontend run lint
npm.cmd --prefix scribe/frontend test
npm.cmd --prefix scribe/frontend run test:deploy-env
npm.cmd --prefix scribe/frontend run build
npm.cmd --prefix scribe/frontend run e2e
node C:\Users\ADMIN\.claude\skills\impeccable\scripts\detect.mjs --json scribe/frontend/src
```

| Layer | Expected proof |
| --- | --- |
| Unit | 79 tests pass unchanged. |
| Integration | n/a. |
| E2E | 32 tests pass unchanged; the regenerated screenshots are byte-identical. |
| Platform | n/a — no deployable surface changes. |
| Release | Production build; CSS bundle shrinks. |

## Method

Substring matching lies in both directions here, so neither direction was
trusted:

- `.turn` hides inside `return`, so a naive search reports it live. Matching is
  boundary-anchored (`(?<![\w-])name(?![\w-])`).
- `visit__dot--open` never appears literally — it is built as
  `` `visit__dot--${connection}` `` — so a modifier is treated as live when its
  `stem--` prefix appears anywhere.
- Names are matched only against text that is actually **assigned as a class**:
  `className=` / `class=` values, `classList` arguments, and query selectors.
  Matching against whole source files reported `hero`, `readback`, `transcript`
  and `turn` as live purely from property names in the copy files.

A ruleset was deleted only when **every** class it names is dead. Six selectors
mixing live and dead classes were left by the script and read by hand:

| Selector | Decision |
| --- | --- |
| `.escalation .button--primary` | deleted — the ancestor is gone, so it is unreachable |
| `.tool-prestart .tool-disclaimer` | deleted — same |
| `.pilot__copy > p:not(.kicker)` | deleted — same |
| `.pilot-disclosure .lead-form` | deleted — same |
| `.button, .button-link, .scenario, .nav-cta … :focus-visible` | trimmed to the live members; the focus ring is untouched |
| `.scenario-picker, .demo-customization, .turn__columns, .site-footer, .lead-form` | trimmed to `.lead-form` |

## Evidence

2026-08-12, local.

**`styles.css`: 2489 → 1272 lines.** The CSS bundle drops from 59.49 kB to
47.01 kB, gzip 11.76 kB to 9.45 kB — about a fifth.

Deleted families, all from the retired two-product site: `onboarding-hero*`,
`burden-section` / `burden-layout` / `burden-calculator` / `calculator-*`,
`workflow-comparison`, `evidence-section` / `evidence-grid` / `evidence-links`,
`trust-section` / `trust-grid`, `hero*` / `hero-proof*`, `guided-sample` /
`sample-speaker` / `review-checklist`, `scenario` / `scenario-picker`,
`scribe-tabs` / `scribe-tab` / `scribe-mark*` / `scribe-caption` /
`scribe-note` / `scribe-doc__text`, `site-nav__links` / `site-nav__menu` /
`site-footer` / `landing-main`, `pilot*`, `demo__*` / `demo-section` /
`demo-customization`, `button-link*`, `compact-heading*`, `start-section*`,
`transcript*`, `turn` / `turn--*` / `turn__columns`, `readback*`, `risk-list`,
`safety-dialog`, `escalation`, `interpreter-status`, `chapter`, `custom-input`,
`tool-prestart`, `is-selected`.

**Impeccable detector: 3 findings → 0.** The three were `border-left: 3px` on
`.turn`, `.hero-proof__stage > p` and `.sample-speaker`, carried since CP-UX-17.
They are gone with their rulesets rather than edited in place.

**Proof that nothing moved:** lint clean, 79 unit tests, 13 deploy-env tests, 32
Playwright tests — all unchanged and passing — and every screenshot regenerated
by the e2e run is **byte-identical to the committed one**. `git status` reports
no change under `docs/qa-evidence/`.

## Findings — not done, and why

`src/content/strings.ts` is 1287 lines of `PageCopy`, and only four of its
fifteen top-level sections are read by any component: `footer`, `form`,
`scribe`, `scribeTool`. The other eleven — `metadata`, `language`, `nav`,
`landing`, `demo`, `hero`, `gateway`, `products`, `evidence`, `safety`, `pilot`
— render nowhere and ship in the JS bundle.

They were **not** deleted, because they are not merely unused.
`src/content/strings.test.ts` asserts against `nav`, `demo`, `hero` and
`products` to enforce a rule from `AGENTS.md`: that primary Vietnamese product
vocabulary never contains `Scribe`, `Interpreter` or `Console`. Deleting the
copy deletes the only executable guard on that naming contract.

That makes it a product decision, not a maintenance sweep: either the guard
moves onto the copy that *is* rendered (`landing.ts`, `demo.ts`, `paperwork.ts`,
which no test currently checks for the same rule), or the sections stay. Worth
its own story; recommended, because the guard is currently watching copy nobody
sees while the copy visitors actually read is unchecked.

## Harness Delta

None.
