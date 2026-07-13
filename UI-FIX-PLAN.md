# UI Fix Plan — carepath-omega.vercel.app (scribe/frontend/)

Plan authored by Fable 5 after reviewing the live deploy and source. Executor: Opus 4.8.
Scope: the Vite/React app in `scribe/frontend/` only. Do the fixes in order. Keep diffs minimal — no redesigns, no new dependencies.

## How findings were verified (and how you re-verify)

The live site was screenshotted and probed with the repo's own Playwright
(`scribe/frontend/node_modules/playwright-core`, headless Chromium) at 1440/1100/900/800/390px widths.
Re-run any probe the same way, e.g.:

```js
// node, from scribe/frontend/: require('playwright-core'), launch chromium,
// newPage({ viewport }), goto https://carepath-omega.vercel.app/ (or local `npm run preview`)
```

Verify locally against `npm run dev`/`preview` in `scribe/frontend/` — do not deploy to verify.

## Do NOT chase these (verified non-issues)

Full-page/element screenshots of this site produce artifacts because of the sticky nav and
GSAP scroll animations. Already confirmed fine:

- Hero "Audio → SOAP" strip overhanging its card (`.hero__route--scribe { right: -3% }`) is an
  intentional accent. `document.scrollWidth - clientWidth === 0` at all tested widths — no
  horizontal overflow anywhere.
- Grey band across the bottom of the safety bento in screenshots = GSAP scrub timeline
  (`scribe/frontend/src/landing/useLandingMotion.ts:45-68`) caught mid-state. Renders correctly live.
- Scribe chapter body text is complete in source (`scribe/frontend/src/content/strings.ts:340`); the
  "truncation" seen in captures was the sticky nav bar overlaying a line during scroll-stitching.
- Marquee is 48px tall and animates correctly; "clipped text" in captures is the same stitching
  artifact.

---

## P0-1: Lead contact path is dead on production

**Symptom:** Footer "Liên hệ chương trình thí điểm" renders `href="mailto:"` (no recipient).
Submitting the pilot lead form opens a recipient-less mail draft and then shows the success-ish
"mail opened" status. The site's only conversion path silently goes nowhere.

**Root cause:** Neither `VITE_LEAD_ENDPOINT` nor `VITE_LEAD_EMAIL` is set in the Vercel project.
`submitLead()` falls through to `buildLeadMailto(payload, email = "")`
(`scribe/frontend/src/leads.ts:88-130`). The deploy gate `scribe/frontend/scripts/validate-deploy-env.mjs` only
validates `VITE_API_BASE` + `VITE_CONSOLE_URL`, so the build passed anyway
(`scribe/frontend/vercel.json` runs `npm run validate:deploy && npm run build`).

**Fix (all three parts):**
1. `scribe/frontend/scripts/validate-deploy-env.mjs`: require at least one lead channel — error if both
   `VITE_LEAD_ENDPOINT` and `VITE_LEAD_EMAIL` are empty. Extend
   `scribe/frontend/scripts/validate-deploy-env.test.mjs` accordingly (`npm run test:deploy-env`).
2. UI guard, belt-and-suspenders:
   - `scribe/frontend/src/leads.ts` / `scribe/frontend/src/LeadForm.tsx`: if no endpoint and no email, `submitLead`
     must not open `mailto:` and the form must show the existing error status (`labels.failed`
     path) instead of "mail opened". Never report success for a no-op.
   - `scribe/frontend/src/LandingPage.tsx:476-478`: don't render the footer mailto link when
     `VITE_LEAD_EMAIL` is empty (render the text non-linked, or drop it).
   - Existing tests mock `leadEmail`/`endpoint` props (`scribe/frontend/src/LeadForm.test.tsx`,
     `scribe/frontend/src/leads.test.ts`) — add the empty-config case.
3. Tell the user to set `VITE_LEAD_EMAIL` (and optionally `VITE_LEAD_ENDPOINT`) in the Vercel
   project settings — the value is a business decision; do not invent one. The code fix must be
   correct with or without it.

**Accept when:** with no lead env vars, footer shows no dead link and form submit shows an error,
not success; `npm run test` and `npm run test:deploy-env` pass; with `VITE_LEAD_EMAIL` set the
mailto contains the recipient.

## P0-2: Mobile nav menu opens off-screen — links unusable on phones

**Symptom:** At 390×844, opening the hamburger shows a white panel whose link labels are
invisible. Measured panel box: `x = -108, width = 304` — a third of it (including all left-padded
label text) is past the left viewport edge. At 900px the panel floats detached mid-nav
(`x = 225`) under the centered button.

**Root cause:** `scribe/frontend/src/styles.css:2267-2277` — `.site-nav__menu > div` is
`position: absolute; right: 0` anchored to `.site-nav__menu` (`position: relative`, line 2248),
i.e. to the 2.6rem hamburger itself, which sits mid-nav between the brand and the VI/EN toggle.
The 19rem-wide panel extends leftward from there.

**Fix:** Anchor the panel to the nav bar, not the button. `.site-nav` is `position: sticky`
(styles.css:129-141) and therefore already a containing block for absolute descendants — the
smallest fix is to drop `position: relative` from `.site-nav__menu` (line 2248) and give the
panel a right offset matching the nav padding (`right: max(1.5rem, calc((100vw - var(--container)) / 2))`
at ≥761px; `1rem`-ish at ≤760px — mirror the nav's own padding values). Keep
`width: min(19rem, calc(100vw - 2rem))`.

**Accept when:** at 320, 390, 760, and 900px widths the open panel's bounding box is fully inside
the viewport, flush near the right edge below the bar, and every link label is visible.

## P0-3: Menu never closes after navigating

**Symptom:** Tap hamburger → tap "An toàn" → page scrolls to the section but the `<details>`
panel stays open, covering the content just navigated to. Verified: `.site-nav__menu[open]`
still present after link click.

**Root cause:** Native `<details>` doesn't close on child anchor clicks
(`scribe/frontend/src/LandingPage.tsx:60-63`).

**Fix:** In `LandingPage.tsx`, close the details when a menu link is clicked (e.g. `onClick` on
the wrapping div or each link that clears the `open` attribute via a ref). Keep it a few lines —
no state library, no outside-click handler unless it's free.

**Accept when:** tapping any menu link scrolls to the section AND the panel is closed.

## P1-1: Evidence section headline wraps 2 words × 6 lines on desktop

**Symptom:** At 1440px, "Xem cách mỗi sản phẩm giữ điểm cần duyệt ở đúng chỗ." renders 64px in a
379px-wide column → 6 cramped lines. Measured: `{w: 379, fs: 64px, lines: 6}`; still 4 lines at
1100px. Inside the carousel the slide `h3` (up to 2.6rem in a ~270px column,
`.evidence-slide` col `minmax(13rem, 0.65fr)`, styles.css:2062-2094) wraps ~5 lines the same way.

**Root cause:** `.evidence` grid gives the intro `minmax(16rem, 0.55fr)` of a 74rem container
minus up to 8rem gap (styles.css:2049-2056), while `.section-intro h2` uses the global
`clamp(2rem, 4.5vw, 4rem)` scale (styles.css:1615-1618) sized for full-width intros.

**Fix:** Scoped override, not a layout rework — e.g.
`.evidence .section-intro h2 { font-size: clamp(1.8rem, 2.2vw, 2.5rem); }` and similarly cap
`.evidence-slide__copy h3` (~`clamp(1.4rem, 1.8vw, 1.9rem)`). Alternatively rebalance the column
(`0.55fr → 0.75fr`) plus a smaller cap — pick whichever reads best live, but the acceptance bar
is below. Don't touch other sections' headings.

**Accept when:** at 1280–1600px the evidence h2 wraps ≤3 lines with ≥3 words per line, and each
slide h3 wraps ≤3 lines; ≤1023px layouts (already fine) unchanged.

## P2 (do only after P0/P1; each is a 1–2 line change)

- **Sticky nav dissolves into the page while scrolling.** `--nav-bg` ≈ page beige at 0.92 alpha
  with only a hairline border (styles.css:129-141), so the floating VI/EN pill + hamburger appear
  to sit directly on content text mid-scroll (most visible on mobile). Add a subtle
  `box-shadow` (or slightly stronger bottom border) to `.site-nav` so the bar reads as a surface.
- **Marquee labels are 11.84px** (`.marquee__track span`, `font-size: 0.74rem`,
  styles.css:780-791) — uppercase microtext below the 12px floor; bump to `0.78rem`.
- **Demo controls wrap ragged on mobile:** in `.demo__controls`
  (`scribe/frontend/src/demo/DemoPlayer.tsx:251`, styles for it in styles.css) "Phát lại" wraps to an orphan
  row at 390px. Make the wrap intentional (consistent gap; buttons full-width or evenly split at
  ≤760px — match `.product-chapter__actions`' existing pattern at styles.css:2429-2433).

## Verification (run all from `scribe/frontend/`)

1. `npm run lint`, `npm run test`, `npm run test:deploy-env` — all green.
2. `npm run build` — green WITH lead env vars; FAILS with a clear message when both lead vars are
   missing (new validator rule). `npm run dev` for visual checks.
3. Playwright probe (as above) against local dev at 390 / 760 / 900 / 1440px:
   menu panel fully in-viewport, closes on navigate; evidence h2 line counts within budget;
   `scrollWidth === clientWidth` (no new horizontal overflow at any width).
4. Both languages (VI default, EN toggle) and `#/scribe` route still render — `App.test.tsx`,
   `LandingPage.test.tsx`, `ScribeTool.test.tsx` cover regressions.
5. The build's `check-diacritics.mjs` runs inside `npm run build` — any copy you touch must keep
   Vietnamese diacritics intact.

## Out of scope

Backend/`scribe/carepath`, the HF-space console (external `VITE_CONSOLE_URL` target), `interpreter/frontend/`
(separate app), content rewrites, redesigns, new sections, dependencies.
