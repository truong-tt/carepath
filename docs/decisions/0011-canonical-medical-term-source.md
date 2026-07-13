# 0011 Canonical Medical-Term Source

Date: 2026-07-13

## Status

Accepted

## Context

Scribe retrieval reads `data/medical_lexicon.json`; Interpreter safety glossary
seeding reads `interpreter/app/glossary/data/seed_glossary.csv`. Both are
clinician-editable medical terminology, but their serving schemas differ.

## Decision

`shared/carepath_shared/terms/medical_terms.json` is the only authored source.
Each row defines Vietnamese and English terms, kind, aliases, risk flags, and
target-specific rendering metadata. `scripts/build_term_artifacts.py` emits
both existing serving artifacts without changing either runtime reader.

Interpreter risk lexicons remain independent safety data and are explicitly
out of scope for this source.

## Consequences

- Serving paths and schemas stay stable.
- CI regenerates artifacts and rejects source/artifact drift.
- Any taxonomy or risk-flag meaning change now requires this decision's
  characterization and safety proof to be revisited.
