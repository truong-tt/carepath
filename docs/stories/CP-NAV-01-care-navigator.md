# CP-NAV-01 Foreign-patient care navigator

## Status

implemented, validated

## Lane

normal

## Product Contract

CarePath stops presenting itself as three clinic tools that share a codebase and
presents itself as one journey a foreign patient walks:

**Find care → Prepare → Visit → Verify → Paperwork → Follow-up**

The clinician confirmation gate stays exactly where it is. It is not a stage the
journey adds; it is the stage the journey exists to make legible.

Concretely, after this story:

1. `/` states the problem, the user and the product in English within one
   viewport, and offers `I need medical care` and `I already have a prescription`.
2. `/get-care/` runs need → provider → Visit Brief → visit + safety gate →
   paperwork, entirely client-side, with no network at all.
3. `/my-carepath/` holds one `CareEpisode` for the session and can clear it.
4. `/kham-song-ngu/` and `/dich-giay-to/` behave as before and can write their
   confirmed output into the episode.

## Relevant Product Docs

- `docs/ux-redesign-carepath.md` — the UX contract this story updates first.
- `docs/decisions/0023-foreign-patient-care-navigator.md` — positioning and the
  patient/clinician language split.
- `docs/product/carepath-suite.md`

## Acceptance Criteria

- A reader who does not know the words Scribe, Interpreter or OCR can describe
  what CarePath does after reading `/`.
- The whole `/get-care/` journey completes with the network disabled.
- A scripted high-risk turn is withheld from the patient column by
  `isGated`/`canSpeakTurn` in `scribe/frontend/src/visit/types.ts` — the same
  predicates the live visit uses — and is released only after a confirm action.
- Curated provider rows are labelled as curated, and no appointment availability
  is stated anywhere.
- `/get-care/` and `/my-carepath/` open no WebSocket, request no microphone and
  make no fetch.
- The episode holds no name, passport, date of birth or phone number, lives in
  `sessionStorage`, and is clearable from the UI.
- Route parity holds: each new route has its `App.tsx` const, three `vercel.json`
  rewrites and a `main.py` FileResponse pair.
- `npm test`, `npm run build` (diacritics gate), `npm run e2e` and `pytest` pass.

## Design Notes

- Commands: none added. The journey is frontend composition.
- Queries: none added.
- API: **unchanged**. Existing `POST /api/sessions`,
  `POST /api/turns/{id}/confirm`, `POST /api/v1/visits/{id}/documents`,
  `POST /api/v1/visits/{id}/note` are reused as-is.
- Tables: **unchanged**. No migration. The episode is browser-side only.
- Domain rules: unchanged. `turn_status` in `interpreter/app/session.py` and the
  risk engine are not touched.
- UI surfaces: `/` rewritten; `/get-care/` and `/my-carepath/` added;
  `/kham-song-ngu/` and `/dich-giay-to/` gain one save action each.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | vitest: episode load/save/clear, provider matching, visit-brief build, scripted gate withholding, landing copy |
| Integration | vitest: Get Care stepper advances need → provider → brief → visit → paperwork |
| E2E | playwright: offline walk of `/` → `/get-care/` → `/my-carepath/`; existing paperwork and demo specs still pass |
| Platform | `npm run build` (diacritics), `npm run validate:deploy` (route parity) |
| Release | `pytest`, `python scripts/smoke_backend.py` — proving the backend was not disturbed |

## Harness Delta

None. Existing lanes and proof layers cover this work.

## Evidence

Run on 2026-08-13, all green:

| Command | Result |
| --- | --- |
| `npx vitest run` | 108 passed, 12 files |
| `npm run build` | built; diacritics gate passed |
| `npm run e2e` | 40 passed, including `tests/journey.spec.ts` |
| `npm run lint` | clean |
| `npx tsc -p tsconfig.app.json` | clean |
| `pytest` | 108 passed, 1 skipped |
| `python scripts/smoke_backend.py` | `health: ok` |
| `python scripts/build_term_artifacts.py --check` | artifacts current |
| `validateRouteRewrites()` | 6 routes, parity on both hosts |

`tests/journey.spec.ts` aborts every request for the whole run and then walks
the journey end to end, so "offline" is proved by removing the network rather
than asserted.

Three defects found and fixed while validating, all pre-existing:

1. `/dich-giay-to/` was registered in `vercel.json` and never in
   `scribe/carepath/main.py`, so it 404'd on the Hugging Face Space from the day
   it shipped. The parity check now reads both hosts.
2. `.visit-turn__meta` used `--faint` on `--tint` at 4.02:1 — below AA on every
   turn card in the live visit since it shipped.
3. `.p-nav__back` was defined three times, each scoped to a route wrapper, so a
   fourth surface got the UA's default link blue on navy at 1.42:1. Now defined
   once in `styles.css` and the duplicates deleted.
