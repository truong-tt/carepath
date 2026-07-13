# Validation

## Proof Strategy

Use the current combined-api, Interpreter safety, console, and static-site
checks. Docker build is attempted only when the local container provider is
available.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Root suite, Interpreter suite, both frontend unit suites |
| Integration | Keyless Scribe smoke and Interpreter mock eval |
| E2E | Interpreter and site Playwright suites |
| Platform | Docker build; keyless health endpoints if the provider is available |

## Fixtures

- `interpreter/eval/fixtures/eval_starter.tsv`
- `interpreter/eval/fixtures/risk_cases.jsonl`

## Commands

```text
python -m pytest
python scripts/smoke_backend.py
cd interpreter; python -m pytest; ruff check .
python interpreter/eval/run_eval.py --set interpreter/eval/fixtures/eval_starter.tsv --providers mock
cd interpreter/frontend; npm test; npm run build; npx playwright test
cd scribe/frontend; npm test; npm run build; npm run e2e
docker build -t carepath .
```

## Acceptance Evidence

2026-07-13:

- Editable installs passed for the root Scribe distribution and `interpreter/`.
- Root tests passed: 95 passed, 1 skipped.
- Keyless Scribe smoke passed.
- Interpreter tests passed: 109 passed, 1 skipped; `ruff check .` passed.
- Interpreter mock eval passed with 100% risk accuracy, escalation correctness,
  and preservation metrics across 50 rows.
- Interpreter console: 38 unit tests, production build, and 4 mock-mode
  Playwright checks passed.
- Public site: 45 unit tests, deploy-environment validation, production build
  including the diacritics gate, and 7 Playwright checks passed.
- Docker validation was skipped because the Harness tool registry has no
  present container-build provider.

The optional production-base console suite reached the canonical route and
passed 3 of 4 checks; its existing phone-width overflow assertion failed. No
console source changed in this relocation, so it is recorded as follow-up
friction rather than changed in this path-only story.
