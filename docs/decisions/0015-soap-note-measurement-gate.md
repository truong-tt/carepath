# 0015 SOAP Note Measurement Gate

Date: 2026-07-13

## Status

Superseded by [0017 In-House Testing Scope](0017-in-house-testing-scope.md)
on 2026-07-13.

## Context

The Scribe SOAP output uses a hosted clinical LLM with an offline fallback.
There is no legitimate basis to train or tune it from invented examples, and no
clinical rating protocol existed to distinguish missing content, hallucination,
and terminology errors.

## Decision

Before any SOAP fine-tuning decision, the owner must obtain at least 50
de-identified pilot notes rated by clinicians under the documented rubric.
The repository holds only a blank rating schema and a validator that accepts
anonymous rating metadata; it must never hold source audio, transcripts,
patient identifiers, or note text.

## Consequences

- The agent can make the measurement process reproducible without simulating
  clinical evidence.
- A rating summary makes serious hallucinations and unsafe dispositions visible
  to the owner before choosing training, retrieval, prompting, or no change.
- The clinical-data study, ratings, and any subsequent model decision remain
  owner-led and require an approved environment.
