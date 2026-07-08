# Agent instructions — carepath-interpreter

Read `PLAN.md` first (the implementation plan), `docs/research.md` for background.
Work PLAN.md phases in order; don't skip ahead or invent features not in §3 Scope.

## Non-negotiable safety invariants (PLAN.md §2 — full text there)

1. Translate-only: never generate medical advice, diagnoses, or drug recommendations.
2. High/critical-risk turns are blocked from patient display + TTS until doctor confirms.
3. Low-confidence output is always visibly flagged, never silently delivered.
4. Raw audio is never persisted — memory-only processing. No audio columns, no temp files.
5. No mic capture before recorded consent.
6. On any pipeline/reviewer failure, fail closed: keep the turn blocked, show the doctor
   raw source + translation, offer escalation. Never fail open to the patient.

## Commands

- Backend: `cd backend && uvicorn app.main:app --reload` · tests: `pytest`
- Frontend: `cd frontend && npm run dev` · tests: `npm test` · e2e: `npx playwright test`
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
