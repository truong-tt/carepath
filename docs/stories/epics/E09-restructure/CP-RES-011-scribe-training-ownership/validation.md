# Validation

## Proof Strategy

Use the existing CPU-only training suite and deterministic baseline report,
then prove the serving and Interpreter boundaries remain separate.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Relocated GEC and SOAP measurement tests |
| Integration | Deterministic baseline report and generated notebooks |
| E2E | Not applicable; no product UI or route changes |
| Platform | Scribe package build and Docker copy-boundary inspection |
| Boundary | No `gec` import in `scribe/carepath/`; no Interpreter move |

## Fixtures

Existing source-controlled DARAG fixtures, manifests, reports, and blank SOAP
rating schema only. No clinical data is used.

## Commands

```powershell
python -m pytest scribe/training/tests
python scribe/training/scripts/build_notebooks.py
python scribe/training/scripts/baseline_report.py
python -m pytest scribe/tests
python -m ruff check scribe/training scribe/carepath
```

## Acceptance Evidence

2026-07-13: all source-controlled training assets moved to
`scribe/training/`, and generated notebooks were rebuilt from their relocated
generator. The project Python 3.12 proof passed: 54 training tests with one
optional skip, 106 Scribe/shared tests, Ruff for the Scribe runtime and training
tree, the frozen baseline report, and the mock Scribe smoke flow. Searches found
no `gec` import in `scribe/carepath/` and no Interpreter import in
`scribe/training/`. Docker build is a clean skip because Harness has no
registered container-build provider; its runtime copy boundary was inspected
and copies only `scribe/carepath/`.
