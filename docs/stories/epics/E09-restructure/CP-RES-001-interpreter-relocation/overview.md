# Overview

## Current Behavior

The Interpreter runtime, console, and safety-evaluation harness live in
`backend/`, `frontend/`, and `eval/` while the combined service imports the
Interpreter as `app`.

## Target Behavior

They live under `interpreter/` as `interpreter/app`, `interpreter/frontend`,
`interpreter/tests`, and `interpreter/eval`, without changing the `app` import,
public routes, or safety behavior.

## Affected Users

- Developers and deploy operators; clinical workflows are unchanged.

## Affected Product Docs

- `docs/product/carepath-suite.md`
- `docs/product/live-interpreter.md`

## Non-Goals

- Changing Interpreter APIs, risk rules, consent, audio handling, or UI behavior.
