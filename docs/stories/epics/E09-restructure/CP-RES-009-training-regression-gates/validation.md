# Validation

## Commands

```powershell
python -m pytest scribe/training/tests
python scribe/training/scripts/baseline_report.py
python -m ruff check scribe/training/gec scribe/training/scripts scribe/training/tests
```

## Acceptance Criteria

- A committed report includes overall WER plus drug-name, dosage, and diacritic
  baseline metrics for the frozen fixture.
- A test proves the gate rejects a drug-name regression even if the regular
  validation and hard-split candidate scores improve.
- The real pipeline evaluates the frozen fixture and passes its safety report
  into `gate.py` before `export_serve.py`.
- CI uses only the 12-row text-only fixture, fake adapter export smoke, and no
  ML training dependencies.

## Acceptance Evidence

2026-07-13:

- `50 passed, 1 skipped` for all training tests. The optional skip is an
  existing audio/NumPy dependency test, not part of the CPU-only GEC proof.
- The committed frozen report verified exactly against its config,
  fixture hash, and deterministic metrics. It records 12 rows, raw WER
  `1.4375`, drug-name accuracy `0.0`, dosage accuracy `0.0`, and diacritics
  accuracy `0.0`; these are baseline measurements, not quality targets.
- A unit test proved the gate rejects a drug-name regression even while the
  regular validation/hard metrics improve. The export smoke loaded a generated
  serve manifest and corrected one frozen-fixture sentence via the injected
  generator, without loading a real adapter.
- Full regressions passed: root `54 passed` and mock smoke; Interpreter Ruff,
  `112 passed, 1 skipped`, and 50-row mock safety evaluation at 100%; console
  `38 passed` plus 4 Playwright tests; site `45 passed`, 5 deploy-env tests,
  build/diacritics, and 7 Playwright tests.
- Docker is a clean skip: the Harness has no registered `container-build`
  provider.
