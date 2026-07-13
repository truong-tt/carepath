# 0016 Scribe Training Ownership

Date: 2026-07-13

## Status

Accepted

## Context

The offline DARAG/GEC training code, fixtures, reports, notebooks, and scripts
already support the Scribe's Vietnamese clinical-note workflow. The top-level
`training/` directory obscures that ownership and risks being confused with the
Interpreter's safety evaluation harness at `interpreter/eval/`.

## Decision

Move the complete offline training boundary to `scribe/training/`. It contains
the GEC package, configs, fixtures, manifests, reports, notebooks, scripts,
tests, and SOAP measurement tooling. `interpreter/eval/` remains the
Interpreter's independent safety regression harness.

The Scribe serving package at `scribe/carepath/` must not import training code;
the production image copies only the Scribe runtime package, not
`scribe/training/`. Training keeps its standalone `gec.*` command-line import
boundary without adding a distribution or dependency.

This supersedes only the top-level training-location portion of decision 0009.

## Consequences

- Training commands and CI use `scribe/training/...` paths.
- Runtime packaging stays independent of offline model-development artifacts.
- The repository has a visibly separate Scribe training boundary and
  Interpreter safety-evaluation boundary.
