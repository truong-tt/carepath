# Validation

## Proof Strategy

The generator must reproduce both tracked artifacts from canonical data; the
existing Scribe retrieval and Interpreter safety suites prove runtime use.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Source schema and generated-artifact drift check |
| Integration | Scribe retrieval and Interpreter glossary tests |
| E2E | Existing console and public-site regressions |
| Platform | Docker build when a provider is registered |

## Commands

```powershell
python scripts/build_term_artifacts.py --check
python -m pytest shared/tests scribe/tests interpreter/tests
python interpreter/eval/run_eval.py --set interpreter/eval/fixtures/eval_starter.tsv --providers mock
```

## Acceptance Evidence

2026-07-13:

- Canonical source contains 192 terms with 35 Scribe and 165 Interpreter
  target mappings; it regenerates both serving artifacts without a diff.
- Shared source/artifact tests passed: 52 passed; `ruff check shared
  scripts/build_term_artifacts.py` passed.
- Root serving tests passed: 54 passed; keyless Scribe smoke passed.
- Interpreter `ruff check .` passed; 109 tests passed, 1 skipped; the 50-row
  mock safety eval stayed at 100% for risk, escalation, and preservation.
- Interpreter console: 38 unit tests, build, and 4 Playwright checks passed.
- Public site: 45 unit tests, 5 deploy-environment checks, diacritics build,
  and 7 Playwright checks passed.
- Docker validation was skipped because the Harness registry has no present
  `container-build` provider.
