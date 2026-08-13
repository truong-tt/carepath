# Story Epics

One directory per epic. High-risk stories get a packet — `overview.md`,
`design.md`, `execplan.md`, `validation.md` — instead of a single file, because
their proof does not fit on one page.

## E09 — Restructure · **complete**

Thirteen stories that split the repository into the layout it has now: the
Interpreter and Scribe runtimes separated, shared normalization and the medical
term store consolidated, and Scribe's offline training moved out of the serving
path. Accepted in `../../decisions/0009-restructure-target-layout.md`.

| Story | What it moved |
| --- | --- |
| CP-RES-001 | Interpreter runtime, console and evaluation |
| CP-RES-002 | Scribe runtime, public site and tests |
| CP-RES-004 | GEC training out of Scribe serving |
| CP-RES-005 | Shared text normalization |
| CP-RES-006 | The medical term store |
| CP-RES-007 | Interpreter runtime hardening |
| CP-RES-008–010 | GEC data foundation, regression gates, SOAP measurement |
| CP-RES-011–013 | Scribe training ownership, deployment handoff, research pipeline |

Every one is `implemented` with recorded proof. Check it rather than trust this
table:

```powershell
.\scripts\bin\harness-cli.exe query matrix
```

**Do not reopen these as current work.** They are the durable record of how the
layout was arrived at, which is why they are kept rather than deleted — a
completed packet explains a decision that a diff alone does not. Two details
they still describe accurately are worth knowing: the interpreter console named
throughout CP-RES-001 was later deleted when the bilingual visit replaced it,
and Docker proof is recorded as skipped because Harness has no registered
container-build provider.

New work goes in `../` as a single story file, or in a new epic directory here
only when it genuinely needs a four-part packet. See `../README.md`.
