# CP-BASE-002 Live Interpreter Safety

## Status

implemented

## Lane

high-risk

## Product Contract

The live interpreter remains translation-only, consent-gated, confidence-aware,
and fail-closed for patient display and TTS.

## Relevant Product Docs

- `docs/product/live-interpreter.md`

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit and integration | `cd interpreter; python -m pytest` |
| Safety regression | `python interpreter/eval/run_eval.py --set interpreter/eval/fixtures/eval_starter.tsv --providers mock` |
| E2E | `cd interpreter/frontend; npx playwright test` |

## Evidence

2026-07-12: Ruff passed; backend tests reported 109 passed and 1 skipped; the
50-row mock eval reported 100% risk accuracy, escalation correctness, and all
preservation metrics; 4 console browser tests passed.
