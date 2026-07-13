# Exec Plan

## Goal

Relocate the Interpreter and its evaluation assets while preserving behavior.

## Scope

In scope:

- Move `backend/`, `frontend/`, and `eval/` with Git history.
- Update direct path references, path math, CI, Docker, deployment docs, and
  relevant current contracts.

Out of scope:

- Product, route, risk, consent, audio, or provider changes.
- External Vercel configuration.

## Risk Classification

Risk flags:

- Cross-module architecture and deployment paths.

Hard gates:

- Interpreter safety proof must remain green.
- Combined API health endpoints and frozen public routes must still work.

## Work Phases

1. Record the target-layout decision and high-risk intake.
2. Move the Interpreter directories with `git mv`.
3. Correct every moved path and static asset default.
4. Audit path math and stale literals.
5. Run the existing relevant proof and record the actual outcome.

## Stop Conditions

Pause for human confirmation if a move changes a public route, safety
invariant, API contract, or requires external hosting configuration.
