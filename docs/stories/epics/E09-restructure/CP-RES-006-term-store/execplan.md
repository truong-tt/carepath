# Exec Plan

## Goal

Create one medical-term source of truth without changing serving contracts.

## Scope

In scope:

- Canonical dataset, deterministic builder, drift test, and CI gate.
- Documentation of generated artifacts and risk-lexicon boundary.

Out of scope:

- Risk lexicon consolidation, data enrichment, taxonomy changes, or API changes.

## Risk Classification

Risk flags:

- Cross-module data ownership and Interpreter safety validation.

Hard gates:

- Generated artifacts stay behavior-equivalent.
- Scribe and Interpreter tests and safety eval pass.

## Work Phases

1. Characterize both artifact schemas and counts.
2. Create the canonical source and deterministic generator.
3. Add drift proof to CI.
4. Run serving, safety, and frontend regression proof.
