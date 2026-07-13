# Overview

## Current Behavior

The Scribe runtime, public site, and root test suite are under `apps/api/`,
`site/`, and `tests/`; the root package imports `carepath`.

## Target Behavior

They are under `scribe/carepath`, `scribe/frontend`, and `scribe/tests` while
the import name, public routes, root distribution, and clinical behavior remain
unchanged.

## Affected Users

- Developers and deployment operators; user-facing routes are frozen.

## Affected Product Docs

- `docs/product/ai-scribe.md`
- `docs/product/carepath-suite.md`

## Non-Goals

- Scribe API, ASR, LLM, audio, copy, or workflow changes.
