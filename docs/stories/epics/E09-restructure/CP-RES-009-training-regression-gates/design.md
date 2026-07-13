# Design

## Baseline

`scribe/training/configs/frozen-baseline-v1.json` identifies the hashed 12-row fixture
and raw-ASR column. `scribe/training/scripts/baseline_report.py` generates or verifies
the committed report exactly, including WER and stratified drug-name, dosage,
and diacritic metrics.

## Gate

The normal report gate remains responsible for validation/hard splits. The
pipeline then predicts the frozen text fixture with the adapter and applies a
second gate before export. It compares `drug_name.term_recall` and
`dosage.number_unit_preservation` to raw ASR with zero regression tolerance.

## CI Fixture Slice

The `training-governance` job is CPU-only and runs all `scribe/training/tests`, which
exercise the full 12-row fixture. Its export smoke creates a fake adapter,
loads the generated `serve_manifest.json`, and corrects the first fixture row
through the existing injected generator. CI then verifies the committed
baseline report without writing it.
