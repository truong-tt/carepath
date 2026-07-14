# CP-UX-13 Privacy and Vietnamese-Capability Visibility

## Status

implemented

## Lane

normal

Privacy hard-gate note: this story restates verified, already-shipped privacy
claims more prominently. It changes no retention, consent, microphone, or API
behavior. Every claim is grounded in `scribe/carepath/main.py` (request-scoped
`TemporaryDirectory` processing) and `docs/product/ai-scribe.md` (temporary
working storage only; consultation audio is never training data).

## Product contract

The landing makes its trust facts visible instead of buried: the hero states
that audio is not retained, and the trust section shows two evidence panels,
Vietnamese capability and audio privacy, under one heading that keeps the
clinician-review requirement and the no-advice boundary. Review is framed as
fast and targeted because corrections and gaps are marked, never as optional.

## Scope

- Extend the hero small print with the audio-retention fact.
- Replace the four-bullet trust list with capability and privacy panels,
  absorbing all previous safety statements.
- No accuracy figure, no savings promise, no suggestion to skip review.
- No route, API, backend, form, or Scribe-tool changes. No new dependency.

## Acceptance criteria

- Audio-retention fact visible in the hero without scrolling.
- Trust section shows both panels with all six verified claims plus the
  review requirement and no-advice boundary.
- No prior safety statement is lost from the page.
- CP-UX-12 gates still pass: lint, unit, deploy-env, build with diacritics,
  Playwright with axe light and dark, Lighthouse, combined-app tests.

## Validation

```powershell
cd scribe\frontend
npm.cmd run lint
npm.cmd test
npm.cmd run test:deploy-env
npm.cmd run build
npm.cmd run e2e
npm.cmd run lighthouse
cd ..\..
python -m pytest scribe/tests/test_combined_app.py
```

## Evidence

2026-07-15: lint passed; 47 unit tests passed; 5 deploy-env tests passed;
production build and NFC diacritics gate passed; 8 Playwright tests passed
(axe light and dark, responsive 320–1440, reduced motion); combined-app 3
passed; Lighthouse 100/100/100 with CLS 0. Screenshots verified the two
trust panels, extended hero small print, and intact review and no-advice
copy at desktop and mobile widths.
