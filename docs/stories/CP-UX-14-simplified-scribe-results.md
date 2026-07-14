# CP-UX-14 Simplified Scribe Result Screen

## Status

implemented

## Lane

normal

## Product contract

After a Scribe request completes, the doctor sees one compact review notice,
the four SOAP sections, and **Thông tin còn thiếu**. Transcript and terminology
evidence returned by the API stays hidden from this public result screen.

## Scope

- Remove transcript, corrected-transcript, terminology, and duplicate-warning presentation.
- Order the remaining content as review notice, SOAP, then missing information.
- Preserve processing time, SOAP-only copy, new-draft action, safe rich text,
  API response compatibility, and existing empty states.
- No backend, audio, prompt, model, route, dependency, or API-schema changes.

## Acceptance criteria

- The result renders `Bản nháp SOAP — cần bác sĩ kiểm tra` exactly once.
- SOAP S/O/A/P content is visible before **Thông tin còn thiếu**.
- Transcript and term labels and values are absent even when present in the response.
- Empty SOAP and missing-information states remain visible and accurate.
- Unit, build/NFC, accessibility, responsive browser, and combined-route checks pass.

## Validation

```powershell
npm.cmd --prefix scribe/frontend run lint
npm.cmd --prefix scribe/frontend test
npm.cmd --prefix scribe/frontend run test:deploy-env
npm.cmd --prefix scribe/frontend run build
npm.cmd --prefix scribe/frontend run e2e
python -m pytest scribe/tests/test_combined_app.py
```

## Evidence

2026-07-15: lint passed; 47 unit tests passed; five deployment-environment
tests passed; production build and NFC gate passed; eight Playwright tests
passed with mobile/desktop result screenshots and Axe checks; combined-app
route tests passed on Python 3.12. Production verification is recorded in the
Harness trace after deployment.
