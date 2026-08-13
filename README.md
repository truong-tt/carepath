# CarePath

**Healthcare in Vietnam, without navigating it alone.**

CarePath is an AI-first care navigator for foreign tourists and expats seeking
outpatient care in Vietnam. It is one journey, not a set of tools:

```text
Find care → Prepare → Visit → Verify → Paperwork → Follow-up
```

The differentiator is the fourth step. A machine translation of a dose is still
a machine translation of a dose, so anything carrying a drug name, a dose or an
allergy is **withheld from the patient until a clinician confirms it**.
Translation is not the safety mechanism; verification is.

## Who reads what

Language follows the audience, not the company
(`docs/decisions/0023-foreign-patient-care-navigator.md`):

| Surface | Route | Language |
| --- | --- | --- |
| Homepage | `/` | English, full Vietnamese behind the toggle |
| The care journey | `/get-care/` | English |
| The care episode | `/my-carepath/` | English |
| Bilingual visit | `/kham-song-ngu/` | Vietnamese clinician ↔ English patient |
| Paperwork reader | `/dich-giay-to/` | Vietnamese — the clinician confirms each line |
| Clinical notes | `/ghi-chep-lam-sang/` | Vietnamese |
| Public demo hub | `/thu-nghiem/` | Vietnamese |

Clinician-facing elements stay Vietnamese even inside an English screen: the
person acting on a risk label is the clinician.

`/get-care/` and `/my-carepath/` make **no network request at all**. The pitch
completes on a venue network that does not exist, and
`scribe/frontend/tests/journey.spec.ts` proves it by aborting every request for
the whole run and then walking the journey end to end.

## What runs underneath

Two backend modules and one FastAPI process serve everything:

- **`scribe/carepath`** (`/api/v1/*`) — consultation audio in, Gipformer ONNX
  transcript with retrieval-assisted term correction, and a draft Vietnamese
  SOAP note for clinician review. Works keyless with mock ASR + the offline
  LLM; production uses a CKey OpenAI-compatible LLM.
- **`interpreter/app`** (`/api/*` + `/ws/*`) — the risk engine, the clinician
  confirmation state machine, read-back, escalation, and the document reader.
  Runs deterministically in mock mode with zero API keys.

`scribe/frontend/` is the only frontend. The separate interpreter console was
deleted once the bilingual visit replaced it; `/phien-dich-y-khoa/` and
`/console/` are deliberate 404s.

The names are internal. On any user-facing screen they are capabilities inside
the journey above, never products with their own marketing.

## Quickstart (keyless demo profile)

Python 3.12 and Node 22.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]" -e ".\shared" -e ".\interpreter[dev]"
Copy-Item .env.local.example .env

# Build the frontend the API will serve
cd scribe/frontend; npm ci; npm run build; cd ../..

# One process, everything on http://127.0.0.1:8000
uvicorn carepath.main:app --app-dir scribe --reload
```

Open `http://127.0.0.1:8000/`. `GET /api/v1/health` and `GET /api/health`
report the two modules.

For frontend work run the Vite dev server instead (`npm run dev` in
`scribe/frontend/`); the API skips a missing dist folder. `/get-care/` and
`/my-carepath/` need no backend at all.

## Tests

```powershell
pytest                          # scriber + combined-app suite (repo root)
python scripts/smoke_backend.py # scriber keyless smoke
python scripts/build_term_artifacts.py --check # canonical term-data drift gate
cd interpreter; pytest          # interpreter suite
python interpreter/eval/run_eval.py --set interpreter/eval/fixtures/eval_starter.tsv --providers mock
cd scribe/frontend; npm test; npm run build; npm run e2e
```

`npm run build` is also the Vietnamese diacritics gate, and
`npm run validate:deploy` checks that every SPA route is reachable on **both**
hosts — Vercel and the Space. A route registered on only one 404s in production
while every local test passes; that has happened.

## Real providers

- Scriber ASR: Gipformer ONNX downloads on first use (`ASR_PROVIDER=gipformer`,
  the default). `scripts/setup_local.ps1` automates the venv + env setup.
- Scriber LLM: `LLM_PROVIDER=ckey` + `LLM_API_KEY` (see `.env.ckey.example`).
- Interpreter: `PROVIDER_MODE=mock` is keyless and deterministic. `demo` adds
  the scripted document scenario; `ckey` reads real documents and additionally
  requires a non-default `ADMIN_TOKEN` or the app refuses to boot.

## Deploy

`docs/deploy.md`. Two hosts, and the project names do not match the domain —
read it before concluding a deploy is broken.

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
historical plans in `docs/history/` remain context, not a source of truth.

## Repo map

- `scribe/frontend/` — the whole public surface: landing, care journey, episode,
  bilingual visit, paperwork reader, clinical notes, demo hub
- `scribe/carepath/` — scriber runtime API (ASR + retrieval + LLM serving)
- `interpreter/` — risk engine, confirmation state machine, safety eval
- `shared/carepath_shared/terms/medical_terms.json` — canonical term source;
  regenerate its serving artifacts with `python scripts/build_term_artifacts.py`
- `scribe/training/` — Scribe-only GEC/SOAP training and eval, never imported
  by serving code
- `docs/README.md` — task-first documentation map
- `docs/history/` — preserved build plans and unification review history
