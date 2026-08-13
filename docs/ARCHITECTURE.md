# CarePath Architecture

CarePath is **one product** — a care navigator for foreign patients — served by
one FastAPI deployment over two backend modules. The combined entrypoint is
`scribe/carepath/main.py`; it owns the Scribe API, imports the Interpreter
routers from `interpreter/app`, and mounts the single built Vite frontend after
the API routes.

## Product Boundaries

| Route | Backend it needs | Module |
| --- | --- | --- |
| `/` | none | — |
| `/get-care/` | **none** — fully client-side | — |
| `/my-carepath/` | **none** — fully client-side | — |
| `/kham-song-ngu/` | `/api/*` + `/ws/*` | `interpreter/app` |
| `/dich-giay-to/` | `/api/sessions`, `/api/turns/*/confirm`, `/api/v1/visits/*/documents` | both |
| `/ghi-chep-lam-sang/` | `/api/v1/*` | `scribe/carepath` |
| `/thu-nghiem/` | `/api/demo/*` (Vercel functions) + `/api/health` | interpreter, via the functions |

Every browser surface ships from `scribe/frontend/`. The separate interpreter
console was deleted when the bilingual visit replaced it; `/phien-dich-y-khoa/`
and `/console/` return an explicit 404 for anyone holding an old link. The two
API namespaces intentionally do not overlap.

The two client-side routes are a deliberate architectural property, not an
accident of what has been built so far: the pitch path must complete without a
network, and `scribe/frontend/tests/journey.spec.ts` enforces it by aborting
every request for the length of the run.

A route is only deployable when it is registered on **both** hosts — a rewrite
in `scribe/frontend/vercel.json` and a `FileResponse` in
`scribe/carepath/main.py`. `npm run validate:deploy` fails the build otherwise.
One registered on only Vercel 404'd on the Space for its whole life.

`scribe/training/` is exclusively the Scribe's offline DARAG/GEC training and quality
track. It does not train or serve the Interpreter. `interpreter/eval/` is a
separate deterministic translation-safety harness that stays with the
Interpreter.

## Boundaries That Must Stay Explicit

- Scribe output is a clinician-reviewed draft; it does not replace clinical
  judgment.
- Interpreter output is translation only. High or critical risk stays blocked
  from patient display and TTS until clinician confirmation.
- Interpreter audio is memory-only: no raw-audio persistence, no microphone
  capture before consent, and failures fail closed.
- Risk lexicons and glossary seeds are editable JSON/CSV data, not code.
- Providers, environment variables, HTTP/WebSocket payloads, uploaded files,
  and database rows are trust boundaries and must be parsed before use.

## Delivery and Proof

The shared process serves built static assets in production; Vite dev servers
remain the development path. Existing Python, eval, frontend, browser, build,
and Lighthouse commands are the validation ladder. Do not add a second service,
state framework, or test runner unless a selected story proves the need.
