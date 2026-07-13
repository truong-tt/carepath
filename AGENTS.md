# Agent instructions — CarePath unified

CarePath is one unified medical AI product with two clearly separated user-facing modules:

1. **Ghi chép bệnh án AI**
   Internal/technical term: AI Scribe / scriber
   Backend: `scribe/carepath`, `/api/v1/*`
   Purpose: listen to a consultation and help generate structured clinical notes.

2. **Phiên dịch khám bệnh trực tiếp**
   Internal/technical term: Medical Interpreter / interpreter
   Backend: `interpreter/app`, `/api/*` + `/ws/*`
   Purpose: live two-way interpretation between Vietnamese doctors and English-speaking patients.

The app is served by one FastAPI process plus two Vite frontends:

* `scribe/frontend/` at `/`
* `interpreter/frontend/` at `/phien-dich-y-khoa/` (`/console/` is a legacy redirect)

## Interpreter status

After restructure Phase 7, the Interpreter is on hold. Accept only bug fixes,
safety fixes, and required operational maintenance there; new product work is
focused on the Scribe training track unless the owner explicitly reopens it.

`docs/history/PLAN.md` and `docs/history/DEMO-SITE-PLAN.md` are historical build
plans for the interpreter and demo site. `docs/history/MERGE-PLAN.md` is the
executed unification plan, M.0–M.8 done, and `docs/history/JUDGE.md` is its
review protocol.
`docs/research.md` holds the interpreter safety background.

## Product UX contract

CarePath must be Vietnamese-first.

The target users may include Vietnamese doctors who are not comfortable with English medical software terms. Therefore, the UI must explain workflows by user intent, not by English product names.

### Primary user-facing labels

Use these as primary UI labels:

* `Ghi chép bệnh án AI`
* `Phiên dịch khám bệnh trực tiếp`

Use these as primary CTAs:

* `Bắt đầu ghi chép`
* `Bắt đầu phiên dịch`

Use this homepage framing:

```text
Bạn muốn hỗ trợ việc gì hôm nay?
```

### Secondary/internal labels

The following English terms may appear only as secondary helper text, developer labels, comments, docs, or internal route/component names:

* Scribe
* AI Scribe
* Interpreter
* Medical Interpreter
* Console
* Transcript
* Encounter
* Session

Do not use `Scribe` or `Interpreter` as primary labels on user-facing screens.

### Required distinction between the two modules

The landing page must make it obvious that these are two different workflows:

#### Ghi chép bệnh án AI

Explain as:

```text
AI nghe buổi khám và tạo ghi chú y khoa có cấu trúc.
```

Use when:

```text
Phù hợp khi bác sĩ muốn giảm thời gian nhập liệu sau khám.
```

Clarify that the doctor must review the output before use.

#### Phiên dịch khám bệnh trực tiếp

Explain as:

```text
Dịch hai chiều giữa bác sĩ tiếng Việt và bệnh nhân tiếng Anh trong lúc khám.
```

Use when:

```text
Phù hợp khi bác sĩ và bệnh nhân không cùng ngôn ngữ.
```

Clarify that the system translates only and must not provide medical advice.

### Every user-facing screen must answer

1. Tôi đang dùng chức năng nào?
2. Chức năng này giúp việc gì?
3. Tôi cần bấm gì tiếp theo?
4. Có rủi ro hoặc giới hạn nào bác sĩ cần biết không?

### Vietnamese copy rules

* Vietnamese text must be clear, short, and professional.
* Preserve Vietnamese diacritics.
* Keep text NFC-normalized.
* Avoid unnecessary English.
* Avoid startup/marketing buzzwords on clinical workflow screens.
* Prefer concrete action language over abstract product names.

Good:

```text
Ghi chép bệnh án AI
Phiên dịch khám bệnh trực tiếp
Bắt đầu ghi chép
Bắt đầu phiên dịch
Bác sĩ nói tiếng Việt, bệnh nhân nghe tiếng Anh
```

Avoid as primary UI:

```text
Scribe
Interpreter
Session
Encounter
Transcript
Start session
Launch interpreter
```

## Non-negotiable safety invariants

This file is the current safety contract. `docs/history/PLAN.md §2` preserves
the original MVP source for historical context.

1. Translate-only: never generate medical advice, diagnoses, or drug recommendations.
2. High/critical-risk turns are blocked from patient display and TTS until doctor confirms.
3. Low-confidence output is always visibly flagged, never silently delivered.
4. Raw audio is never persisted. Use memory-only processing. No audio columns, no temp files.
5. No mic capture before recorded consent.
6. On any pipeline or reviewer failure, fail closed: keep the turn blocked, show the doctor raw source and translation, offer escalation. Never fail open to the patient.

## Implementation workflow for agents

For UX or product-flow changes, do not implement immediately.

First produce or update a plan in `docs/ux-redesign-carepath.md` with:

1. Current UX problem
2. Proposed flow
3. Affected routes/pages/components
4. Vietnamese-first copy
5. Implementation stories
6. Dependencies between stories
7. Acceptance criteria
8. Validation commands
9. Risks and fallback behavior

Then implement one story at a time.

### Recommended story order for UX redesign

1. Update Vietnamese-first product naming and copy.
2. Redesign the landing page into two clear workflow cards.
3. Add or clarify separate entry routes for the two modules.
4. Add pre-start onboarding/explanation screens.
5. Improve empty/loading/error states in Vietnamese.
6. Run QA for mobile, accessibility, safety copy, and route regressions.

Do not combine homepage redesign, routing changes, and audio/backend logic changes in one large patch.

### Agent behavior

* Keep changes small and focused.
* Preserve existing working functionality.
* Do not rewrite backend, audio, risk, or websocket logic unless the current story explicitly requires it.
* Do not introduce new dependencies without documenting why.
* Prefer existing components and styling patterns.
* When changing user-facing Vietnamese text, check diacritics and consistency.
* When changing risk-engine behavior, update fixtures and evals.
* When changing product copy only, avoid touching medical logic.

## Commands

### Combined service

```bash
uvicorn carepath.main:app --app-dir scribe --reload
```

Requires:

```bash
pip install -e ".[dev]" -e "./shared" -e "./interpreter[dev]"
```

### Scriber and combined tests

```bash
pytest
python scripts/smoke_backend.py
python scripts/build_term_artifacts.py --check
```

### Interpreter backend alone

```bash
cd interpreter && uvicorn app.main:app --reload
pytest
```

### Console

```bash
cd interpreter/frontend && npm run dev
npm test
npx playwright test
```

### Demo site

```bash
cd scribe/frontend && npm run dev
npm test
npm run build
npm run e2e
```

`npm run build` is also the diacritics gate.

### Full mock-mode run

Set this in `.env`:

```bash
PROVIDER_MODE=mock
```

Mock mode must work with no API keys.

### Eval regression

```bash
python interpreter/eval/run_eval.py --set interpreter/eval/fixtures/eval_starter.tsv --providers mock
```

## Conventions

* Python 3.12.
* Python code must be ruff-formatted and type-hinted.
* Use pure functions for normalization and risk rules.
* TypeScript must be strict.
* Components should be small.
* Keep state minimal: context/zustand is allowed, Redux is not.
* `shared/carepath_shared/terms/medical_terms.json` is the canonical medical
  term source. Regenerate `data/medical_lexicon.json` and
  `interpreter/app/glossary/data/seed_glossary.csv` with
  `python scripts/build_term_artifacts.py`; do not hand-edit generated artifacts.
* Risk lexicons under `interpreter/app/risk/lexicons/` remain separate
  interpreter safety data. Clinicians edit data, not code.
* Every risk-engine behavior change updates `interpreter/eval/fixtures/risk_cases.jsonl`.
* The fixture run is the test.
* Zero misses on critical fixtures is a hard gate.
* Secrets only via env.
* `.env` is gitignored.
* `.env.example` must stay current.
* No new dependencies without noting why in the PR.
* Vietnamese text is data, not decoration: always NFC-normalized, diacritics preserved.
* Tests must include diacritic-stripped variants where matching allows it.

## Acceptance criteria for UX clarity changes

A UX clarity change is not done un  less all of the following are true:

1. A Vietnamese doctor can understand the two workflows without knowing the words `Scribe` or `Interpreter`.
2. The landing page clearly separates:

   * `Ghi chép bệnh án AI`
   * `Phiên dịch khám bệnh trực tiếp`
3. Each workflow has a distinct CTA.
4. Each workflow explains when to use it.
5. English terms appear only as secondary helper text, not primary labels.
6. Mobile layout remains clear.
7. Existing core functionality still works.
8. Safety invariants remain unchanged.
9. Build and relevant tests pass.

<!-- HARNESS:START -->
## Harness workflow

This repository uses Repository Harness for durable task intake, proof, and
decision records. This block adds to the CarePath instructions above; it does
not replace them.

Priority, highest first:

1. The current user request and the safety and product rules in this file.
2. Current product contracts in `docs/product/`.
3. Selected story packets in `docs/stories/` and accepted decisions in
   `docs/decisions/`.
4. Executable tests and the Harness proof matrix.
5. `docs/history/` as context only.

Before any task, read `README.md`, `docs/HARNESS.md`, and
`docs/FEATURE_INTAKE.md`; then run
`.\scripts\bin\harness-cli.exe query matrix` on Windows. Classify and record
the task as `tiny`, `normal`, or `high-risk` before changing code.

- Tiny work records an intake and runs the relevant quick proof.
- Normal work also updates one story packet and its proof record.
- High-risk work uses `docs/templates/high-risk-story/`, records a decision
  when it changes architecture, data, safety, APIs, or validation, and waits
  for human direction if its scope is ambiguous.
- A UX or product-flow task still must first update
  `docs/ux-redesign-carepath.md`, then follow the Harness lane requirements.
- Before a step that could use an external tool, query the available provider:
  `.\scripts\bin\harness-cli.exe query tools --capability <capability> --status present`.
  A missing provider is a clean skip, never a reason to invent a dependency.
- Finish normal and high-risk work with a Harness trace that records the real
  validation outcome and any friction. Do not claim proof that was not run.
<!-- HARNESS:END -->
