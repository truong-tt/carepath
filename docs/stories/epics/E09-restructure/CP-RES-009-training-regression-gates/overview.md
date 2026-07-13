# Overview

## Current Behavior

The GEC fixture has deterministic per-category metrics, but no committed
baseline report or export-blocking gate for drug and dosage regressions.

## Target Behavior

`scribe/training/reports/` contains a reproducible frozen baseline. A real adapter
evaluation must pass both the existing aggregate gate and the safety-weighted
frozen-fixture gate before `export_serve.py` runs.

## Non-Goals

- Train a model, source clinical data, or change Scribe serving behavior.
- Add torch, CUDA, or an external provider to CI.
