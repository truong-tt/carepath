# Overview

## Current Behavior

GEC research code is physically inside the Scribe serving package despite the
serving runtime not importing it. Scripts, generated notebooks, and three
training tests live outside that package.

## Target Behavior

GEC research code, scripts, notebooks, and training tests live under
`scribe/training/`. Serving remains `scribe/carepath`, retains no `gec` import, and
continues loading only exported adapter bundles.

## Affected Users

- Developers and ML operators; runtime clinical behavior is unchanged.

## Affected Product Docs

- `docs/product/ai-scribe.md`

## Non-Goals

- Changing serving behavior, GEC algorithms, models, dependencies, or data.
