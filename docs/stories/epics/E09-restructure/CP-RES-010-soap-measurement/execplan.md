# Exec Plan

## Goal

Prepare an owner-led, de-identified measurement gate for SOAP quality.

## Scope

In scope:

- Rubric and blank score-only schema.
- Standard-library validation and summary.
- Product contract that prevents premature fine-tuning.

Out of scope:

- Clinical-data collection, storage, rating, or model changes.

## Risk Classification

Risk flags:

- Clinical data and model-quality decision policy.

Hard gates:

- No source material enters the repository.
- At least 50 distinct notes must be rated before the owner decides whether to
  change the model.

## Work Phases

1. Define the minimum score-only schema and rubric.
2. Validate bounded scores and the unique-note threshold.
3. Document owner prerequisites and stop conditions.
4. Prove the validator with synthetic in-memory test rows only.

## Stop Conditions

Pause for owner direction if any request would add patient data, audio,
transcripts, or note text to this repository.
