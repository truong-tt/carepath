# Exec Plan

## Goal

Make Scribe ownership of all offline DARAG/GEC training explicit without
changing serving behavior or the Interpreter safety harness.

## Scope

In scope:

- Relocate `training/` to `scribe/training/` with Git history preserved.
- Update path-sensitive scripts, generated notebooks, configs, tests, CI,
  packaging rules, and active documentation.
- Verify the Scribe runtime does not import the relocated `gec` package.

Out of scope:

- Model training, data collection, dependency changes, and API changes.
- Interpreter runtime or `interpreter/eval/` changes.

## Risk Classification

Risk flags:

- Architecture, packaging, CI, and training-boundary relocation.

Hard gates:

- Scribe and training tests pass.
- The deterministic baseline report passes.
- No Scribe runtime import of `gec` remains.

## Work Phases

1. Inventory root-relative paths and packaging copies.
2. Move the training directory under `scribe/`.
3. Update executable paths, configuration references, generated notebooks, CI,
   and docs.
4. Run unit, build, boundary, and baseline checks.
5. Record the real Harness validation outcome.

## Stop Conditions

Pause for human confirmation if a move requires training data migration,
changes an API contract, or forces an Interpreter dependency on Scribe code.
