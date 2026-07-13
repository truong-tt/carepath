# Validation

## Proof Strategy

Validate serving without training extras, then run focused GEC tests when the
existing local environment has their dependencies.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Root serving tests and focused training tests |
| Integration | Keyless Scribe smoke and GEC import boundary |
| E2E | Existing console and site suites |
| Platform | Generated notebook imports |

## Fixtures

- Existing deterministic GEC test fixtures.
- Export manifest fixture in `scribe/tests/test_gec_local.py`.

## Commands

```text
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe scripts\smoke_backend.py
.venv\Scripts\python.exe -m pytest scribe/training/tests
.venv\Scripts\python.exe scribe/training/scripts/build_notebooks.py
rg -l "from gec|import gec" scribe/
```

## Acceptance Evidence

2026-07-13:

- Rebuilt all four generated notebooks from `scribe/training/scripts/build_notebooks.py`.
- Root serving proof passed without training extras: 54 passed.
- Keyless Scribe smoke passed.
- Focused training tests passed: 41 passed, 1 skipped.
- `scribe/` contains no `from gec` or `import gec` lines.
- Interpreter tests passed: 109 passed, 1 skipped; `ruff check .` passed.
- Interpreter safety eval remained 100% across all 50 rows.
- Interpreter console: 38 unit tests, production build, and 4 Playwright checks passed.
- Public site: 45 unit tests, deploy-environment validation, production build
  including the diacritics gate, and 7 Playwright checks passed.
- Docker validation was skipped because the Harness tool registry has no
  present container-build provider.
