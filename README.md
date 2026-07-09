# CarePath

One product, two modules for Vietnamese clinics:

- **Scribe** — upload consultation audio, get a Gipformer ASR transcript with
  retrieval-assisted term correction and a draft Vietnamese SOAP note for
  clinician review. Backend: `apps/api/carepath` (FastAPI, `/api/v1/*`).
- **Interpreter** — live Vietnamese ↔ English interpreting with risk gating,
  read-back confirmation, and interpreter escalation. Backend: `backend/app`
  (FastAPI, `/api/*` + `/ws/*`). Mock mode runs with zero API keys.

Public demo site: `site/` (Vite + React). Interpreter console: `frontend/`.

> Temporary post-merge stub — the full unified README lands with ticket M.8 of
> `MERGE-PLAN.md`. Until then: scriber quickstart is unchanged from `main`
> (`scripts/setup_local.ps1`, `scripts/run_api.ps1`), interpreter quickstart is
> unchanged from the interpreter branch (`cd backend && uvicorn app.main:app`).
