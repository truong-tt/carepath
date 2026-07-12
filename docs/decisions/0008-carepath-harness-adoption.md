# 0008 CarePath Harness Adoption

Date: 2026-07-12

## Status

Accepted

## Context

CarePath has two clinical workflows, strict safety invariants, multiple test
surfaces, and historical plans. Future coding agents need a durable way to
classify work, preserve those boundaries, and record actual proof.

## Decision

Adopt Repository Harness from upstream commit `14e6f102a4a645562d046f7c693c61401261cac6`
with its pinned, checksum-verified Windows CLI v0.1.11. Keep `AGENTS.md` as the
highest repository-level safety and UX instruction, tailor the Harness to the
current CarePath contracts, and load the same instructions from `CLAUDE.md`.

## Alternatives Considered

1. Keep only historical plans and ad-hoc validation notes.
2. Adopt a documentation-only workflow without durable local records.
3. Replace the existing CarePath instructions with the generic upstream shim.

## Consequences

Positive:

- New work has explicit risk lanes, proof expectations, and durable traces.
- Codex and Claude Code share the same project contract.
- The Harness introduces no product dependencies or CI changes.

Tradeoffs:

- Agents must perform a small intake and trace step for future work.
- `harness.db` is local-only, so durable operational records are per clone.

## Follow-Up

- Upgrade the Harness only as a separately reviewed maintenance task.
- Register optional tools only when a recurring validation need proves one.
