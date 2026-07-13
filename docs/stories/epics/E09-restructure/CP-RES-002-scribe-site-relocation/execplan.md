# Exec Plan

## Goal

Relocate the Scribe runtime, site, and test suite without behavior changes.

## Scope

In scope:

- Move the Scribe runtime, public site, and root tests with Git history.
- Update package discovery, path math, training-script imports, CI, Docker,
  deployment docs, and current contracts.

Out of scope:

- Hosting-project configuration, API changes, and clinical behavior changes.

## Risk Classification

Risk flags:

- Cross-module architecture, deployment paths, and public site source root.

Hard gates:

- Both health endpoints, frozen public routes, keyless smoke, and all existing
  safety proof remain green.

## Work Phases

1. Record a high-risk intake.
2. Move the directories with `git mv`.
3. Correct package discovery and every moved path.
4. Audit path math and stale literals.
5. Run the relevant proof and record the actual outcome.

## Stop Conditions

Pause for a public-route or safety change. Record the Vercel source-root
setting as owner action rather than changing it externally.
