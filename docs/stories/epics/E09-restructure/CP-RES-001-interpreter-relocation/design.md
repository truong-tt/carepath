# Design

## Domain Model

No product-domain, data, or safety behavior changes. This is a directory-only
ownership move.

## Application Flow

The combined Scribe process continues to import `app` after editable install of
`./interpreter[dev]`; standalone Interpreter execution continues from its
directory.

## Interface Contract

Frozen: `/api/*`, `/ws/*`, `/phien-dich-y-khoa/`, and `/console/` redirect.

## Data Model

Unchanged. The evaluation fixtures move with the Interpreter tests.

## UI / Platform Impact

CI, Docker, static asset defaults, and deployment documentation point at the
new locations. No browser-visible behavior changes.

## Observability

Existing health endpoints and safety-eval output remain the proof.

## Alternatives Considered

1. Keep `eval/` at repository root.
2. Rename `app` during the move.
