# CP-BASE-001 Unified API and Ghi chép bệnh án AI

## Status

implemented

## Lane

normal

## Product Contract

The combined FastAPI service keeps the Scribe health and note-drafting path
available while preserving clinician review of generated output.

## Relevant Product Docs

- `docs/product/ai-scribe.md`

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit and integration | `python -m pytest` |
| Release smoke | `python scripts/smoke_backend.py` |

## Evidence

2026-07-12: 96 passed, 1 skipped in the root suite; the mock ASR and offline
LLM smoke test passed.
