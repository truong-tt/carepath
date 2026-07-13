# Validation

## Proof Strategy

The characterization suite proves each original contract. Existing Interpreter
fixtures and evaluation prove safety behavior is unchanged.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | 50 Vietnamese clinical normalization cases across all contracts |
| Integration | Scribe, Interpreter, and training focused tests |
| E2E | Existing frontend regressions |
| Platform | Docker build when a registered provider is available |

## Commands

```powershell
python -m pytest shared/tests scribe/tests interpreter/tests scribe/training/tests
python interpreter/eval/run_eval.py --set interpreter/eval/fixtures/eval_starter.tsv --providers mock
```

## Acceptance Evidence

2026-07-13:

- Editable `carepath-shared`, root Scribe, and Interpreter installs succeeded.
- The 50-case characterization suite plus focused Scribe, Interpreter, and
  training tests passed: 143 passed.
- Root serving tests passed: 54 passed; keyless Scribe smoke passed.
- Interpreter `ruff check .` passed; 109 tests passed, 1 skipped; the 50-row
  mock safety eval stayed at 100% for risk, escalation, and preservation.
- Interpreter console: 38 unit tests, build, and 4 Playwright checks passed.
- Public site: 45 unit tests, 5 deploy-environment checks, diacritics build,
  and 7 Playwright checks passed.
- The implementation scan finds `fold_for_match`, `normalize_text`, and
  `normalize_for_match` definitions only in `shared/carepath_shared/normalize.py`.
- Docker validation was skipped because the Harness registry has no present
  `container-build` provider.
