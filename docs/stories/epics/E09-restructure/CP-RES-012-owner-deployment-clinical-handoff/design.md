# Design

## Domain Model

No runtime change is required. The product contract documents that optional
in-house review is informational only; deployment credentials and health-data
consent remain owner-controlled trust boundaries.

## Application Flow

The deployment owner configures Vercel exactly as `docs/deploy.md` specifies,
then validates the live site and Space health endpoints. Optional in-house
review may use synthetic or already-approved de-identified material, but it
does not authorize any SOAP model decision.

## Interface Contract

The existing Vercel environment validation and Space health endpoints are the
deployment contract. The score-only SOAP review schema and validator provide
in-house quality signals only.

## Data Model

No clinical material belongs in this repository. Optional review metadata may
be processed only outside the source tree using the existing validator.

## UI / Platform Impact

No local UI change. The Vercel Root Directory must point to `scribe/frontend`.

## Observability

Capture live deployment status. Optional in-house review summaries stay outside
this repository's source tree.

## Alternatives Considered

1. Keep the external clinical-rating gate: rejected because it conflicts with
   the owner-directed in-house testing scope.
2. Simulate live deployment: rejected because it would not prove the external
   environment.
