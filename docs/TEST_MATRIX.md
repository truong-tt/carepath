# CarePath Test Matrix

**The matrix is not in this file. It is in the Harness database.**

```powershell
.\scripts\bin\harness-cli.exe query matrix
```

That command prints every story with its unit / integration / e2e / platform
proof flags and the recorded evidence, and it is updated by
`harness-cli story update` as work lands. It is the source of truth.

This file used to hold a copied table of the same data. It went eight stories
stale — the last row was `CP-UX-11` from 2026-07-15, while the database had
carried everything through `CP-NAV-01` — and it still described itself as "the
current CarePath baseline". A snapshot of a live query is wrong the moment the
next story lands, and a wrong matrix is worse than no matrix: it invites you to
trust a proof status that was never re-checked.

## What the flags mean

Proof labels mean the relevant layer has evidence for that story's contract.
They do not claim every historical behavior was retested. Story packets in
`stories/` define the exact commands for future changes, and
`TRACE_SPEC.md` defines what a completion record must contain.

## Recording proof

```powershell
.\scripts\bin\harness-cli.exe story update --id <id> --unit 1 --integration 1 --e2e 1 --platform 1
.\scripts\bin\harness-cli.exe trace --summary "<work>" --outcome completed
```

Record the outcome that actually ran. A flag set without the command behind it
is the failure this file exists to warn about.
