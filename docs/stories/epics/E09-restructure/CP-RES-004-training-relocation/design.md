# Design

## Domain Model

No runtime domain or clinical data changes. The training module is not a
distribution; its scripts and tests add `scribe/training/` and `scribe/` to `sys.path`.

## Application Flow

Training imports `gec.*` from `scribe/training/gec` and may import `carepath` only for
existing ASR/config helpers. Serving imports neither `gec` nor `training`.

## Interface Contract

Frozen: all public routes, exported bundle schema, and `LLM_PROVIDER=gec_local`
loading behavior.

## Data Model

No dataset or persistence change.

## UI / Platform Impact

Generated notebooks move under `scribe/training/notebooks` and are rebuilt from the
moved script. CI rejects new direct `gec` imports inside `scribe/`.

## Observability

Root tests without training extras prove serving independence; focused training
tests with the existing environment prove the moved research imports.

## Alternatives Considered

1. Leave research modules inside the serving package.
2. Split a new `gec_runtime` package from research code.
