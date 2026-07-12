# HARN-001 Adopt CarePath Harness

## Status

implemented

## Lane

normal

## Product Contract

Future CarePath work has a durable intake, story/proof, decision, and trace
workflow without changing existing product behavior.

## Relevant Product Docs

- `docs/product/carepath-suite.md`

## Acceptance Criteria

- The pinned Harness install is merge-safe and checksum-verifies its CLI.
- Codex and Claude Code load the same CarePath instructions.
- Current module boundaries and proof commands replace generic Harness
  placeholders.
- Existing product code, CI, dependencies, and user worktree changes remain
  untouched.

## Validation

| Layer | Expected proof |
| --- | --- |
| Integration | CLI version, initialization, matrix query, and audit |
| Release | Existing repository validation commands record real outcomes |

## Harness Delta

Installs the initial Harness policy, schemas, templates, baseline records, and
decision for CarePath.

## Evidence

Pinned merge install created 43 upstream Harness files and checksum-verified
`harness-cli.exe` v0.1.11. CLI initialization, matrix query, and audit ran;
the complete existing CarePath proof suite passed in the configured Python 3.12
and Node environments on 2026-07-12.
