# Validation

## Proof Strategy

Run the current root, Interpreter, console, and site matrix after correcting
all relocation paths. Docker is attempted only when a container-build provider
is registered.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Root, Interpreter, console, and site unit suites |
| Integration | Keyless smoke and Interpreter mock eval |
| E2E | Interpreter and site Playwright suites |
| Platform | Docker build and keyless health endpoints if available |

## Fixtures

- Root Scribe fixtures and `data/medical_lexicon.json`
- `interpreter/eval/fixtures/eval_starter.tsv`

## Commands

```text
python -m pytest
python scripts/smoke_backend.py
cd interpreter; python -m pytest; ruff check .
python interpreter/eval/run_eval.py --set interpreter/eval/fixtures/eval_starter.tsv --providers mock
cd interpreter/frontend; npm test; npm run build; npx playwright test
cd scribe/frontend; npm test; npm run build; npm run e2e
```

## Acceptance Evidence

2026-07-13:

- Editable installs passed for the root Scribe distribution and `interpreter/`.
- Root tests passed: 95 passed, 1 skipped; keyless Scribe smoke passed.
- Interpreter tests passed: 109 passed, 1 skipped; `ruff check .` passed.
- Interpreter mock eval passed with 100% risk accuracy, escalation correctness,
  and preservation metrics across 50 rows.
- Interpreter console: 38 unit tests, production build, and 4 Playwright
  checks passed.
- Public site: 45 unit tests, deploy-environment validation, production build
  including the diacritics gate, and 7 Playwright checks passed.
- The production static route check passed at `/phien-dich-y-khoa/`.
- Docker validation was skipped because the Harness tool registry has no
  present container-build provider.

Owner follow-up: change the Vercel project Root Directory to `scribe/frontend`.
