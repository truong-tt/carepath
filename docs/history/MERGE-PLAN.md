# CarePath Unification Plan — merge Scriber + Interpreter into one product

**Executor:** codex-5.6 terra (fallback: codex-5.5 xhigh). Work tickets M.0 → M.8 in
order, **one commit per ticket**, commit subject `M.x <imperative summary>`. Every
ticket ends green: run that ticket's Verify list before committing. If a Verify step
fails, fix it inside the same ticket — never commit red, never skip ahead.

**Judge:** after M.8, claude-fable-5 reviews the branch against `JUDGE.md`. Anything
that fails a hard gate there comes back as a fix list — save everyone a round trip by
running the gates yourself first.

---

## 1. What is being merged

The repo holds two products with **unrelated git histories**:

| | Scriber (`origin/main`) | Interpreter (`origin/carepath-interpreter-demo`) |
|---|---|---|
| Backend | `apps/api/carepath` FastAPI: `/api/v1/health`, `/api/v1/corrections`, `/api/v1/soap-notes` | `backend/app` FastAPI: `/api/*` REST + `/ws/sessions/{id}` WebSocket, risk engine, admin review |
| ASR / LLM | Gipformer ONNX (local, keyless) + ckey OpenAI-compatible LLM. **Deployed, working** (HF Space Docker) | OpenAI + Anthropic cloud providers (no keys) → **mock mode only** |
| Frontends | `apps/web` (static tool), `apps/web-next` (Next.js landing) | `frontend/` (interpreter console), `site/` (marketing demo site — the S.8 clinical redesign) |

Target: **one product, "CarePath"**, on branch `carepath-unified`:

1. **One FastAPI service** (single deploy): scriber routes stay at `/api/v1/*`,
   interpreter routes at `/api/*` + `/ws/*`, one combined lifespan.
2. **Interpreter stays mock-only for now.** Do not touch the provider abstraction or
   wire new providers. Real interpreter providers are a later, separate track.
3. **`site/` becomes the entire public face**, rebranded "CarePath Translate" →
   "CarePath" with two modules: **Interpreter** and **Scribe**. The newer branch's
   UI/UX (logos, design system) wins everywhere. `apps/web` and `apps/web-next` are
   retired.
4. **Histories are preserved** via `git merge --allow-unrelated-histories`.

## 2. Non-negotiable invariants (inherited from AGENTS.md — full text there)

These apply to every ticket. The judge greps for regressions on each one.

1. Translate-only: never generate medical advice, diagnoses, or drug recommendations.
2. High/critical-risk turns stay blocked from patient display + TTS until doctor confirms.
3. Low-confidence output is always visibly flagged, never silently delivered.
4. Raw audio is never persisted by the interpreter — memory-only. No audio columns, no temp files.
5. No mic capture before recorded consent.
6. On pipeline/reviewer failure, fail closed — never fail open to the patient.
7. Vietnamese copy always carries full diacritics, NFC-normalized. `site/` build enforces this.
8. **The scriber API contract is frozen**: request/response schemas and routes under
   `/api/v1/*` must be byte-for-byte compatible with `origin/main` (`carepath/schemas.py`
   and the endpoint signatures in `carepath/main.py`). The deployed HF Space and its
   clients must keep working.
9. Keyless boot is a hard requirement end-to-end: `PROVIDER_MODE=mock` +
   `LLM_PROVIDER=offline` + `ASR_PROVIDER=mock`/`ALLOW_MOCK_ASR=true` must run the whole
   combined product with zero API keys.
10. Secrets only via env. `.env` gitignored, `.env.example` stays current. No new
    dependencies beyond those named in this plan without a written why in the commit body.

## 3. Verify command inventory

Used throughout the tickets (all verified to exist on their source branches):

```text
# scriber (repo root, Python 3.12 venv with: pip install -e ".[dev]")
pytest                                     # root suite (tests/, pythonpath apps/api)
python scripts/smoke_backend.py            # forces mock ASR + offline LLM internally

# interpreter backend (from backend/, same venv with: pip install -e ".[dev]")
ruff check .
pytest

# eval regression (repo root)
python eval/run_eval.py --set eval/fixtures/eval_starter.tsv --providers mock

# interpreter console (from frontend/)
npm ci && npm run lint && npm test && npm run e2e     # e2e needs PROVIDER_MODE=mock backend

# demo site (from site/)
npm ci && npm run lint && npm test && npm run build   # build runs check-diacritics.mjs
npm run e2e
```

---

## Tickets

### M.0 — Unify the histories

1. `git checkout -b carepath-unified origin/main`
2. `git merge --allow-unrelated-histories origin/carepath-interpreter-demo`
3. Exactly three paths collide — resolve as:
   - `README.md`: temporary stub — unified title, one paragraph per product, links to
     both quickstarts. Rewritten properly in M.8.
   - `.gitignore`: union of both, deduplicated.
   - `.env.example`: both files concatenated under `# --- Scriber (apps/api) ---` and
     `# --- Interpreter (backend/) ---` section headers. Properly merged in M.2.
4. Nothing else changes in this ticket. No restructuring, no renames.

**Verify:** root `pytest` passes; `python scripts/smoke_backend.py` passes;
`cd backend && pytest` passes; `frontend/` and `site/` `npm test` pass.

### M.1 — One FastAPI service

Goal: a single uvicorn process serves both API surfaces.

1. Root `pyproject.toml`: no changes to the `carepath` package config. The interpreter
   backend stays where it is and keeps its own `backend/pyproject.toml`; the combined
   env simply installs both: `pip install -e ".[dev]" -e "./backend[dev]"`. Confirm the
   resolver accepts both dependency sets on Python 3.12 (backend requires >=3.12).
2. Extend `apps/api/carepath/main.py`:
   - `app.include_router(api_router)` and `app.include_router(ws_router)` from
     `app.api` (the interpreter package is importable as `app` once installed). Register
     routers **before** the `app.mount("/", StaticFiles(...))` call so routes win.
   - Extend the existing lifespan: after scriber warmup, run the interpreter startup
     sequence exactly as `backend/app/main.py` does today — `validate_runtime_settings()`,
     `init_db()`, then in a DB session `seed_glossary(db)` and
     `crud.purge_old_sessions(db, settings.retention_days)`.
   - Do **not** add the interpreter's CORSMiddleware; the scriber's origin-guard +
     CORS config governs the combined app.
3. Leave `backend/app/main.py` untouched — it remains the standalone dev/test app, and
   the interpreter pytest suite keeps running against it unmodified.
4. Route collision check: scriber owns `/api/v1/*`; interpreter owns `/api/health`,
   `/api/sessions*`, `/api/turns*`, `/api/admin/*`, `/ws/sessions/*`. `/api/health` and
   `/api/v1/health` are distinct — keep both.

Watch-outs:
- WebSocket route through the combined app: verify `/ws/sessions/{id}` accepts a
  connection (the interpreter e2e covers this in M.5's CI wiring; here a manual
  `pytest`-style check or a small added test against the combined app is enough).
- The scriber origin-guard middleware only rejects when `CORS_ORIGINS` is set and the
  Origin header mismatches — document in `.env.example` (M.2) that local Vite dev
  origins (`http://localhost:5173`) must be listed when developing against it.

**Verify:** `uvicorn carepath.main:app --app-dir apps/api` boots keyless (env:
`PROVIDER_MODE=mock`, `ASR_PROVIDER=mock`, `ALLOW_MOCK_ASR=true`, `LLM_PROVIDER=offline`)
and answers `GET /api/v1/health` **and** `GET /api/health`; root `pytest`;
`python scripts/smoke_backend.py`; `cd backend && pytest`; add one combined-app test
(root `tests/test_combined_app.py`) asserting both health endpoints and a WebSocket
handshake on a created session — this test is the ticket's artifact.

### M.2 — Config and env unification

1. Rewrite `.env.example` as one documented file: shared section (nothing collides —
   verified), scriber section (ASR_*, GIPFORMER_*, LLM_*, CORS_ORIGINS, TEAM_CODE,
   SOAP_RATE_LIMIT_*), interpreter section (PROVIDER_MODE, ADMIN_TOKEN,
   CONFIDENCE_THRESHOLD, RETENTION_DAYS, DATABASE_URL, MAX_TURN_AUDIO_BYTES, provider
   models/keys marked "later track — mock mode needs none").
2. Defaults must produce a keyless boot: `PROVIDER_MODE=mock`, `LLM_PROVIDER=offline`
   documented as the demo profile. Keep `.env.local.example` / `.env.ckey.example`
   consistent or fold them in — fewest files wins, but don't break
   `scripts/setup_local.ps1`, which copies `.env.local.example`.
3. sqlite `DATABASE_URL` default stays (ephemeral on HF Space is acceptable for the
   mock demo; note this in the file).

**Verify:** fresh env from the new `.env.example` defaults boots the combined app
keyless; `python scripts/smoke_backend.py`; `cd backend && pytest`.

### M.3 — Rebrand `site/` to unified CarePath — **ALREADY DONE on the interpreter branch**

This ticket was executed by claude-fable-5 directly on `carepath-interpreter-demo`
before the merge (commit(s) touching `site/` after S.8): brand is now "CarePath"
(logo/favicon/titles/package `carepath-site`), the landing is a two-module story
(hero + module tiles + a `#scribe` chapter with a scripted `ScribeShowcase`
ASR→correction→SOAP walkthrough), and all tests/build/e2e are green.

**Your job in this ticket is verification only:** from `site/` run `npm run lint`,
`npm test`, `npm run build` (diacritics gate), `npm run e2e`; grep gate:
`grep -ri "carepath translate" site/src` returns nothing. Fix anything the merge broke;
otherwise commit nothing and move on.

### M.4 — Port the Scribe tool into `site/`, retire the old frontends

1. Rebuild the `apps/web/app` tool (record/upload audio → raw transcript → corrected
   transcript → SOAP draft with retrieved terms) as a React view inside `site/`, using
   the site's design system and `strings.ts` i18n.
2. Routing: `site/` has no router — add a **hash route** (`#/scribe`) with a small
   `location.hash` switch in `App.tsx`. No router dependency, no server-side SPA
   fallback needed. Note: the landing already has a `#scribe` **anchor** (the Scribe
   overview chapter with the scripted `ScribeShowcase`) — keep it, and add a "Mở công
   cụ Scribe / Open the Scribe tool" CTA inside that chapter linking to the `#/scribe`
   tool route.
3. API calls (see `apps/web/app.js` on `origin/main` for the exact flow):
   - `GET {base}/api/v1/health` for the status badge,
   - `POST {base}/api/v1/soap-notes` (multipart file upload),
   - base URL from `VITE_API_BASE`, defaulting to `""` (same-origin, matching M.5).
   - Handle 400 (bad audio), 413/oversize, and 429 rate-limit responses with bilingual
     messages; support an optional `X-Team-Code` header from a `VITE_TEAM_CODE` env or
     input field (it bypasses the scriber's rate limit — never hardcode a value).
4. Mic/consent: the scribe records clinician dictation. Reuse the site's existing
   consent-gate pattern before any `getUserMedia` call (invariant 5) — file upload
   needs no consent gate.
5. Delete `apps/web/` and `apps/web-next/` entirely (git history preserves them).
   Remove now-dead references: the `app.mount("/", StaticFiles(directory=WEB_DIR...))`
   block keeps working until M.5 swaps the directory — if `WEB_DIR` points at the
   deleted `apps/web`, make the mount conditional on the directory existing so the API
   still boots; M.5 finishes the job.

**Verify:** `site/` lint + test + build + e2e green (add at least one e2e that walks
the scribe route against a mocked fetch or the local keyless API); combined app still
boots; `git ls-files apps/web apps/web-next` returns nothing.

### M.5 — Serve the frontends from the API

1. `frontend/` (interpreter console): set Vite `base: "/console/"`, make its API base
   same-origin-relative in production (keep the localhost dev default working).
2. Combined app static serving, in this order after all routers:
   - `app.mount("/console", StaticFiles(directory=<frontend/dist>, html=True))`
   - `app.mount("/", StaticFiles(directory=<site/dist>, html=True))`
   - Directories configurable via env (`SITE_DIST_DIR`, `CONSOLE_DIST_DIR`) with those
     defaults; mounts are skipped with a logged warning when the dir is missing (dev
     and CI run the Vite dev servers instead).
3. Landing links: Interpreter module CTA → `/console`, Scribe CTA → `#/scribe`.
4. WebSocket URL in the console must derive from `window.location` when served
   same-origin (ws/wss scheme).

**Verify:** build both frontends, boot the combined app keyless, manually fetch `/`,
`/console/`, `/api/health`, `/api/v1/health`; `frontend/` mock-mode Playwright e2e
green; `site/` e2e green.

### M.6 — One CI workflow

Merge into a single `.github/workflows/ci.yml` (keep `keepalive.yml` as-is) with jobs:

1. `scriber`: Python 3.12, `pip install -e ".[dev]"`, root `pytest`,
   `python scripts/smoke_backend.py`.
2. `interpreter-backend`: `pip install -e "./backend[dev]"`, `ruff check backend`,
   backend `pytest`, eval regression run.
3. `combined-app`: install both packages, run the M.1 combined-app test + keyless boot
   check.
4. `frontend`: existing lint + vitest job.
5. `site`: existing lint + vitest + build (diacritics) job.
6. `e2e`: existing Playwright jobs for `frontend/` (against `PROVIDER_MODE=mock`
   backend) and `site/` — preserve their current setup from the interpreter branch's
   ci.yml (S.7 wiring).

**Verify:** `git push` the branch and confirm all CI jobs green, or run each job's
commands locally in a clean venv/node_modules if CI isn't available to you.

### M.7 — Docker / deploy

1. Multi-stage `Dockerfile`:
   - `node:22-slim` stage: `npm ci && npm run build` for `site/` and `frontend/`
     (frontend built with `base=/console/`; site build runs the diacritics gate).
   - Python stage (keep the existing base, env, Gipformer int8 pre-download exactly as
     today): additionally `pip install ./backend`, copy the two dist folders, set
     `SITE_DIST_DIR`/`CONSOLE_DIST_DIR`, same `CMD` (port 7860).
2. Update `docs/deploy.md` and `README.hf-space.md`: one Space serves the landing,
   console, scribe, and both APIs; document the interpreter env vars (mock defaults, ADMIN_TOKEN
   note: the combined app runs `validate_runtime_settings`, which only enforces
   ADMIN_TOKEN when `PROVIDER_MODE=cloud`).
3. `apps/web-next` is gone — remove Vercel references from docs; note the old Vercel
   project can be deleted.

**Verify:** `docker build .` succeeds; `docker run` with no API keys boots and serves
`/`, `/console/`, `/api/health`, `/api/v1/health`, and a mock `POST /api/v1/soap-notes`
(smoke-style WAV) — mirror what `scripts/check_goal5_deploy.ps1` checks where practical.

### M.8 — Docs

1. Rewrite `README.md` for the unified product: what CarePath is (two modules), local
   quickstart (one venv, both packages, combined uvicorn command, both frontends),
   keyless demo profile, test commands, deploy pointer.
2. Update `AGENTS.md`: unified command list, invariants unchanged, plan pointers —
   `PLAN.md` and `DEMO-SITE-PLAN.md` marked historical (do not delete), `MERGE-PLAN.md`
   marked done, `JUDGE.md` referenced as the review protocol.
3. Sweep for stale references: `grep -ri "web-next\|apps/web\b\|carepath translate"`
   across docs and configs; fix stragglers.

**Verify:** every command in the new README executes as written on a clean checkout;
full Verify inventory from §3 green one last time.

---

## 4. Out of scope — do not do

- No real interpreter providers (no Gipformer-for-interpreter, no ckey MT/reviewer, no
  new keys). Mock stays.
- No changes to the GEC training pipeline, notebooks, `scripts/gec/`, or eval datasets.
- No auth/multi-tenant, no analytics, no new runtime dependencies beyond what this plan
  names (the hash route explicitly avoids react-router).
- No visual redesign of the S.8 system — extend it.
