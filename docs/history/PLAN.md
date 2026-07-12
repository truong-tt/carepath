# CarePath Interpreter — MVP Implementation Plan

Live Vietnamese ↔ English medical interpreter for outpatient consultations in Vietnam.
This plan turns [docs/research.md](docs/research.md) into buildable tickets. Research says
what and why; this file says how. When they conflict, this file wins for implementation,
research wins for safety/compliance intent.

**Executor:** codex-5.5. Work phases in order. Within a phase, tickets are ordered by
dependency. Every ticket ends green: `pytest` + frontend tests pass, mock-mode e2e works.

---

## 1. Product in one paragraph

A tablet/laptop web app used during a consultation between a Vietnamese-speaking doctor
and an English-speaking patient (and the reverse). Push-to-talk per speaker → server ASR →
text normalization → glossary-aware MT → rules-based risk classifier → bilingual transcript.
Low-risk turns speak out immediately (browser TTS). High-risk turns (dose, allergy, negation,
laterality, red-flags) are **blocked until the doctor confirms a read-back** of the critical
entities. Very-high-risk content prominently routes to a human interpreter. It is a
translation-and-verification aid — never a diagnostic or advice tool.

## 2. Safety invariants — never violate, in any ticket

1. **No autonomous medical content.** The system only translates and surfaces what was said.
   Post-filter any provider output that adds advice, diagnoses, or drug recommendations.
2. **No critical turn reaches the patient unconfirmed.** Risk tier `high`/`critical` blocks
   TTS + patient-facing display until doctor confirms or corrects.
3. **No silent low-confidence output.** Below threshold → visible flag + re-ask/typed
   fallback. Never emit a low-confidence dose/allergy/negation quietly.
4. **Privacy mode is default-on.** Raw audio is processed in memory and never written to
   disk or DB. Only text + metadata persist. (Vietnam Decree 13/PDP Law; HIPAA-shaped.)
5. **Consent before capture.** No mic capture until session consent + AI-use disclosure is
   recorded ("AI translation, may contain errors, you may request a human interpreter").
6. **Interpreter escalation is always one tap away** and never hidden by any state.
7. **Everything auditable.** Every high/critical turn logs confidence, risk spans, doctor
   action (confirm/correct/escalate), timestamps.

## 3. Scope

**In (MVP):** dual push-to-talk; Vi↔En ASR+MT; bilingual live transcript; risk highlighting;
confirmation/read-back gate; low-confidence handling; interpreter-escalation flow; consent +
disclosure; per-turn feedback flag; privacy mode; deterministic mock providers; evaluation
harness; minimal review page.

**Out (explicitly — do not build):** diagnosis/advice/QA of any kind, visit summaries,
emergency triage, informed-consent workflows, mental-health flows, pediatric emergency,
model fine-tuning (adapters make it a later swap), mobile native apps, auth/multi-tenant
(single shared device assumption; one env-var admin token for the review page).

## 4. Architecture & stack (decided — don't re-litigate)

```
Browser (React+TS+Vite)
  ├─ push-to-talk mic capture (MediaRecorder) ──┐ WebSocket (audio chunks + JSON events)
  ├─ bilingual transcript + risk highlighting   │
  ├─ confirm/read-back modal, escalate button   │
  └─ TTS via browser speechSynthesis            ▼
Backend (Python 3.12, FastAPI, uvicorn)
  session/turn orchestrator
  ├─ ASRProvider    (mock | cloud)     ┐
  ├─ MTProvider     (mock | LLM)       │ swappable adapters (Protocol classes)
  ├─ ReviewerProvider (mock | LLM)     ┘
  ├─ normalizer     (rules: numbers, units, dates, diacritics)
  ├─ risk engine    (rules + lexicons — deterministic, no ML in MVP)
  └─ SQLite (sessions, turns, feedback — no audio)
```

| Decision | Choice | Why (one line) |
|---|---|---|
| Backend | Python 3.12 + FastAPI + WebSocket | Best ecosystem for audio/NLP libs; async streaming |
| Frontend | React 18 + TypeScript + Vite | Standard, fast, codex-friendly |
| Storage | SQLite via `sqlite3`/SQLModel | Single-clinic MVP; zero ops; swap to Postgres later |
| ASR (real) | OpenAI `gpt-4o-transcribe` (Vi + En), lang hint per turn | Good Vi support, confidence-ish via logprobs; adapter makes PhoWhisper/VietMed fine-tune a later swap |
| MT (real) | Claude `claude-sonnet-5` with glossary-in-prompt + strict "translate only" system prompt | Day-1 placeholder per research (generic API acceptable); glossary pinning + rule post-checks close the gap until a MedEV fine-tune |
| Reviewer (real) | Claude `claude-sonnet-5`, second pass on high-risk turns only | Back-translates + extracts critical entities for read-back; cost-bounded by risk gating |
| TTS | Browser `speechSynthesis` (`vi-VN`, `en-US`) | Native, free, offline; server TTS adapter is a later ticket if voice quality fails in testing |
| Risk engine | Deterministic rules + lexicons, **not** ML NER | Testable, explainable, zero-latency; ViHealthBERT NER is a post-MVP upgrade behind the same interface |
| Mock mode | `PROVIDER_MODE=mock` env → deterministic canned providers | CI, demos, and frontend dev need no keys and no network |

Monorepo layout (plain folders, no workspace tooling):

```
/backend
  app/main.py            FastAPI app, WS endpoint
  app/config.py          env settings (pydantic-settings)
  app/db.py              SQLite setup + models
  app/session.py         session/turn orchestrator (the pipeline)
  app/normalize.py       text normalization rules
  app/risk/engine.py     risk classifier (rules)
  app/risk/lexicons/     *.json data files (see §7)
  app/providers/base.py  Protocol interfaces
  app/providers/mock.py  deterministic mocks
  app/providers/openai_asr.py
  app/providers/claude_mt.py
  app/glossary/          store + seed data + import script
  tests/
/frontend
  src/                   components, ws client, tts, state (zustand or plain context)
  tests/                 vitest + one Playwright e2e (mock mode)
/eval
  run_eval.py            CLI harness
  fixtures/              risk-rule fixtures, golden turns, eval TSVs
/docs
  research.md            source research report
PLAN.md  AGENTS.md  README.md  .env.example
```

## 5. Data model (SQLite)

```sql
sessions(id TEXT PK, created_at, status TEXT,          -- active|ended|escalated
         consent_json TEXT,                            -- who consented, disclosure shown, ts
         privacy_mode INTEGER DEFAULT 1, escalated_at)

turns(id TEXT PK, session_id FK, seq INTEGER,
      speaker TEXT,            -- doctor|patient
      src_lang TEXT, tgt_lang TEXT,
      source_text TEXT, normalized_text TEXT, translation TEXT,
      asr_confidence REAL, mt_confidence REAL,
      risk_tier TEXT,          -- low|medium|high|critical
      risk_spans_json TEXT,    -- [{start,end,kind,severity,term}]
      readback_json TEXT,      -- reviewer output for high/critical: entities + back-translation
      status TEXT,             -- pending|delivered|awaiting_confirm|confirmed|corrected|blocked|escalated
      corrected_text TEXT, created_at)

feedback(id TEXT PK, turn_id FK, reason TEXT,          -- wrong_term|wrong_meaning|missing|other
         comment TEXT, created_at)
```

No audio column anywhere. That's a feature.

## 6. API contract

REST (JSON):

```
POST   /api/sessions                 {consent:{...}}            → {session_id}
POST   /api/sessions/{id}/end                                   → 204
POST   /api/sessions/{id}/escalate                              → 204   (sets status, logs)
DELETE /api/sessions/{id}            hard-deletes session+turns → 204   (PDP deletion right)
GET    /api/sessions/{id}/transcript                            → [turn, ...]
POST   /api/turns/{id}/confirm       {edited_translation?}      → turn  (unblocks TTS/display)
POST   /api/turns/{id}/feedback      {reason, comment?}         → 201
GET    /api/admin/review?risk=high&flagged=1   (X-Admin-Token)  → paged turns for review page
```

WebSocket `/ws/sessions/{id}`:

```
client→server  {type:"start_turn", speaker:"doctor", lang:"vi"}
client→server  binary audio chunks (webm/opus from MediaRecorder)
client→server  {type:"end_turn"}
client→server  {type:"text_turn", speaker, lang, text}      // typed fallback path
server→client  {type:"turn_result", turn:{...full turn row...},
                requires_confirmation:bool, low_confidence:bool}
server→client  {type:"turn_error", message, retryable:bool}
```

One in-flight turn per session (push-to-talk enforces it); reject overlapping `start_turn`.

## 7. Risk engine spec (rules + lexicons)

Deterministic pipeline over source text + translation. Each rule emits spans
`{kind, severity, term}`; tier = max severity hit. Lexicons are JSON data files in
`app/risk/lexicons/` — reviewable by clinicians without touching code.

| Rule | Fires on | Tier | Maps to research failure modes |
|---|---|---|---|
| `red_flag` | đau ngực / khó thở / chest pain / can't breathe / suicidal … | critical | #23 |
| `negation` | không / chưa / ngưng / not / no / stop / never near a medical term | high | #1, #24 |
| `dose_number` | number + unit (mg/ml/mcg/viên/gói/ống/tablet…) or fraction (nửa/half) | high | #3, #5, #16, #26 |
| `frequency_duration` | ngày X lần / X times a day / trong N ngày / for N days | high | #4, #15 |
| `allergy` | dị ứng / allergic / allergy | critical | #2 |
| `pregnancy` | mang thai / có bầu / pregnant | critical | #21 |
| `laterality` | trái / phải / left / right | high | #9 |
| `drug_name` | glossary drug hit; escalate if in LASA pair list | high (critical if LASA) | #7, #8 |
| `route` | nhỏ mắt / uống / tiêm / drops / oral / injection | high | #25 |
| `low_confidence` | ASR or MT confidence < threshold (config, default 0.7) | forces flag at any tier | #6, #17–19 |
| `number_mismatch` | digits extracted from source ≠ digits in translation | critical | cascade check |
| `negation_mismatch` | negation cue count source vs translation differs | critical | cascade check |

Tier → behavior: `low` = deliver + speak. `medium` = deliver + highlight spans.
`high` = block, show read-back (reviewer entities + back-translation), require confirm.
`critical` = block + confirm + prominent "Get human interpreter" banner.

Lexicon seed files to create (ticket 3.1): `red_flags.json`, `negation_cues.json`,
`units_forms.json`, `routes.json`, `laterality.json`, `pregnancy.json`,
`lasa_pairs.json` (~30 known pairs), `abbreviations_vi.json` (HA, TC, …).
Glossary seed: ~150 curated Vi↔En drug/term pairs committed as CSV.
Full Meddict (>64k entries) import behind `glossary/import_meddict.py` — **do not block
on it**; license unverified (research §Meddict), run when cleared.

## 8. Phases and tickets

### Phase 0 — Scaffold (research Epic 1, 16)

- **0.1 Repo scaffold.** Layout from §4; `pyproject.toml` (fastapi, uvicorn, pydantic-settings,
  sqlmodel, pytest, httpx, anthropic, openai, jiwer, sacrebleu); Vite React-TS app;
  `.env.example` (`PROVIDER_MODE`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `ADMIN_TOKEN`,
  `CONFIDENCE_THRESHOLD`); README with run commands. GitHub Actions: lint (ruff, eslint) +
  pytest + vitest. *Accept:* CI green on empty-ish repo; `uvicorn app.main:app` serves health check.
- **0.2 Provider interfaces + mocks.** `base.py` Protocols:
  `ASRProvider.transcribe(audio: bytes, lang: str) -> ASRResult(text, confidence)`;
  `MTProvider.translate(text, src, tgt, glossary_hits: list[GlossaryEntry]) -> MTResult(text, confidence)`;
  `ReviewerProvider.review(source, translation, src, tgt) -> Review(back_translation, entities: list[CriticalEntity], flags)`.
  Mocks: keyed canned responses + passthrough default; injectable error/low-confidence cases.
  *Accept:* conformance tests pass for mocks; provider chosen by `PROVIDER_MODE`.

### Phase 1 — Core loop, mock mode (Epics 2, 3, 4, 8)

- **1.1 DB + models.** §5 schema, SQLModel, session/turn/feedback CRUD. *Tests:* round-trip,
  hard delete cascades.
- **1.2 Session API + WS orchestrator.** §6 contract; pipeline = ASR → normalize (stub) →
  glossary lookup (stub) → MT → risk (stub returns `low`) → persist → emit `turn_result`.
  Typed-text path skips ASR. *Accept:* WS turn round-trips in mock mode; overlapping turn
  rejected; WS reconnect resumes session. *Tests:* contract tests with mocks, incl. dropped
  connection mid-turn.
- **1.3 Push-to-talk UI.** Two big hold-to-talk buttons (Doctor 🇻🇳 / Patient 🇬🇧),
  MediaRecorder capture → WS chunks, turn state indicator, typed-input fallback,
  bilingual transcript pane (source + translation per turn, timestamped). Browser TTS on
  `turn_result` (vi-VN/en-US voice pick with graceful no-voice fallback to text-only).
  *Accept:* full spoken round trip against mock backend; mic-permission-denied path shows
  typed fallback. *Tests:* vitest components + 1 Playwright mock-mode e2e.
- **1.4 Consent gate.** Session-start screen (Vi + En side by side): AI disclosure text,
  interpreter-right notice, consent checkboxes → `POST /api/sessions`. Mic UI unmounted
  until consent recorded. *Accept:* no WS/mic possible pre-consent; consent stored in
  `consent_json`.

### Phase 2 — Real providers (Epics 5, 6)

- **2.1 OpenAI ASR adapter.** `gpt-4o-transcribe`, per-turn lang hint, confidence derived
  from logprobs (document the derivation), timeout+retry, `turn_error` on failure.
  *Tests:* mocked HTTP; golden-audio fixture test marked `@pytest.mark.live` (skipped in CI).
- **2.2 Claude MT adapter.** `claude-sonnet-5`; system prompt: translate only, preserve
  numbers/units/negation verbatim, never add advice; glossary hits injected as constraints;
  output parsed strictly (reject non-translation content — invariant 1). *Tests:* prompt
  snapshot, parse rejection cases, glossary-term forcing against mocked API.
- **2.3 Claude reviewer adapter.** High/critical turns only: back-translate + extract
  `CriticalEntity{kind: drug|dose|frequency|route|allergen|laterality|negation, source_span,
  translated_span}` as JSON. *Tests:* schema validation, malformed-output fallback (fail
  closed → turn stays blocked, doctor sees raw source + translation).
- **2.4 Normalizer.** Vietnamese number words → digits ("một trăm hai mươi"→120,
  "nửa"→0.5), unit canonicalization (mg/ml/mcg, mi-li-gam→mg), relative dates ("sau mười
  ngày"→ "+10 days"), diacritic-stripped fallback matching for glossary. Pure functions.
  *Tests:* table-driven, ≥40 cases from research failure modes #3–5, #15–16, #26, #30.

### Phase 3 — Safety layer (Epics 9, 10, 11, 12; the heart of the product)

- **3.1 Glossary + lexicons.** SQLite-backed glossary (term_vi, term_en, kind, lasa_group),
  exact + diacritic-insensitive + fuzzy (rapidfuzz ≥90) lookup; seed CSV ~150 terms;
  lexicon JSON files from §7; `import_meddict.py` (guarded, not in CI). *Tests:* LASA
  collision cases, multi-word terms, abbreviation expansion.
- **3.2 Risk engine.** §7 rules over (normalized source, translation); returns tier + spans +
  mismatch flags. *Accept:* tiers match labeled fixtures — build `eval/fixtures/risk_cases.jsonl`
  with ≥3 cases per failure mode #1–30 from research (source of truth for behavior).
  *Tests:* the fixture run IS the test. Zero misses on critical fixtures.
- **3.3 Risk highlighting UI.** Colored spans by severity in both transcript columns;
  legend; critical spans get acknowledgment affordance. *Tests:* rendering, overlapping
  spans, a11y (contrast + non-color severity cue).
- **3.4 Confirmation/read-back flow.** High/critical: modal for doctor — source text,
  translation, reviewer's back-translation + entity table (drug/dose/frequency/route/
  laterality/negation) — actions: Confirm / Edit translation / Escalate. Patient panel +
  TTS release only on confirm (invariant 2). Edits saved to `corrected_text`, status
  `corrected`. *Tests:* dosage/allergy/negation scripted flows; doctor-edit path;
  reviewer-failure fail-closed path.
- **3.5 Low-confidence + escalation.** Below-threshold → banner "Low confidence — please
  repeat or type" + re-record/typed affordances (invariant 3). Persistent "Human interpreter"
  button → full-screen bilingual escalation card (placeholder contact copy) + session
  status `escalated` (invariant 6). *Tests:* injected low-confidence mock; escalation
  state machine.

### Phase 4 — Feedback, review, evaluation (Epics 14, 15, 17)

- **4.1 Per-turn feedback.** Flag icon per turn → reason picker (§5 enum) + comment.
  *Tests:* submit, appears in review query.
- **4.2 Review page.** Single admin route (X-Admin-Token): filter turns by risk/flagged/
  low-confidence/escalated; show source, translation, correction, feedback; CSV export.
  No dashboards, no charts. *Tests:* auth reject, pagination, export.
- **4.3 Eval harness.** `python eval/run_eval.py --set fixtures/eval_500.tsv --providers mock|real`:
  runs text-mode pipeline; computes WER (jiwer, when audio refs exist), BLEU/chrF
  (sacrebleu), and preservation checks — number/unit exact, negation polarity, laterality,
  drug-name exact, escalation correctness; emits JSON + markdown report vs thresholds
  below. Ships with a 50-row starter TSV built from research examples; the real 500-set
  is a clinical-team deliverable that drops into the same format. *Accept:* reproducible
  report; CI runs it in mock mode as regression gate.

**MVP thresholds (from research; calibrate with clinicians before pilot):**
number+unit preservation 100% · negation polarity 100% · drug-name terminology ≥98% ·
escalation correctness ≥95% with zero missed red-flags · end-to-end turn latency ≤5s ·
**pilot go/no-go: zero critical-harm errors uncaught by the safety layer.**

### Phase 5 — Pilot readiness (mostly non-code; codex assists)

- **5.1 Hardening.** Rate limiting, request size caps, structured logs with PHI-safe
  redaction (log turn IDs + tiers, never text at INFO), retention config
  (`RETENTION_DAYS`, purge job), TLS/deploy notes.
- **5.2 Docs.** README: run modes, provider config, threshold calibration, known
  limitations (verbatim from research §Open Questions), consent copy for counsel review.
- Human tasks (not codex): 500-set annotation, clinician calibration of thresholds and
  lexicons, Vietnamese counsel review (Decree 13 / PDP Law DPIA, cross-border transfer —
  note both Anthropic and OpenAI APIs are offshore processors of sensitive audio/text;
  the adapter design exists precisely so an in-country/on-prem swap is possible), pilot
  clinic + interpreter partner.

### Phase 6 — Post-review remediation (added 2026-07-08 after code review of Phases 0–4)

Phases 0–4 are implemented and green (backend 92 tests, frontend 5, Playwright e2e,
eval harness). A code review found the defects below. Work these tickets **in order**
— they are ranked by severity. Phase 5.1's hardening items are expanded into concrete
tickets 6.9–6.11 here; treat this section as superseding 5.1.

- **6.0 Initialize the repository.** `.git/` is an empty directory — there is no repo,
  no history. `git init`, verify `.gitignore` excludes what's currently lying around
  (`carepath.db`, `__pycache__/`, `dist/`, `*.egg-info/`, `test-results/`, caches — the
  existing .gitignore already covers all of these), initial commit of the clean tree.
  Do this FIRST so every following fix is a reviewable diff.
  *Accept:* `git log` shows one initial commit; `git status` clean after a test run.

- **6.1 Fix normalizer corrupting Vietnamese words into digits.** `_replace_number_words`
  ([backend/app/normalize.py:108-147](backend/app/normalize.py#L108-L147)) substitutes bare
  number-words context-free after diacritic folding, so common words collide:
  "Ba của cháu bị đau bụng" (My dad has stomach pain) → "3 của cháu bị đau bụng";
  "anh Tư đến khám" → "anh 4 đến khám". The corrupted text is what MT translates.
  **Rule:** only digit-replace a number-word run when (a) the run has ≥2 number tokens
  ("hai mươi", "năm trăm"), or (b) a single number-word is immediately followed by a
  unit/classifier/time word (viên, gói, ống, lần, ngày, tuần, tháng, giờ, mg, ml, mcg,
  tuổi — new lexicon list in normalize.py). Never replace a capitalized word that is not
  sentence-initial (names: Tư, Ba, Năm are common). Keep "nửa"+classifier → 0.5.
  *Accept/tests:* table-driven cases — the two corruptions above stay unchanged;
  "uống nửa viên, ngày hai lần" → "uống 0.5 viên, ngày 2 lần", "năm trăm mi-li-gam"
  → "500 mg", "tái khám sau mười ngày" → "+10 days" all still pass; full risk-fixture
  and eval-harness runs stay green.

- **6.2 WS pipeline errors must send `turn_error`, not kill the socket.** The WS loop
  ([backend/app/api.py:290-311](backend/app/api.py#L290-L311)) has no try/except around
  `process_audio_turn`/`process_text_turn`; an ASR `RuntimeError` (after retries) or a
  `ProviderOutputError` from strict MT parsing propagates and drops the connection with
  no message — routine in cloud mode. Wrap both calls: on exception, log (id + error
  class only, no text — see 6.10), send
  `{type:"turn_error", message:"translation failed — retry or use typed fallback",
  retryable:true}`, clear the in-flight entry, keep the loop alive.
  *Tests:* WS tests using `MockASRProvider(fail=True)` and `MockMTProvider(fail=True)`
  assert the client receives `turn_error` and can complete a following turn on the
  same socket.

- **6.3 Restore diacritics in the Vietnamese consent copy.** The legally significant
  disclosure ([frontend/src/components/ConsentGate.tsx:33-38](frontend/src/components/ConsentGate.tsx#L33-L38))
  is stripped of diacritics, violating the AGENTS.md convention. Correct copy:
  "Thông báo sử dụng AI" / "Công cụ phiên dịch" / "Công cụ này chỉ phiên dịch lời nói.
  Kết quả có thể sai và không thay thế lời khuyên y tế, chẩn đoán, hoặc khuyến nghị
  dùng thuốc." Also make the two consent-checkbox labels bilingual (En + Vi).
  *Tests:* ConsentGate test asserts the diacritic strings render.

- **6.4 One-sided number-mismatch check.** `_mismatch_spans`
  ([backend/app/risk/engine.py:177](backend/app/risk/engine.py#L177)) requires digits on
  BOTH sides, so a translation that drops the number entirely — the worst case — passes
  silently. Change: if the normalized source contains digits and the translation contains
  none → `number_mismatch`, critical. (Both-sides-differ stays as is.)
  *Tests:* new risk fixtures — unit-less numeric utterance (e.g. blood-pressure value)
  with digit-free translation must tier critical; existing fixtures stay green.

- **6.5 Reviewer returns entity text, not character spans.** The read-back table shows
  offsets like "12-18" ([frontend/src/components/InterpreterConsole.tsx:253-259](frontend/src/components/InterpreterConsole.tsx#L253-L259))
  — unusable for the doctor, and LLM-generated indices are unreliable anyway. This was a
  PLAN §Phase-2 contract mistake, not an implementation error. Change `CriticalEntity`
  to `{kind, source_text, translated_text}` (drop spans) in
  [backend/app/providers/base.py](backend/app/providers/base.py), the reviewer system
  prompt + parser, mock, `review_payload` in session.py, and the UI table (render the
  two text columns). *Tests:* update reviewer parse tests + session safety test;
  UI test asserts actual entity text renders in the confirmation card.

- **6.6 Minimal admin review UI.** PLAN 4.2 shipped API-only. Add one frontend route
  `/admin`: token input (kept in memory, sent as `X-Admin-Token`), filter controls
  mapping to the existing query params, results table (source, translation, correction,
  risk tier, status, feedback), CSV download link. Nothing else — no charts.
  *Tests:* component test with mocked fetch: 401 path shows error, rows render.

- **6.7 Small backend guards (one ticket).**
  (a) Startup guard: `provider_mode=cloud` + `admin_token=="change-me"` → refuse to boot
  with a clear error. (b) WS + REST reject new turns/confirms on `ended` sessions
  (escalated sessions stay usable — communication continues while the interpreter is
  arriving). (c) `confirm_turn` returns 409 unless status is `awaiting_confirm` or
  `blocked`. (d) Console header shows real provider mode from `/api/health` instead of
  hardcoded "Mock mode session". *Tests:* one per guard.

- **6.8 Don't block the event loop on provider calls.** The WS handler calls the
  synchronous pipeline inline; in cloud mode a slow provider (up to 30s timeout) freezes
  every connection. Wrap the `process_*` calls with `await anyio.to_thread.run_sync(...)`.
  *Tests:* existing WS tests still pass (behavioral change is concurrency-only).

- **6.9 Retention purge.** `RETENTION_DAYS` setting (default 30, `0` = keep forever);
  on startup delete sessions (+ turns/feedback) older than the cutoff.
  `# ponytail: startup purge only; add a scheduler when the app runs for weeks unattended.`
  *Tests:* seeded old session purged, recent kept, `0` keeps all.

- **6.10 PHI-safe logging + size caps.** Structured logging: INFO logs may carry ids,
  tiers, statuses, error classes — never `source_text`/`translation`/audio. Cap audio
  per turn (`MAX_TURN_AUDIO_BYTES`, default 10 MB — reject with `turn_error`) and typed
  text length (2 000 chars). *Tests:* oversized audio → turn_error; log-capture test
  asserts no turn text at INFO.

- **6.11 CI runs the Playwright e2e.** Third job: install both apps, start backend in
  mock mode, `npx playwright test`. *Accept:* e2e green in CI, not just locally.

Not fixing (accepted for MVP): transcript `highlightText` marks only the first risk
span per turn (badges list the rest); in-flight turn lock is process-local
(single-worker deploy); admin review endpoint scans in Python (single-clinic scale).

## 9. What we deliberately did NOT build (and when to add)

- **Server TTS adapter** → add if browser voices fail clinician testing (Phase 3 review).
- **ML NER (ViHealthBERT) risk detection** → add behind risk-engine interface when rules
  plateau on eval fixtures.
- **Fine-tuned ASR/MT (VietMed/ViMedCSS/MedEV, PiDA augmentation)** → post-MVP; adapters
  are the seam. Fine-tuning is the biggest known quality lever (research finding 3).
- **Streaming partial transcripts** → add if ≤5s turn latency fails; push-to-talk turns
  are short, so batch-per-turn likely suffices.
- **Auth/multi-tenant, Postgres, visit summaries, analytics dashboards** → post-pilot.

## 10. Open questions that block PILOT, not build

Copied from research §Open Questions — legal (Vietnam DPIA + cross-border, US §1557/HIPAA
classification), clinical thresholds, formulary/LASA list ownership, pilot partner. Build
proceeds in mock + placeholder-provider mode regardless.
