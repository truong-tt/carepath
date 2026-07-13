# CP-UX-09 Block public Interpreter access

## Status

implemented

## Lane

normal

## Product Contract

The public CarePath experience exposes Scribe only. Interpreter browser paths
return 404 while its API, WebSocket, and safety behavior remain available for
internal development.

## Relevant Product Docs

- `docs/product/live-interpreter.md`
- `docs/ux-redesign-carepath.md`

## Acceptance Criteria

- `/phien-dich-y-khoa/*` and `/console/*` return 404.
- Scribe and both API health routes continue to return 200.
- No Interpreter safety or API behavior changes.

## Design Notes

- UI surfaces: retain the existing Scribe-first public landing.
- API: no contract change.
- Routing: remove the Interpreter static mount and guard its public paths.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `python -m pytest scribe/tests/test_combined_app.py` |
| E2E | `cd scribe/frontend; npm.cmd test; npm.cmd run e2e` |
| Platform | Space routes return 404 for Interpreter and 200 for Scribe and health |
| Release | `cd scribe/frontend; npm.cmd run build` |

## Harness Delta

No Harness change. The deployment-only Space snapshot continues to omit
non-runtime binary QA assets.

## Evidence

2026-07-13: combined-app route proof passed (3 tests); Scribe frontend unit
(45), build, and browser (7) checks passed; Ruff passed. Space commit
`cc678b9` is Running. Live HTTP checks returned 404 for
`/phien-dich-y-khoa/`, its asset path, and `/console/`; `/`,
`/ghi-chep-lam-sang/`, `/api/v1/health`, `/api/health`, and the Vercel public
site each returned 200.
