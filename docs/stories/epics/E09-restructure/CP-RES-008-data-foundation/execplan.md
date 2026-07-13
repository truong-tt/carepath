# Exec Plan

## Goal

Make the existing GEC pipeline reproducible and refuse unapproved data before
training, while adding a frozen safety-oriented text evaluation set.

## Scope

In scope:

- JSON run configs with fixed seeds.
- Manifest validation before `train`.
- Frozen stratified fixture and per-category evaluation output.

Out of scope:

- Clinical-data collection, consent approval, de-identification, model training,
  or SOAP-model work.

## Risk Classification

Risk flags:

- Clinical-data governance and validation policy.

Hard gates:

- Unapproved manifests block training before a model subprocess.
- Frozen fixture contains no audio or patient identifiers.

## Work Phases

1. Characterize pipeline/config/profile flow.
2. Add manifest and config loaders.
3. Add frozen text-only fixture and category metrics.
4. Prove the gate, then run regression suites.
