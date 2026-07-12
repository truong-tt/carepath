# GEC-001 Remove Human-Labeling Workflow

## Status

implemented

## Lane

normal

## Product Contract

The offline GEC training pipeline uses ViMedCSS real pairs and synthetic pairs
only. It does not include Label Studio tooling or clinician-corrected export
ingestion.

## Relevant Product Docs

- `docs/ARCHITECTURE.md`

## Acceptance Criteria

- No Label Studio, local labeling, or labeled-pair producer remains in the
  repository.
- The GEC data model still supports generic `raw_asr` and `gold_text` pairs.
- The pipeline, generated notebooks, and tests use real ViMedCSS and synthetic
  paths only.

## Validation

| Layer | Expected proof |
| --- | --- |
| Static | Focused Ruff check and zero-reference scan |
| Integration | `python -m pytest tests/test_gec.py` |
| Release | Root `python -m pytest` |

## Evidence

2026-07-12: notebook generation passed; focused Ruff passed; 26 focused GEC
tests passed; the root suite reported 95 passed and 1 skipped. The final scan
found no Label Studio, local-labeling, or labeled-pair references.
