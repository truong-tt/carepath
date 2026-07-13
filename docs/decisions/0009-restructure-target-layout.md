# 0009 CarePath Restructure Target Layout

Date: 2026-07-13

## Status

Superseded in part by 0016

> Location update (2026-07-13): the approved Scribe training boundary now
> resides at `scribe/training/`. The remaining Interpreter and shared-layout
> decisions in this record remain accepted.

## Context

CarePath serves two independent clinical workflows from one process, while the
repository currently places their runtime, frontends, tests, evaluation, and
training assets in mixed top-level locations. The approved restructure requires
a durable target layout without changing import names, routes, or safety
behavior.

## Decision

Move runtime ownership into `scribe/` and `interpreter/`, and reserve `shared/`
for the later shared package. Decision 0016 supersedes this record's original
top-level GEC-training location. Keep the import names `carepath` and `app`,
keep all public routes unchanged, and retain the root `pyproject.toml` as the
Scribe distribution. Move the interpreter evaluation harness with
`interpreter/`; it is not GEC training.

Each relocation phase must update path math, packaging, CI, Docker, deployment
documentation, and the affected product contracts, then pass its relevant
existing proof before the next phase begins.

## Alternatives Considered

1. Leave the current mixed top-level layout.
2. Rename both runtime imports to match their new directory names.
3. Create separate Python distributions before the relocations.

## Consequences

Positive:

- Runtime and training ownership are visible from the repository layout.
- Existing imports and public API routes remain stable.
- The risk-evaluation suite stays with the Interpreter that it validates.

Tradeoffs:

- Relative path calculations and deployment files must be audited after every move.
- The Vercel project root setting requires owner action when `scribe/frontend/` moves.

## Follow-Up

- Record a separate high-risk Harness intake and trace for every phase.
- Do not begin owner-led clinical-data collection without legal consent and data-handling approval.
