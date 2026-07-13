# Design

## Domain Model

A dataset manifest has ID, source description, consent status, and SHA-256.
A pipeline config references it and carries all profile/run-size values,
including fixed seeds. The train stage validates the manifest before executing
any subprocess.

## Application Flow

Existing data → synthesize → train → evaluate → export stages remain intact.
`--profile` now selects a versioned config by default; `--config` supports an
explicit approved run file.

## Data Model

The frozen evaluation JSONL is text-only and category-tagged. Its manifest hash
protects fixture drift. No raw audio field or data collection is introduced.

## Alternatives Considered

1. Add consent text to notebook instructions only.
2. Gate every preliminary data stage rather than only model training.
3. Train on an unapproved public-dataset reference.
