# CP-UX-11 Problem-Led Scribe Onboarding

## Status

implemented

## Lane

normal

## Product contract

The public site is Vietnamese-only and starts with the documentation burden a
doctor recognizes. It teaches the available Ghi chép bệnh án AI workflow with a
small self-calculator and a safe guided sample before asking the visitor to
upload audio or contact the pilot team.

Phiên dịch khám bệnh trực tiếp remains a non-interactive development status.

## Scope

- Compact the public landing page and remove the VI/EN control.
- Add a four-question, browser-only documentation-time calculator.
- Reuse the existing Scribe showcase for a guided sample that never invents an
  assessment or plan.
- Put upload instructions and the upload control on the same Scribe tool screen.
- Keep the pilot form Scribe-only and secondary to the working product action.

No backend, API, audio processing, consent, retention, Interpreter, WebSocket,
TTS, or clinical safety behavior changes.

## Acceptance criteria

- The hero says `Dành thời gian cho người bệnh, không phải cho việc gõ bệnh án.`
  and its first action opens the guided sample.
- The site contains no public English-language toggle or English-first product
  label.
- A visitor can calculate current daily documentation time without a CarePath
  savings claim or network request.
- The sample explains conversation, clarified transcript, structured draft, and
  clinician review; Assessment and Plan remain for the doctor to complete.
- The real Scribe route shows instructions and the audio upload control together
  without an extra continue gate.
- Interpreter status remains visible, non-interactive, and its public routes
  remain 404.
- Mobile, keyboard, reduced-motion, diacritics, Axe, build, Lighthouse, and
  combined-app checks pass.

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

## Proof

- unit: 45 passed
- integration: combined app 3 passed
- e2e: 8 passed at 320, 360, 390, 768, and 1440px; phone and desktop screenshots captured
- platform: lint, deploy-env 5 passed, build/NFC passed, Lighthouse 100/100/100
