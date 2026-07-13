# 0017 In-House Testing Scope

Date: 2026-07-13

## Status

Accepted

## Context

The restructure and public deployment work are complete. The remaining
50-note clinician-rating target in decision 0015 would require an external
clinical-evidence program that is outside the current in-house testing scope.

## Decision

Remove the 50-note clinician-rating target from the restructure completion
criteria and from the SOAP review utility. In-house review is optional and
informational: it may inspect synthetic or already-approved de-identified
material with the existing score-only rubric, but it cannot authorize a SOAP
fine-tuning, provider, or safety-policy change.

No audio, transcript, patient identifier, or note text may enter this
repository. A future clinical-evidence program or model decision requires a
separate owner decision.

## Consequences

- The restructure can complete without external clinical-rating evidence.
- The rubric remains available for bounded in-house quality checks, without a
  minimum sample-size goal or readiness result.
- CarePath makes no clinical-quality or model-readiness claim from in-house
  testing.

## Alternatives Considered

1. Keep the 50-note gate: rejected because it conflicts with the current
   owner-directed in-house scope.
2. Delete the rubric and validator: rejected because they remain useful for
   privacy-bounded internal QA.
