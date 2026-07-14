# CP-UX-10 Scribe-Led Public Landing Story

## Status

implemented

## Lane

normal

## Product Contract

The public landing tells a Vietnamese-first story about reducing
post-consultation documentation work. Ghi chép bệnh án AI is the only active
journey. Phiên dịch khám bệnh trực tiếp is visibly in development and has no
public action.

## Relevant Product Docs

- `docs/product/carepath-suite.md`
- `docs/product/ai-scribe.md`
- `docs/product/live-interpreter.md`
- `docs/ux-redesign-carepath.md`

## Acceptance Criteria

- The Scribe hero, workflow, review limit, and canonical CTA are clear in
  Vietnamese without requiring knowledge of the term Scribe.
- Interpreter status is prominent, non-interactive, and does not weaken its
  existing 404 public-route contract.
- The Scribe pilot form cannot select or submit Interpreter interest.
- Mobile, keyboard, reduced-motion, diacritics, Axe, and Lighthouse gates pass.
- No backend, API, audio, consent, WebSocket, TTS, or risk behavior changes.

## Design Notes

- Editorial split hero with a 72rem title width and interface-led product visual.
- Gapless 12-by-2 bento: `7×2 + 5×1 + 5×1 = 24` cells.
- Geist remains self-hosted. GSAP supplies desktop pinning and image scale/fade;
  reduced-motion and mobile layouts remain static.
- No photography, fake testimonials, unsupported statistics, or remote assets.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Landing copy, non-interactive status, Scribe CTA, Scribe-only form |
| E2E | Responsive layout, keyboard, Axe, reduced motion, Scribe route |
| Platform | Build, diacritics, Lighthouse, Vercel production and live routes |
| Regression | Combined-app Scribe 200 and Interpreter 404 route tests |

## Harness Delta

Add this story to the local Harness, record the real proof results, and finish
with a trace. No new Harness capability is required.

## Evidence

- Frontend lint passed; Vitest passed 46 tests across 10 files.
- Deploy-environment validation passed 5 tests; the production build and
  Vietnamese NFC/diacritics gate passed.
- Playwright passed 5 flows across 320, 360, 390, 768, and 1440px, including
  hero line limits, overflow, keyboard access, Axe, reduced motion, and the
  canonical Scribe route.
- The combined FastAPI route proof passed 3 tests under the repository Python
  3.12 environment, including Scribe availability and Interpreter 404s.
- Lighthouse scored 100 performance, 100 accessibility, and 100 best practices.
- No interactive browser was connected for separate desktop/phone visual
  capture, so that manual visual gate remains explicitly unverified.
