# CarePath Architecture

CarePath is one FastAPI deployment with two separately named clinical workflows.
The combined entrypoint is `scribe/carepath/main.py`; it owns the Scribe API,
imports the Interpreter routers from `interpreter/app`, and mounts both built Vite
frontends after API routes.

## Product Boundaries

| Workflow | Backend boundary | Browser surface |
| --- | --- | --- |
| Ghi chép bệnh án AI | `scribe/carepath`, `/api/v1/*` | `scribe/frontend/` at `/`, including `/ghi-chep-lam-sang/` |
| Khám bệnh nhân nước ngoài | `interpreter/app`, `/api/*` and `/ws/*` | `scribe/frontend/` at `/kham-song-ngu/` |

Both browser surfaces now ship from `scribe/frontend/`. The separate interpreter
console was deleted when the bilingual visit replaced it; `/phien-dich-y-khoa/`
and `/console/` return an explicit 404 for anyone holding an old link. The two
API namespaces intentionally do not overlap.

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
