# 0012 Interpreter Runtime Hardening

Date: 2026-07-13

## Status

Accepted

## Context

The Interpreter compared admin tokens directly, purged retained sessions only
at startup, and hard-coded development CORS origins. The combined FastAPI
service duplicated the standalone Interpreter startup path.

## Decision

Use `hmac.compare_digest` for the admin token. Give the Interpreter one shared
lifespan that seeds, purges on startup, runs a daily retention purge task, and
cancels it on shutdown; the combined service enters the same lifespan. Parse
CSV `CORS_ORIGINS` through Interpreter settings, with the existing two Vite
origins as the default.

## Consequences

- Admin authentication avoids an avoidable timing leak.
- Retention continues while a process stays up.
- Standalone and combined Interpreter startup cannot drift.
- Production operators configure allowed cross-origin development clients via
  `.env`; same-origin deployment remains the default topology.
