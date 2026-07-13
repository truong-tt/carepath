# Design

## Domain Model

The shared module owns three explicit contracts: Interpreter text
normalization, case-insensitive metric normalization, and lexical-match
normalization. This preserves the intentionally distinct behavior that had
previously been hidden by duplicate function names.

## Interface Contract

`app.normalize`, `carepath.evaluation`, `carepath.services.retrieval`,
`gec.metrics`, and `gec.retrieval` keep their existing public imports.

## UI / Platform Impact

No UI, route, API, persistence, or provider behavior changes.

## Alternatives Considered

1. Force every caller onto Interpreter `normalize_text` and change scoring.
2. Keep local copies and accept future drift.
