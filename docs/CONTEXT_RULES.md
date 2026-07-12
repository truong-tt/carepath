# CarePath Context Rules

Read enough to preserve the selected contract, not the entire repository.

| Lane | Required context before implementation |
| --- | --- |
| Tiny | `AGENTS.md`, `docs/FEATURE_INTAKE.md`, matrix query, and exact files to change |
| Normal | Tiny context plus relevant product contract, story, validation command, and architecture when a boundary changes |
| High-risk | Normal context plus relevant decisions, high-risk template, safety/eval fixtures, and every affected module boundary |

Always read the current task's validation evidence before recording its trace.
For product or UX work, read the appropriate `docs/product/` contract; for UX
flows also read `docs/ux-redesign-carepath.md`. For risk, consent, TTS, audio,
or provider work, read `AGENTS.md` safety invariants and the affected tests and
fixtures before editing.

Stop reading unrelated history once the lane, contract, affected files, and
proof path are clear. Search targeted paths with `rg` rather than loading broad
archives.
