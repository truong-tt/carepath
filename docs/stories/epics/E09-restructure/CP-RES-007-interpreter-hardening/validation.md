# Validation

## Proof Strategy

Focused tests prove constant-time comparison invocation, CSV configuration, and
one daily purge iteration. Existing app, risk-evaluation, and frontend suites
prove unchanged runtime behavior.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Admin comparison, CORS parsing, daily purge loop |
| Integration | Standalone and combined FastAPI lifespans |
| E2E | Existing console and public-site regressions |
| Platform | Docker build when a provider is registered |

## Commands

```powershell
python -m pytest interpreter/tests/test_health.py interpreter/tests/test_api.py scribe/tests/test_combined_app.py
cd interpreter; ruff check .; pytest
python interpreter/eval/run_eval.py --set interpreter/eval/fixtures/eval_starter.tsv --providers mock
```

## Acceptance Evidence

2026-07-13:

- Focused hardening proof passed: 21 tests cover the shared lifecycle,
  constant-time admin comparison, CSV CORS parsing, and one daily purge loop.
- Root serving tests passed: 54 passed; keyless Scribe smoke passed; generated
  term-artifact drift check passed.
- Interpreter `ruff check .` passed; 112 tests passed, 1 skipped; the 50-row
  mock safety eval stayed at 100% for risk, escalation, and preservation.
- Interpreter console: 38 unit tests, build, and 4 Playwright checks passed.
- Public site: 45 unit tests, 5 deploy-environment checks, diacritics build,
  and 7 Playwright checks passed.
- `AGENTS.md` now freezes Interpreter work to bugfix, safety, and required
  operations changes unless the owner reopens feature work.
- Docker validation was skipped because the Harness registry has no present
  `container-build` provider.
