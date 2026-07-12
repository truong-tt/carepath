# CarePath Architecture

CarePath is one FastAPI deployment with two separately named clinical workflows.
The combined entrypoint is `apps/api/carepath/main.py`; it owns the Scribe API,
imports the Interpreter routers from `backend/app`, and mounts both built Vite
frontends after API routes.

## Product Boundaries

| Workflow | Backend boundary | Browser surface |
| --- | --- | --- |
| Ghi chép bệnh án AI | `apps/api/carepath`, `/api/v1/*` | `site/` at `/`, including `/ghi-chep-lam-sang/` |
| Phiên dịch khám bệnh trực tiếp | `backend/app`, `/api/*` and `/ws/*` | `frontend/` at `/phien-dich-y-khoa/` |

`/console/` redirects to the canonical interpreter path for compatibility. The
two API namespaces intentionally do not overlap.

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
