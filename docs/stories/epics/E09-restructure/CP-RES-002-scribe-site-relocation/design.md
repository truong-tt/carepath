# Design

## Domain Model

No domain, data, safety, or route behavior changes.

## Application Flow

The root `pyproject.toml` remains the Scribe distribution but discovers
`carepath` from `scribe/`. The combined process continues to serve the
Interpreter from `interpreter/` and static frontend directories from their
new locations.

## Interface Contract

Frozen: `/`, `/ghi-chep-lam-sang/`, `/api/v1/*`, `/api/*`, `/ws/*`,
`/phien-dich-y-khoa/`, and `/console/` redirect.

## Data Model

`data/medical_lexicon.json` remains CWD-relative at repository root.

## UI / Platform Impact

Docker, CI, docs, scripts, and Vercel root-directory documentation update to
the new Scribe/site paths. Vercel configuration is owner-operated.

## Observability

Existing health endpoints, smoke test, browser tests, and diacritics gate are
the regression proof.

## Alternatives Considered

1. Leave the public site at repository root.
2. Rename the `carepath` import to match the directory.
