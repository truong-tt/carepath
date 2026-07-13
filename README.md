# CarePath

A clinical AI suite for Vietnamese clinics with two distinct products and one
principle: **the clinician stays in control.**

- **Scribe** (`scribe/carepath`, routes `/api/v1/*`) — upload consultation
  audio, get a Gipformer ONNX transcript with retrieval-assisted term
  correction and a draft Vietnamese SOAP note for clinician review. Works
  keyless with mock ASR + the offline LLM; production uses a CKey
  OpenAI-compatible LLM.
- **Interpreter** (`interpreter/app`, routes `/api/*` + `/ws/*`) — live
  Vietnamese ↔ English interpreting with risk gating, read-back confirmation,
  interpreter escalation, and an admin review page. Runs in deterministic
  mock mode with zero API keys; cloud providers are a later track.

Frontends, all served by the same API in production:

- `scribe/frontend/` — the public demo site (landing at `/`, working Scribe tool at
  `/ghi-chep-lam-sang/`). Vietnamese default, English toggle, full diacritics enforced
  at build time.
- `interpreter/frontend/` — the interpreter app, served at `/phien-dich-y-khoa/`.

One FastAPI process serves both APIs and both frontends. The executed
unification plan and its review protocol are archived in `docs/history/`.

## Quickstart (keyless demo profile)

Python 3.12 and Node 22.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]" -e ".\shared" -e ".\interpreter[dev]"
Copy-Item .env.local.example .env

# Build the frontends the API will serve
cd scribe/frontend; npm ci; npm run build; cd ../..
cd interpreter/frontend; npm ci; npm run build; cd ../..

# One process, everything on http://127.0.0.1:8000
uvicorn carepath.main:app --app-dir scribe --reload
```

Then open `http://127.0.0.1:8000/` (demo site), `/ghi-chep-lam-sang/` (Scribe tool),
`/phien-dich-y-khoa/` (interpreter app). `GET /api/v1/health` and `GET /api/health`
report both modules.

For frontend development, run the Vite dev servers instead
(`npm run dev` in `scribe/frontend/` or `interpreter/frontend/`); the API skips missing dist folders.

## Tests

```powershell
pytest                          # scriber + combined-app suite (repo root)
python scripts/smoke_backend.py # scriber keyless smoke
python scripts/build_term_artifacts.py --check # canonical term-data drift gate
cd interpreter; pytest          # interpreter suite
python interpreter/eval/run_eval.py --set interpreter/eval/fixtures/eval_starter.tsv --providers mock
cd interpreter/frontend; npm test; npx playwright test
cd scribe/frontend; npm test; npm run build; npm run e2e
```

## Development Harness

CarePath uses Repository Harness to keep agent work reviewable and its proof
durable. Before a task, read `AGENTS.md`, `docs/HARNESS.md`, and
`docs/FEATURE_INTAKE.md`, then inspect the current proof matrix:

```powershell
.\scripts\bin\harness-cli.exe query matrix
```

The local Harness database is intentionally ignored by Git. Initialize it once
per clone, classify the task, and record a trace after validation:

```powershell
.\scripts\bin\harness-cli.exe init
.\scripts\bin\harness-cli.exe intake --type "Change request" --summary "<work>" --lane normal
.\scripts\bin\harness-cli.exe trace --summary "<work>" --outcome completed
```

`docs/product/` is the current CarePath contract, `docs/stories/` holds
story-sized work, and `docs/decisions/` records durable tradeoffs. The
historical plans remain context, not the default source of truth.

## Real providers

- Scriber ASR: Gipformer ONNX downloads on first use (`ASR_PROVIDER=gipformer`,
  the default). `scripts/setup_local.ps1` automates the venv + env setup.
- Scriber LLM: `LLM_PROVIDER=ckey` + `LLM_API_KEY` (see `.env.ckey.example`).
- Interpreter: `PROVIDER_MODE=mock` is the supported mode today. The cloud
  mode (`ANTHROPIC_API_KEY`/`OPENAI_API_KEY`) exists behind the provider
  abstraction but is not wired into a deployment yet.

## Deploy

One Hugging Face Space (Docker) serves everything: see `docs/deploy.md`.

## Repo map

- `scribe/carepath` — scriber runtime API (ASR + retrieval + LLM serving)
- `shared/carepath_shared/terms/medical_terms.json` — canonical term source;
  regenerate its serving artifacts with `python scripts/build_term_artifacts.py`
- `scribe/training/gec` — Scribe-only DARAG training/eval package (never imported by serving)
- `interpreter/` — interpreter API, console, tests, and safety eval
- `scribe/frontend/` — the public site; `scribe/tests/` — scriber + combined-app tests
- `scribe/training/scripts`, `scribe/training/notebooks/` — Scribe-only GEC training pipeline;
  `interpreter/eval/` remains the Interpreter safety harness; `docs/` — background + deploy
- `docs/README.md` — task-first documentation map; `docs/history/` — preserved
  build plans and unification review history
