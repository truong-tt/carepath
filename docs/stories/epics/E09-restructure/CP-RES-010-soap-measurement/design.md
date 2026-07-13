# Design

## Domain Model

One anonymous rating row has a pseudonymous note ID, pseudonymous clinician
ID, three bounded scores, review timestamp, and final disposition. The schema
contains no clinical source material.

## Application Flow

The owner exports anonymous score-only rows from the approved review
environment and runs `validate_soap_ratings.py` locally. The summary reports
the number of unique notes, mean scores, serious hallucinations, unsafe
dispositions, and whether the 50-note decision threshold is met.

## Data Model

`rating-template.csv` is header-only. The real export must stay outside the
repository and the validator rejects non-approved columns, preventing an
accidental note-text field from becoming part of the workflow.

## Observability

The CLI prints a JSON summary only; it never writes, logs, or uploads ratings.

## Alternatives Considered

1. Use synthetic note ratings.
2. Store full notes and audio beside the code.
3. Fine-tune before clinician measurement.

All are rejected because they would create weak or unsafe evidence.
