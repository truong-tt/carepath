# Overview

## Current Behavior

The Scribe produces a clinician-reviewed SOAP draft. The repository now has a
bounded review tool, but current work is limited to in-house testing.

## Target Behavior

The repository provides an optional score-only rubric, blank schema, and
validator for informational in-house review. It has no minimum sample-size
target and cannot authorize a model change.

## Affected Users

- In-house reviewers.

## Affected Product Docs

- `docs/product/ai-scribe.md`

## Non-Goals

- Collect source audio, patient data, generated note text, or ratings in this
  repository.
- Train, fine-tune, or change the SOAP serving provider.
