# Exec Plan

## Goal

Complete the owner-only end conditions without weakening deployment or clinical
safety requirements.

## Scope

In scope:

- Owner configures Vercel Root Directory as `scribe/frontend` and supplies the
  documented deployment environment variables.
- Owner rebuilds the Docker Space and verifies the documented live routes.
- Clinical owner completes the approved de-identified rating protocol.

Out of scope:

- Repository-side deployment automation or clinical-data collection.
- Any model training or SOAP provider change before the rating threshold.

## Risk Classification

Risk flags:

- Deployment, credentials, clinical data, privacy.

Hard gates:

- No source audio, transcript, identifier, or note text enters the repository.
- No SOAP model decision before 50 approved clinician ratings.

## Work Phases

1. Owner completes the Vercel and Space configuration in `docs/deploy.md`.
2. Owner records live route and health-endpoint evidence.
3. Clinical owner completes legal approval, de-identification, and ratings.
4. Owner reopens the plan with that evidence for final verification.

## Stop Conditions

Do not proceed without deployment-owner access or approved clinical-data
authority.
