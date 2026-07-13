# Exec Plan

## Goal

Provide an optional, privacy-bounded in-house SOAP quality review tool.

## Scope

In scope:

- Rubric and blank score-only schema.
- Standard-library validation and summary.
- Product contract that keeps in-house results informational.

Out of scope:

- Clinical-data collection or storage in this repository, or model changes.

## Risk Classification

Risk flags:

- Clinical data, privacy, and model-quality decision policy.

Hard gates:

- No source material enters the repository.
- The summary has no minimum sample-size or model-readiness result.
- No model, provider, or safety-policy change follows from in-house results
  without a separate owner decision.

## Work Phases

1. Define the minimum score-only schema and rubric.
2. Validate bounded scores and summarize anonymous review metadata.
3. Document the in-house scope and stop conditions.
4. Prove the validator with synthetic in-memory test rows only.

## Stop Conditions

Pause for owner direction if any request would add patient data, audio,
transcripts, or note text to this repository, or use in-house results to
change a model, provider, or safety policy.
