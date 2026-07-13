# Design

## Domain Model

No repository model or product contract changes are required. Deployment
credentials and health-data consent remain owner-controlled trust boundaries.

## Application Flow

The deployment owner configures Vercel exactly as `docs/deploy.md` specifies,
then validates the live site and Space health endpoints. Separately, the
clinical owner obtains approved, de-identified pilot material and at least 50
clinician rubric ratings before any SOAP model decision.

## Interface Contract

The existing Vercel environment validation and Space health endpoints are the
deployment contract. The score-only SOAP rating schema and validator are the
clinical-measurement contract.

## Data Model

No clinical material belongs in this repository. Only anonymous score metadata
that passes the existing validator may be processed in an approved environment.

## UI / Platform Impact

No local UI change. The Vercel Root Directory must point to `scribe/frontend`.

## Observability

Capture live deployment status and owner-approved rating summaries outside this
repository's source tree.

## Alternatives Considered

1. Simulate deployment or clinical evidence: rejected because it would not
   prove the external environment or satisfy clinical-data safeguards.
