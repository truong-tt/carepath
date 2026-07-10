# Agent instructions — CarePath (unified)

One product, two modules: the scriber (`apps/api/carepath`, `/api/v1/*`) and the
interpreter (`backend/app`, `/api/*` + `/ws/*`), served by one FastAPI process
plus two Vite frontends (`site/` at `/`, `frontend/` at `/console/`).
`PLAN.md` and `DEMO-SITE-PLAN.md` are historical build plans for the interpreter
and demo site. `MERGE-PLAN.md` is the executed unification plan (M.0–M.8 done);
`JUDGE.md` is its review protocol, run by claude-fable-5.
`docs/research.md` holds the interpreter safety background.

## Non-negotiable safety invariants (PLAN.md §2 — full text there)

1. Translate-only: never generate medical advice, diagnoses, or drug recommendations.
2. High/critical-risk turns are blocked from patient display + TTS until doctor confirms.
3. Low-confidence output is always visibly flagged, never silently delivered.
4. Raw audio is never persisted — memory-only processing. No audio columns, no temp files.
5. No mic capture before recorded consent.
6. On any pipeline/reviewer failure, fail closed: keep the turn blocked, show the doctor
   raw source + translation, offer escalation. Never fail open to the patient.

## Commands

- Combined service: `uvicorn carepath.main:app --app-dir apps/api --reload`
  (needs `pip install -e ".[dev]" -e "./backend[dev]"`)
- Scriber + combined tests: root `pytest` · keyless smoke: `python scripts/smoke_backend.py`
- Interpreter backend alone: `cd backend && uvicorn app.main:app --reload` · tests: `pytest`
- Console: `cd frontend && npm run dev` · tests: `npm test` · e2e: `npx playwright test`
- Demo site: `cd site && npm run dev` · tests: `npm test` · build (diacritics gate):
  `npm run build` · e2e: `npm run e2e`
- Full mock-mode run: set `PROVIDER_MODE=mock` in `.env` — must work with no API keys.
- Eval regression: `python eval/run_eval.py --set eval/fixtures/eval_starter.tsv --providers mock`

## Conventions

- Python 3.12, ruff-formatted, type-hinted; pure functions for normalize/risk rules.
- TypeScript strict; components small; state minimal (context/zustand, no redux).
- Risk lexicons and glossary seeds are JSON/CSV data files — clinicians edit data, not code.
- Every risk-engine behavior change updates `eval/fixtures/risk_cases.jsonl`; the fixture
  run is the test. Zero misses on critical fixtures is a hard gate.
- Secrets only via env; `.env` is gitignored; `.env.example` stays current.
- No new dependencies beyond those named in PLAN.md without noting why in the PR.
- Vietnamese text is data, not decoration: always NFC-normalized, diacritics preserved;
  tests include diacritic-stripped variants where matching allows it.
