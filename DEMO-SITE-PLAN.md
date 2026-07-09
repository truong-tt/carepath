# CarePath Interpreter — Demo Website Plan

A public demo/marketing site for the product. Separate track from PLAN.md (the product);
do not touch `backend/` or `frontend/` for this work. Everything lives in a new `/site`
folder. Read [docs/research.md](docs/research.md) for the evidence base the copy draws on.

**Executor:** codex-5.5 (xhigh). Work tickets S.0 → S.7 in order, one commit per ticket,
same conventions as AGENTS.md. All copy that appears in Vietnamese MUST have full
diacritics — this is a hard rule (see AGENTS.md).

---

## 1. Purpose, audience, and the one metric

The site convinces **Vietnamese clinic owners and hospital administrators** (secondary:
pilot clinicians, investors) that CarePath is a safe, compliant way to run consultations
with English-speaking patients — and converts them into **pilot-program requests**.
One conversion goal: the "Đăng ký thí điểm" (Request a pilot) form. Everything on the
page exists to move a skeptical healthcare buyer toward that form.

Language: **Vietnamese default, English toggle** (persist choice in localStorage).

## 2. Architecture (decided)

- **Static site, no backend.** New `/site` folder: Vite + React 18 + TypeScript — same
  stack and lint rules as `frontend/`, but an independent app (own package.json). Output
  is plain static files deployable to any host (GitHub Pages/Netlify/nginx).
- **The interactive demo is a scripted, client-only simulation.** It replays canned
  consultation turns that reproduce the real product UX (push-to-talk feel, bilingual
  transcript, risk highlighting, read-back confirmation, escalation button). No real
  ASR/MT calls, no API keys, no audio recording, no PHI — the browser never captures
  the mic. Seed the scripts from `eval/fixtures/eval_starter.tsv` scenarios (they are
  already clinically shaped and bilingual).
- **Lead capture without a server:** the pilot-request form POSTs to a configurable
  `VITE_LEAD_ENDPOINT`; when unset, it falls back to a prefilled `mailto:` link. Mark
  this as the single integration point. Store nothing in the browser beyond the form
  draft.
- Simple i18n: one `strings.ts` dictionary module (`vi`/`en` keys), no i18n library.
- No analytics, no cookies, no tracking in MVP. A comment marks where a privacy-safe
  counter could go later.

## 3. Honesty guardrails (non-negotiable)

The product's brand IS safety. The site models the same honesty the app enforces:

1. The demo is clearly labeled as a simulation: "Bản mô phỏng — không phải bản dịch
   trực tiếp" visible while the demo plays.
2. Never claim autonomy or diagnosis. The tagline space says *translation-and-
   verification aid with human-interpreter escalation* — mirror AGENTS.md invariant 1.
3. Banned patterns: fake urgency ("only 3 pilot slots left!"), fake scarcity, countdown
   timers, guilt-trip copy ("No thanks, I prefer miscommunication"), pre-checked
   marketing-consent boxes, hidden pricing.
4. Every statistic shown must come from docs/research.md and carry its citation in a
   tooltip/footnote (e.g., 40–80% of verbal medical information is immediately
   forgotten — Kessels 2003; up to 66% of MT'd discharge-instruction sets contained
   an inaccuracy — BMJ Qual Saf 2025).
5. Loss-aversion and contrast framing must be factual (real costs, real risks), never
   fabricated numbers. Pricing figures are placeholders marked `TODO-pricing` for the
   founder to fill; do not invent prices presented as real.

## 4. Page architecture — each section wired to a persuasion principle

Single long-scroll landing page + the embedded demo. Section order is the persuasion
sequence; the six principles are design mechanics, not decoration:

| # | Section | Principle applied | Mechanic |
|---|---|---|---|
| 1 | **Hero** | Reciprocity | Value before any ask: headline + the live demo sits above the fold, playable immediately. No form, no email gate anywhere before section 7. CTA: "Xem demo 90 giây" scrolls into the demo. |
| 2 | **Interactive demo** | Smart defaults + Goal gradient + IKEA | See §5. Scenario pre-selected and pre-loaded (smart default: "Khám ngoại trú — kê đơn thuốc", the most relatable case). A 4-step progress rail starts with step 1 already checked: "✓ Kịch bản đã chọn" — the visitor begins at 25%, not zero. Customization panel (IKEA): clinic name, specialty, scenario choice — reflected live in the demo header ("Phòng khám Đa khoa An Bình — Demo"). |
| 3 | **The problem** | Loss aversion (ethical) | What clinics lose *today*: cited stats on miscommunication (research §Exec Summary), the cost/scarcity of qualified interpreters, compliance exposure. Frame: "Mỗi lượt khám không được phiên dịch đúng là một rủi ro bạn đang gánh" — protecting what they have (patients, reputation, license), not threatening to take features away. |
| 4 | **Safety by design** | Trust builder (no trick) | The product's differentiator. Render the real safety mechanics as cards: read-back confirmation, risk highlighting, low-confidence flagging, one-tap interpreter escalation, no-audio-storage privacy mode. Copy source: PLAN.md §2 invariants, translated for a non-technical buyer. |
| 5 | **How it works** | — | 3 illustrated steps (speak → verify → confirm), one line each. |
| 6 | **Cost framing** | Contrast effect (ethical) | Anchor with the true, cited costs of the status quo: full-time bilingual staff or per-visit professional interpreter rates, and the cost of a single adverse event. Then the pilot offer (placeholder `TODO-pricing`). The anchor numbers must be real and sourced — contrast through honest arithmetic, not a fake slashed price. |
| 7 | **Pilot CTA + form** | Reciprocity + IKEA + Loss aversion payoff | By now the visitor has used the demo and customized it. Form headline: "Giữ lại bản demo bạn vừa tạo" — submitting sends them their configured demo transcript (attach the transcript text into the form payload). Fields: name, clinic, role, email/Zalo, pre-filled message (smart default) summarizing their chosen scenario. ≤5 fields. |
| 8 | **Footer** | — | Compliance posture line (Decree 13/PDP-aware design, §1557-aligned positioning), AI-use honesty statement, contact. |

## 5. The interactive demo spec (the heart of the site)

A `DemoPlayer` component simulating one consultation:

- **Scenario scripts:** 3 scripted conversations (JSON in `site/src/demo/scenarios/`),
  ~8 turns each, adapted from eval fixtures: (a) prescription + dosage (default),
  (b) allergy check with a negation moment, (c) chest-pain red flag → escalation.
  Each turn: speaker, Vietnamese text, English text, risk tier, risk spans, and for
  high/critical turns a read-back payload (entities: drug/dose/frequency/negation).
- **Playback:** turns appear one-by-one with a typing/speaking animation and a subtle
  push-to-talk button pulse (autoplay ~4s per turn; controls: play/pause, next, replay).
  Visitor can also click "Thử tự gõ" to type one custom line that gets echoed into the
  transcript with a canned translation — participation, not real MT (label it).
- **The safety moment is the hero moment:** when the dosage/allergy turn arrives,
  playback *stops*, the read-back confirmation card slides in (real product styling:
  entity table, Confirm / Edit / Escalate), and the progress rail advances only when
  the visitor clicks Confirm. In scenario (c), the red-flag turn triggers the
  full-screen escalation banner exactly like the product.
- **Progress rail (goal gradient):** `✓ Kịch bản` → `Nghe hội thoại` → `Xác nhận
  read-back` → `Nhận bản ghi`. Step 4 unlocks a "Tải bản ghi demo" button (downloads
  the bilingual transcript as a formatted .txt/.html — the free cookie they keep).
- Visual fidelity: match the real product's transcript layout and risk badge colors
  (lift the palette from `frontend/src/App.css`) so the demo IS the product, not a
  cartoon of it.

## 6. Design direction

- Clinical-trust aesthetic: calm, spacious, high contrast; one accent color for risk/
  CTA moments; light + dark theme. No stock-photo doctors, no purple-gradient AI slop,
  no emoji in headings. Vietnamese typography checked with real diacritics at display
  sizes (choose a font that renders Vietnamese well — e.g. Be Vietnam Pro, self-hosted).
- Responsive: the demo must work on a phone (clinic owners will open this from Zalo).
- Accessibility is part of the pitch: WCAG AA contrast, full keyboard path through the
  demo, `prefers-reduced-motion` respected (no autoplay animation), semantic landmarks.
- Performance: static, self-hosted font subset, no external requests at runtime except
  the lead endpoint on submit. Lighthouse ≥95 performance/accessibility/best-practices.

## 7. Tickets

- **S.0 Scaffold.** `/site` Vite React-TS app, eslint config copied from frontend,
  `npm run dev/build/test`, README section. Commit this plan file with it.
  *Accept:* `npm run build` outputs static files; CI-ready.
- **S.1 Demo engine.** Scenario JSON schema + 3 scripts + `DemoPlayer` with playback,
  read-back stop, escalation moment, progress rail, transcript download. *Tests:*
  vitest — playback advances, confirmation gates progress, download produces bilingual
  content; scripts validated against the schema.
- **S.2 Page sections.** Sections 1, 3–6, 8 with bilingual copy (research-cited stats
  with footnotes; `TODO-pricing` placeholders). *Accept:* full page renders in vi + en;
  no diacritic-stripped Vietnamese anywhere (add a test that greps built output for
  the corrected consent-style strings).
- **S.3 Persuasion wiring.** Smart-default scenario preselection, customization panel
  (clinic name/specialty live in demo header), form pre-fill from demo state, "keep
  your demo" transcript attach. *Tests:* customization propagates; form payload
  contains scenario summary.
- **S.4 Language toggle.** `strings.ts`, vi default, persisted choice, `<html lang>`
  switches. *Tests:* toggle flips all sections.
- **S.5 Lead form.** `VITE_LEAD_ENDPOINT` POST with mailto fallback, ≤5 fields, inline
  validation, success state, zero persistence beyond the draft. *Tests:* endpoint mode
  + fallback mode.
- **S.6 A11y + e2e.** Keyboard-only Playwright run through the whole demo flow to form
  success; reduced-motion snapshot; axe-core pass with no serious violations.
- **S.7 CI.** New `site` job: lint, test, build, run the S.6 e2e against `vite preview`.
  *Accept:* CI green end to end.

## 8. Non-goals

No real translation calls, no account system, no CMS, no blog, no analytics, no A/B
testing framework, no multi-page router (one page + anchors), no video production
(the scripted demo replaces a demo video). Pricing numbers are founder input, not
codex's to invent.
