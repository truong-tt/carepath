# 0013 GEC Training Data Governance

Date: 2026-07-13

## Status

Accepted

## Context

GEC training previously accepted a dataset name and profile without a durable
record of its source, consent status, immutable version, or deterministic run
configuration. Clinical audio is sensitive personal data and cannot be sourced
or approved by an agent.

## Decision

Use versioned JSON run configs with fixed seeds and a dataset-manifest reference.
`run_pipeline.py` refuses every training stage until the referenced manifest has
owner-approved consent and a non-placeholder SHA-256. Add a text-only frozen
stratified evaluation fixture with a separate immutable hash; it contains no
patient audio or identifiers.

## Consequences

- The agent can validate pipeline governance without collecting clinical data.
- The owner must complete lawful sourcing, consent, de-identification, and hash
  verification before a real training run.
- Evaluation categories make drug, dosage, laterality, negation, number, and
  diacritic regressions visible independently.
