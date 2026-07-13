# Exec Plan

## Goal

Remove duplicated normalization ownership without changing the existing
Interpreter, metric, or lexical-retrieval contracts.

## Scope

In scope:

- Shared distribution and compatibility re-exports.
- A 50-case Vietnamese clinical characterization suite.
- CI, Docker, and setup instructions for the shared editable install.

Out of scope:

- Metric-baseline changes and matching-policy changes.

## Risk Classification

Risk flags:

- Cross-module architecture and validation behavior.

Hard gates:

- Interpreter safety eval and risk fixtures remain unchanged.
- Existing metric and retrieval characterizations pass.

## Work Phases

1. Capture contracts with deterministic cases.
2. Move the canonical Interpreter implementation to `shared/`.
3. Replace variants with direct imports.
4. Install shared package in every runtime path.
5. Run proof and record the Harness trace.
