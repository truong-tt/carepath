# Design

## Domain Model

One anonymous rating row has a pseudonymous note ID, pseudonymous clinician
ID, three bounded scores, review timestamp, and final disposition. The schema
contains no clinical source material.

## Application Flow

An in-house reviewer exports anonymous score-only rows from an approved local
review environment and runs `validate_soap_ratings.py` locally. The summary
reports the number of unique notes, mean scores, serious hallucinations, and
unsafe dispositions. It has no readiness result or decision threshold.

## Data Model

`rating-template.csv` is header-only. The real export must stay outside the
repository and the validator rejects non-approved columns, preventing an
accidental note-text field from becoming part of the workflow.

## Observability

The CLI prints a JSON summary only; it never writes, logs, or uploads ratings.

## Alternatives Considered

1. Use synthetic or already-approved de-identified material for in-house
   testing.
2. Store full notes and audio beside the code.
3. Change the model based on in-house measurements alone.

The first option is accepted for bounded in-house testing. The latter options
are rejected because they would create privacy or safety risk.
