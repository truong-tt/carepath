# Exec Plan

## Goal

Apply the three Phase 7 hardening changes without widening runtime behavior.

## Scope

In scope:

- Constant-time admin-token comparison.
- Shared daily retention lifecycle.
- CSV CORS configuration and `.env.example` documentation.

Out of scope:

- Provider/model changes, routes, storage schema, and safety-rule changes.

## Risk Classification

Risk flags:

- Credentials, privacy retention, security, and deployment configuration.

Hard gates:

- Existing admin authorization, safety fixtures, and combined-app tests pass.
- Background task cancels during lifespan shutdown.

## Work Phases

1. Characterize current admin, retention, and CORS paths.
2. Centralize Interpreter lifespan.
3. Add focused hardening tests.
4. Run full regression proof and record the trace.
