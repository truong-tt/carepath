# Overview

## Current Behavior

Offline Scribe DARAG/GEC training resides at the repository root in
`training/`, despite having no Interpreter imports or runtime role.

## Target Behavior

All offline Scribe training resides at `scribe/training/`. The Interpreter
retains only `interpreter/eval/` for its safety regression harness.

## Affected Users

- Scribe maintainers running offline training, evaluation, or Colab notebooks.
- Release maintainers running CI and building the combined service image.

## Affected Product Docs

- `docs/product/ai-scribe.md`
- `docs/ARCHITECTURE.md`

## Non-Goals

- Change Scribe or Interpreter product behavior.
- Move or alter `interpreter/eval/`.
- Train a model, add dependencies, or include training artifacts in production.
