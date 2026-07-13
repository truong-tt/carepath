# Validation

## Proof Strategy

Unit tests construct score-only synthetic rows in memory. No clinical material
is created or persisted.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Quality summary, serious-hallucination summary, invalid-score rejection |
| Integration | Existing CPU-only training test job discovers the validator test |
| E2E | Not applicable; no product surface changes |
| Platform | No external provider required |

## Commands

```powershell
python -m pytest scribe/training/tests
python -m ruff check scribe/training/scripts/validate_soap_ratings.py scribe/training/tests/test_soap_ratings.py
```

## Acceptance Evidence

2026-07-13: `python -m pytest scribe/training/tests` passed with `54 passed,
1 skipped`; the review-validator focused test passed with `4 passed`, and
Ruff passed. No data collection, model training, or serving behavior change
occurred. The tool is limited to optional in-house testing and makes no model
decision claim.
