# Overview

## Current Behavior

The Scribe produces a clinician-reviewed SOAP draft, but no durable protocol
exists for assessing its quality before changing the model.

## Target Behavior

The repository provides a de-identified rubric, blank schema, and validator.
The owner can collect at least 50 real clinician ratings in an approved
environment before making a tuning decision.

## Affected Users

- Clinical owner and clinician reviewers.

## Affected Product Docs

- `docs/product/ai-scribe.md`

## Non-Goals

- Collect pilot audio, patient data, generated note text, or ratings.
- Train, fine-tune, or change the SOAP serving provider.
