# CarePath Harness

CarePath uses Repository Harness to turn a request into safe, reviewable work.
The application is what clinicians use; the Harness is the durable operating
layer for humans and coding agents.

## Sources of Truth

Apply sources in this order:

1. Current user instruction and the safety, Vietnamese-first, and UX rules in
   `AGENTS.md`.
2. The current contracts in `docs/product/`.
3. The selected story packet in `docs/stories/` and accepted decisions in
   `docs/decisions/`.
4. Executable tests and the proof matrix.
5. `docs/history/` and research as background, unless a current contract
   explicitly incorporates them.

No Harness document may weaken a CarePath safety invariant. If sources conflict,
pause and ask the user rather than choosing a less-safe interpretation.

## Durable Layer

`scripts/bin/harness-cli.exe` manages the local, ignored `harness.db` using the
versioned migrations in `scripts/schema/`. Initialize it once per clone:

```powershell
.\scripts\bin\harness-cli.exe init
```

The database records intake classifications, story proof, decisions, traces,
and Harness friction. Markdown remains the reviewable product record; the
database records what happened locally.

## Task Loop

1. Read `AGENTS.md`, this file, `docs/FEATURE_INTAKE.md`, and the current
   matrix.
2. Classify and record the request with `harness-cli.exe intake`.
3. Read only the affected product contract, stories, decisions, and code.
4. Define the proof before implementation.
5. Implement only the selected lane.
6. Update the product contract, story, and matrix when the change affects them.
7. Run the applicable existing checks and record their actual result.
8. Record a trace. Capture repeated missing context or proof as Harness
   friction or a backlog item.

For UX or product-flow work, `AGENTS.md` additionally requires an updated
`docs/ux-redesign-carepath.md` before implementation. That requirement applies
even when intake classifies the edit as tiny.

## Tool Registry

The registry is optional. Before relying on an external tool, query it by
capability. If no present provider is registered, skip that optional step and
record the limitation only when it affects proof. Do not add a dependency or
tool registration merely to satisfy the Harness.

## Done

A task is done when its requested change is complete, relevant contracts and
proof records are current, the applicable checks have real results, and the
trace says what happened. A failed unrelated existing check is recorded as
failed proof; repairing it requires separate scope.
