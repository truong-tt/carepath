# 0014 GEC Safety-Weighted Regression Gate

Date: 2026-07-13

## Status

Accepted

## Context

Aggregate WER can improve while a correction damages a medication name or a
dosage. Those errors have a higher clinical cost than ordinary transcription
differences. The training pipeline also lacked a versioned committed baseline
that CI could validate without model or GPU dependencies.

## Decision

Commit a deterministic report for the hashed, text-only frozen GEC fixture.
Require its report to stay reproducible in CI. A trained adapter must pass the
existing aggregate gate and, before export, a frozen-fixture gate that rejects
any regression in `drug_name.term_recall` or
`dosage.number_unit_preservation` versus raw ASR.

## Consequences

- Overall WER alone can never approve an adapter that harms drug or dosage
  preservation.
- CI remains CPU-only: it validates the 12-row fixture, committed report, and
  a fake-adapter export/injected-generation smoke test.
- A real adapter run still needs the owner-approved training manifest and an
  available GPU; this policy does not authorize data collection or training.
