# Stories

Stories are work packets. They turn product intent into bounded implementation
and validation work.

This directory holds them. It previously said "No story packets are active yet"
while sitting next to two dozen of them.

## What is here

- `CP-NAV-*` — the care navigator, the current product direction.
- `CP-UX-*` — public-surface and onboarding work, `09` through `19`.
- `CP-BASE-*` — the four baseline contracts the repository started from.
- `CP-MNT-*`, `GEC-*`, `HARN-*` — maintenance, training governance, harness
  adoption.
- `epics/` — multi-story programmes. See `epics/README.md`; E09 is complete.
- `backlog.md` — candidate work that has not been sliced yet.

A completed packet is kept, not deleted: it records why a decision was made,
which a diff does not. Do not reopen one as current work.

Proof status lives in the Harness database, not in these files:

```powershell
.\scripts\bin\harness-cli.exe query matrix
```

## Normal Story

Use `docs/templates/story.md`. One file, named for its id:

```text
docs/stories/CP-UX-19-paperwork-route.md
```

## High-Risk Story

Use `docs/templates/high-risk-story/` when `FEATURE_INTAKE.md` classifies the
work as high-risk. Four files, in a directory named for the id:

```text
docs/stories/epics/E09-restructure/CP-RES-007-interpreter-hardening/
  overview.md
  design.md
  execplan.md
  validation.md
```

## Status Flow

```text
planned -> in_progress -> implemented
                  |
                  v
               changed
                  |
                  v
               retired
```
