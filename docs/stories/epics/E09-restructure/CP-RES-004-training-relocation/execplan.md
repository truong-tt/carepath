# Exec Plan

## Goal

Move GEC research assets out of the serving tree while preserving imports and
exported-model compatibility.

## Scope

In scope:

- Move GEC code, scripts, notebooks, and GEC-focused tests with Git history.
- Rename research imports from `carepath.gec.*` to `gec.*`.
- Rebuild generated notebooks and add the CI serving-import guard.

Out of scope:

- Training new models, changing training algorithms, or changing serving APIs.

## Risk Classification

Risk flags:

- Serving/training architecture boundary and validation policy.

Hard gates:

- Root serving tests must pass without training extras.
- `scribe/` must contain no direct `gec` import.
- Export bundle contract remains unchanged.

## Work Phases

1. Record high-risk intake.
2. Move training assets with `git mv`.
3. Repair imports and path math, then regenerate notebooks.
4. Add the CI import-boundary guard.
5. Run serving and focused training proof; record the actual outcome.

## Stop Conditions

Pause if moving code requires a serving import from `scribe/training/`, a new runtime
dependency, or a bundle-schema change.
