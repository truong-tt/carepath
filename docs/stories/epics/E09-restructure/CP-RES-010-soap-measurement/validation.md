# Validation

## Proof Strategy

Unit tests construct score-only synthetic rows in memory. No clinical material
is created or persisted.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | 50-note threshold, serious-hallucination summary, invalid-score rejection |
| Integration | Existing CPU-only training test job discovers the validator test |
| E2E | Not applicable; no product surface changes |
| Platform | No external provider required |

## Commands

```powershell
python -m pytest scribe/training/tests
python -m ruff check scribe/training/scripts/validate_soap_ratings.py scribe/training/tests/test_soap_ratings.py
```

## Acceptance Evidence

2026-07-13: focused proof passed with `38 passed`; no data collection, model
training, or serving behavior change occurred. The owner has not yet supplied
the required pilot data or clinical ratings, so no model decision is claimed.
