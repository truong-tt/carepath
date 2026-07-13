# Design

## Domain Model

`scribe/training/` is the offline Scribe development boundary. It exposes the
standalone `gec` package only to training scripts and tests. `scribe/carepath/`
is the Scribe serving boundary and must remain independent of it.

## Application Flow

Training commands resolve the repository root, add `scribe/training/` and
`scribe/` to their command-line import paths, and read versioned files from the
new location. Generated notebooks use the same bootstrap paths.

## Interface Contract

No HTTP, websocket, product UI, or model-serving contract changes. The public
training command paths move from `training/...` to `scribe/training/...`.

## Data Model

Only source-controlled fixtures, configs, manifests, and reports move. No
clinical data, raw audio, or runtime artifacts are migrated or created.

## UI / Platform Impact

The production Docker build copies `scribe/carepath/` rather than all of
`scribe/`, excluding the offline training boundary from the runtime image.

## Observability

The existing CI training-governance job continues to execute the relocated test
suite and deterministic baseline report.

## Alternatives Considered

1. Keep `training/` at the repository root: rejected because it conceals Scribe
   ownership.
2. Create a top-level compatibility link: rejected because it preserves the
   ambiguous architecture boundary.
