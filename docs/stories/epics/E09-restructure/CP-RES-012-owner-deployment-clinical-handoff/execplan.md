# Exec Plan

## Goal

Record the completed owner deployment work and replace the external
clinician-rating completion gate with an in-house testing scope.

## Scope

In scope:

- Owner configures Vercel Root Directory as `scribe/frontend` and supplies the
  documented deployment environment variables.
- Owner rebuilds the Docker Space and verifies the documented live routes.
- Product and plan records state that optional in-house SOAP review is
  informational only.

Out of scope:

- Repository-side deployment automation or clinical-data collection.
- Any model training or SOAP provider change from in-house review results.

## Risk Classification

Risk flags:

- Deployment, credentials, clinical data, privacy, model-decision policy.

Hard gates:

- No source audio, transcript, identifier, or note text enters the repository.
- No SOAP model, provider, or safety-policy change from in-house review results
  without a separate owner decision.

## Work Phases

1. Owner completes the Vercel and Space configuration in `docs/deploy.md`.
2. Owner records live route and health-endpoint evidence.
3. Record the deliberate in-house-only scope and its safety limits.
4. Verify the policy, plan, optional review utility, and Harness evidence.

## Stop Conditions

Pause for owner direction if a request would collect clinical data or make a
model, provider, or safety-policy change from in-house review results.
