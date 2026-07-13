# Validation

## Proof Strategy

Unit proof validates manifests, fixed seeds, pre-training refusal, fixture hash,
and every category. Existing Scribe/Interpreter regressions prove no serving
impact.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Manifest, config, fixture hash, category reports |
| Integration | `run_pipeline --stage train` refuses unapproved data |
| E2E | Existing console and public-site regressions |
| Platform | Docker build when a provider is registered |

## Commands

```powershell
python -m pytest scribe/training/tests/test_governance.py scribe/training/tests/test_gec.py
python scribe/training/scripts/run_pipeline.py --stage train
python scribe/training/scripts/evaluate.py --input scribe/training/eval/fixtures/gec_eval_v1.jsonl --prediction-columns raw_asr
```

## Acceptance Evidence

2026-07-13:

- `32 passed` for `scribe/training/tests/test_governance.py` and
  `scribe/training/tests/test_gec.py`; Ruff passed for the changed training modules.
- The frozen fixture evaluates deterministically: 12 text-only rows, two each
  for diacritics, dosage, drug name, laterality, negation, and numbers. Its
  manifest hash was verified by the test suite.
- `run_pipeline.py --config scribe/training/configs/smoke-v1.json --stage train`
  stopped before starting a model subprocess with the expected
  `owner-approved consent` failure. No clinical data was collected or trained.
- Full regressions passed: root `54 passed` and mock smoke; Interpreter Ruff,
  `112 passed, 1 skipped`, and a 50-row mock safety evaluation at 100%; console
  `38 passed` plus 4 Playwright tests; site `45 passed`, 5 deploy-env tests,
  build/diacritics gate, and 7 Playwright tests.
- Docker remains an explicit clean skip because no `container-build` provider
  is registered in the Harness tool registry.
