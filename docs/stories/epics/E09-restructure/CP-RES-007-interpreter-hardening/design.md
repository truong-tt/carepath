# Design

## Application Flow

`interpreter_lifespan` performs existing validation, database initialization,
seeding, and startup purge. It owns a daily `asyncio` retention task and awaits
its cancellation during shutdown. The combined application enters this same
context after Scribe warmup.

## Interface Contract

`/api/admin/review`, all API/WebSocket routes, provider defaults, and both
health endpoints retain their existing shapes.

## Data Model

No schema change. The existing `RETENTION_DAYS` setting controls both startup
and daily purges.

## UI / Platform Impact

`CORS_ORIGINS` is a comma-separated setting, documented in `.env.example`.

## Alternatives Considered

1. Duplicate a background task in each app lifespan.
2. Add a scheduler dependency.
3. Keep startup-only retention.
