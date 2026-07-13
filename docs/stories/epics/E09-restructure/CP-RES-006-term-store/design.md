# Design

## Domain Model

Each canonical row contains `term_vi`, `term_en`, `kind`, `aliases`,
`risk_flags`, and ordered target mappings. Target metadata preserves the
different existing Scribe category/Vietnamese surface and Interpreter CSV
schema without runtime code changes.

## Interface Contract

Scribe continues reading `data/medical_lexicon.json`; Interpreter continues
reading `interpreter/app/glossary/data/seed_glossary.csv`.

## Observability

`scripts/build_term_artifacts.py --check` reports stale generated artifacts;
CI regenerates and rejects any diff.

## Alternatives Considered

1. Change both runtimes to read a new common schema.
2. Keep two independently authored files.
