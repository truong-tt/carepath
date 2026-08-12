# CP-UX-19 A Front Door for the Paperwork

## Status

implemented

## Lane

high-risk

## Product contract

Translating a Vietnamese medical document is a task a clinician can start
directly, at `/dich-giay-to/`, without starting an interpreted consultation.

The document reader already exists and already runs every line through the risk
engine and the clinician gate. What this story adds is the route: consent,
capture, line-by-line confirmation, and a bilingual sheet that can be handed to
the patient — with the withheld gap at the same grid column it occupies on every
other surface (DEC-0022).

There is no microphone, no audio and no WebSocket anywhere in this route.

## Scope

- New route `/dich-giay-to/` (pathname check in `App.tsx`, no router).
- `PaperworkScreen` composing three endpoints that already exist:
  `POST /api/sessions`, `POST /api/v1/visits/{id}/documents`,
  `POST /api/turns/{turn_id}/confirm`.
- Reuse `DocumentCapture` and `DocumentReview` unchanged.
- Consent: the visit screen's checkbox, wording verbatim. Age, sex and reason
  become optional.
- Capability check reused from `useDemoCapability`'s health route; fail closed.
- Waiting state that names line count and elapsed time, reusing the `.d-wait`
  pattern.
- Move the `.p-reg` register family from `landing.css` to `styles.css`.
- A third CTA in the landing's start section.
- Hide any demo hub panel that would render with no usable control.
- **No change** to the risk engine, the confirmation gate, consent logic,
  microphone behaviour, TTS eligibility, the WebSocket contract, or any existing
  route. No new dependency.

Out of scope: batching the per-line translation calls into one. It is a real
optimisation — `main.py` measures ~13s/line — and it is a backend change.

## Acceptance criteria

1. The route reaches a usable capture state having opened no WebSocket and
   called no `getUserMedia`.
2. Consent is required before any read, in the visit screen's exact wording.
3. Lines render on the spine at the same grid column as `/` and `/thu-nghiem/`.
4. A held line's English has zero DOM occurrences before confirmation.
5. Confirming a line moves it into the patient sheet; unconfirmed lines can
   never appear there.
6. The waiting state names line count and elapsed time.
7. No demo hub panel renders without at least one usable control.
8. axe reports no serious violations, light and dark, at 390 and 1440.
9. Every existing e2e assertion still passes; no existing route changes.
10. Vietnamese text stays NFC-normalised with diacritics preserved.

## Validation

```powershell
npm.cmd --prefix scribe/frontend run lint
npm.cmd --prefix scribe/frontend test
npm.cmd --prefix scribe/frontend run build
npm.cmd --prefix scribe/frontend run e2e
npm.cmd --prefix scribe/frontend run build
node C:\Users\ADMIN\.claude\skills\impeccable\scripts\detect.mjs --json scribe/frontend/src
```

| Layer | Expected proof |
| --- | --- |
| Unit | `PaperworkScreen` state machine: idle, reading, held, confirmed, error, empty. |
| Integration | n/a — no backend surface changes. |
| E2E | No socket and no mic on the route; held English absent from the DOM; confirm moves a line to the sheet; capability failure fails closed; axe light and dark. |
| Platform | Screenshots at 360, 390, 768, 1440 in both schemes. |
| Release | `npm run build` twice — the second is the diacritics gate. |

## Decisions

- DEC-0022 — the withheld gap is a positional invariant. This route inherits it.

## Harness Delta

None proposed.

## Evidence

2026-08-12, local. **Not deployed**, so platform proof is 0.

Lint clean. 79 unit tests. Production build twice, including the NFC diacritics
gate. **32 Playwright tests**, up from 24, all passing. Eight are new and cover
this route:

- *the route never opens a socket and never asks for a microphone* — `WebSocket`
  and `getUserMedia` are both instrumented before navigation; the recorded
  socket list is empty and the mic counter is 0 after a full consent → capture →
  render cycle. This is the assertion that makes a public paperwork door
  defensible, so it probes the primitives rather than trusting the imports.
- *nothing is read before the clinician consents* — no file input exists until
  consent, the start control is disabled, and the visit screen's wording is
  asserted verbatim.
- *a held dose line keeps its English out of the patient sheet* — the sheet does
  not contain `take 1 tablet`, the clinician's review pane does, and the English
  cell's left edge is measured at or right of the Vietnamese cell's right edge
  (DEC-0022, extended to this surface).
- *confirming a held line moves it onto the patient sheet* — one row before, two
  after, and the review pane empties.
- *a backend that cannot read documents says so instead of offering to try* —
  fails closed; no consent control and no file input are rendered at all.
- *the landing page offers the paperwork door* — the CTA resolves to
  `/dich-giay-to/`.
- axe clean in light and dark, at 390 and 1440, with zero horizontal overflow at
  360, 390, 768 and 1440.

**Screenshots.** `docs/qa-evidence/cp-ux-19-{light,dark}-{360,390,768,1440}-paperwork.png`

**Reused, not rebuilt.** `DocumentCapture`, `DocumentReview`, `startVisit`,
`confirmTurn`, `isGated`, `spokenText`, `riskLabel`, `useDemoCapability`, the
shared register and `.p-cta`. The only change to an existing component is two
optional callbacks on `DocumentCapture` (`onStart`, `onFail`) so a caller that
owns the whole screen can render the long wait; the visit screen passes neither
and is unaffected.

**Shared primitive moved.** The `.p-reg` register family, `.p-mark`, `.p-ord`,
`.p-indent`, `.p-held`, `.p-lede`, `.p-wrap` and `.p-cta` moved from
`landing.css` to `styles.css`. Vite bundles every stylesheet into one file, so
the old arrangement worked by accident; a new surface should not have to import
the landing's composition to get a button.

**One change reverted after the tests disagreed with it.** CP-UX-19 initially
hid a demo hub panel that renders with no usable control, on the reading that a
heading with nothing to click looks broken. `demo-hub.spec.ts` asserts the
opposite on purpose — the panel names a capability and then refuses to fake it,
which is the basis of this product's credibility. The change was reverted and
the reasoning left in the code so it is not re-attempted.

**One pre-existing flake fixed.** *a visitor sees the limits before running
anything* compared two `boundingBox()` readings taken a round-trip apart, and
`html { scroll-behavior: smooth }` moved the second one at random — it failed
in roughly one run in three. The assertion is unchanged; the measurement is now
a single document-relative `evaluate`. Five consecutive isolated runs pass.

**Impeccable detector: 3 findings, unchanged.** All three are the dead
`ScribeShowcase` rulesets in `styles.css`; this route adds none. They belong to
CP-MNT-01.

## Owner actions still required

1. Deploy — push to `origin/main`.
2. Set the Space to `PROVIDER_MODE=ckey` with `LLM_API_KEY`. Until then this
   route fails closed with `Chưa đọc được giấy tờ` rather than reading anything,
   and `/thu-nghiem/` can only run the scripted prescription.
