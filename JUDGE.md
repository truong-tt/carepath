# JUDGE.md — claude-fable-5 review protocol for the CarePath unification

**Who runs this:** claude-fable-5, in a fresh session, after codex finishes MERGE-PLAN.md.
**What is judged:** the `carepath-unified` branch, ticket commits M.0 → M.8.
**Baselines for comparison:** `origin/main` (scriber contract) and
`origin/carepath-interpreter-demo` (interpreter behavior + S.8 design).

Judge the work, not the plan. If MERGE-PLAN.md itself turns out to be wrong somewhere
and codex deviated for a good, documented reason, that is acceptable — say so explicitly
in the verdict instead of failing the ticket.

---

## 1. Hard gates — any failure ⇒ overall NEEDS WORK

Run every gate. Report each as PASS / FAIL with evidence (command output, file:line).

### G1. Everything green

Run the full Verify inventory (MERGE-PLAN.md §3) on a clean checkout of
`carepath-unified`:

```text
pip install -e ".[dev]" -e "./backend[dev]"        # one Python 3.12 venv
pytest                                              # root (scriber + combined-app test)
python scripts/smoke_backend.py
cd backend && ruff check . && pytest && cd ..
python eval/run_eval.py --set eval/fixtures/eval_starter.tsv --providers mock
cd frontend && npm ci && npm run lint && npm test && cd ..
cd site && npm ci && npm run lint && npm test && npm run build && cd ..
# e2e (needs built app / mock backend per ci.yml):
cd frontend && npm run e2e ; cd ../site && npm run e2e
```

### G2. Scriber API contract frozen

The deployed HF Space clients must not break:

```text
git diff origin/main carepath-unified -- apps/api/carepath/schemas.py
```

Schema diff must be empty (or provably additive-only). Then compare every `/api/v1/*`
route signature, status codes, and rate-limit/TEAM_CODE behavior in
`apps/api/carepath/main.py` against `origin/main` — changes must be additions
(interpreter routers, static mounts, lifespan additions), never modifications to
existing scriber behavior.

### G3. Safety invariants intact (AGENTS.md §2 / MERGE-PLAN.md §2)

Audit with greps + targeted reads on the merged tree:

1. **No raw-audio persistence** in the interpreter path: no audio columns in
   `backend/app/crud.py` models, no `tempfile`/disk writes of turn audio in
   `backend/app/session.py` or `api.py`. (The scriber's documented tempfile
   normalization of *uploaded clips* on `origin/main` is pre-existing and allowed.)
2. **Consent before mic**: every `getUserMedia` call site in `frontend/` and `site/`
   (including the new scribe view) is gated behind the consent flow.
3. **Risk blocking**: high/critical turns still blocked pre-confirmation — spot-check
   `backend/app/session.py` + `frontend/src/components/InterpreterConsole.tsx` are
   unchanged from the interpreter branch (or changed only for import/serving reasons).
4. **Fail-closed**: pipeline error paths in `backend/app/api.py` unchanged.
5. **No advice generation** introduced anywhere in new copy or code.
6. **Diacritics**: `site/` build gate ran; spot-check new Vietnamese copy (Scribe
   section, error messages) for full diacritics.

### G4. Keyless boot

With **no** API keys in the environment (`PROVIDER_MODE=mock`, `ASR_PROVIDER=mock`,
`ALLOW_MOCK_ASR=true`, `LLM_PROVIDER=offline`): the combined uvicorn app boots and
serves `/api/health`, `/api/v1/health`, a mock `POST /api/v1/soap-notes`, a created
interpreter session + WebSocket handshake, and (if dists are built) `/` and `/console/`.

### G5. Retirement + hygiene

- `git ls-files apps/web apps/web-next` → empty.
- `grep -ri "carepath translate" site/src docs README.md` → empty.
- No secrets/keys anywhere in `git diff origin/main...carepath-unified`.
- Root `package-lock.json` orphan (if still present without a root `package.json`) —
  flag for deletion.
- `.env.example` documents both products; defaults match the keyless demo profile.

## 2. Scored review — 1 (poor) to 5 (excellent) each

| Dimension | What 5 looks like |
|---|---|
| Brand/UI consistency | Landing, scribe view, and console read as one product on the S.8 design system; logo/name unified; no leftover Translate branding or old apps/web styling. |
| Code quality | Matches AGENTS.md conventions (ruff, TS strict, small components, data-not-code lexicons); no copy-paste from app.js left un-Reactified; no dead code. |
| Commit hygiene | Exactly one commit per ticket, M.0→M.8 in order, subjects match, bodies explain any deviation from the plan. |
| Minimalism | No unrequested abstractions, no new deps beyond plan, hash route not a router lib, mounts/env kept simple. |

## 3. Verdict format

1. **Per-ticket table**: ticket · commit sha · gates touched · PASS / NEEDS WORK · one-line note.
2. **Hard-gate table**: G1–G5 with evidence.
3. **Scores** with one sentence each.
4. **Overall: PASS or NEEDS WORK.** If NEEDS WORK: a numbered, codex-executable fix
   list — each item states the file, the defect, the expected behavior, and which gate
   it unblocks. No vague items.
