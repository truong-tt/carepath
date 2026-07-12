# CarePath onboarding UX/UI fix — execution backlog

**Status:** implementation backlog. Successor to `docs/ux-redesign-carepath.md`: that document's functional stories (intent quiz, consent gate, stepper, device check, first-session checklist) are implemented and tested; this backlog fixes their **visual execution**, which failed QA review.

**Objective:** make both product onboardings — the Interpreter app (`frontend/`) and the Scribe tool (`site/`) — match the design language already shipped on the landing page, and fix the concrete layout defects captured in `.codex/qa-evidence/`.

**Evidence baseline (look at these before coding):**

| Defect | Capture |
|---|---|
| Intent quiz is a bare fieldset with default radios in an empty page; no stepper, no context | `.codex/qa-evidence/interpreter-quiz-state-1440x900.png` |
| Consent stepper is a right-rail stack of gray input-looking boxes with uppercase text statuses; giant flat gray disabled button | `.codex/qa-evidence/interpreter-consent-fixed-1440x900.png` |
| Device-check page heading renders above/behind the sticky header (stacking bug); page is one button in a void | `.codex/qa-evidence/interpreter-device-state-1440x900.png` |
| Console session-action chips overlap the checklist card; PTT button reads as disabled; patient panel is an empty white box | `.codex/qa-evidence/console-fixed-1440x900.png` |
| Scribe explainer step 4 orphan-wraps under step 1; dead space in card; H1 breaks mid-word ("bệnh / án"); 360px header truncates VI/EN toggle | `.codex/qa-evidence/scribe-fixed-1440x900.png`, `scribe-fixed-360x800.png` |

## Hard rails — apply to every task

- No new dependencies: no router, state library, i18n library, or CSS framework. Plain CSS custom properties and existing React state only.
- Consent controls are never pre-checked, defaulted, or gamified. Both attestations stay required. The honest-progress stepper policy in `docs/ux-redesign-carepath.md` stands: no step displays complete without a real completed action or persisted prior choice.
- No `getUserMedia` call, `/api/` request, or WebSocket before consent submission. `frontend/tests/mock-mode.spec.ts` asserts this and must stay green.
- Internal identifiers (`scribe`, `interpreter`, `doctor`, `patient`, `vi`, `en`), API paths, WebSocket events, risk rules, and TTS eligibility (`canSpeakTurn` in `frontend/src/tts.ts`) are unchanged.
- Preserve keyboard operability, ARIA roles/labels, forced-colors support, and reduced-motion support — all were deliberately built and are covered by tests and QA captures.
- Playwright specs assert on exact Vietnamese labels. Any copy change updates the spec in the same commit.
- Preserve every safety invariant in `AGENTS.md`. A UI change must never release blocked content, un-suppress TTS, or start audio before consent.
- One task per commit, in the order below. Each task is presentation/layout only unless its scope says otherwise.

## Delivery order

| Order | Task | Area | Depends on |
|---:|---|---|---|
| 1 | FIX-01 Design tokens for the interpreter app | frontend | None |
| 2 | FIX-02 App shell + sticky-header stacking bug | frontend | FIX-01 |
| 3 | FIX-03 Unified onboarding frame + stepper restyle | frontend | FIX-02 |
| 4 | FIX-04 Intent quiz option cards | frontend | FIX-03 |
| 5 | FIX-05 Consent screen hierarchy | frontend | FIX-03 |
| 6 | FIX-06 Device-check green room | frontend | FIX-03 |
| 7 | FIX-07 Console first-run polish | frontend | FIX-01, FIX-02 |
| 8 | FIX-08 Scribe onboarding layout fixes | site | None (parallel-safe) |
| 9 | FIX-09 Landing → product handoff continuity | site + frontend | FIX-03, FIX-08 |
| 10 | FIX-10 QA gate and evidence refresh | both | All above |

FIX-08 can run in parallel with FIX-01…07. FIX-04, FIX-05, FIX-06 can run in any order after FIX-03.

---

### FIX-01 — Port the landing-page design tokens into the interpreter app

**Files:** `frontend/src/App.css` (top), reference `site/src/styles.css:14-70`.

`site/src/styles.css` already defines the full system: `--ink #102a2e`, `--ivory #f4f1e8`, `--teal #0f766e`, `--mist`, `--amber`, `--critical`, derived `--bg/--text/--muted/--line/--surface` via `color-mix`, dark-panel tokens `--deep/--on-deep/--accent-on-deep`, radii `--r-panel/--r-control`, `--shadow`, and a `prefers-color-scheme: dark` override block. Port this token block (or the subset the app needs) into a `:root` block at the top of `frontend/src/App.css`, then replace every hardcoded hex in the file with the matching token. `frontend/src/App.css` currently has **zero** custom properties; colors like `#f4f1e8`, `#102a2e`, `#0f766e`, `#c7d4d1` repeat throughout — most map 1:1 to existing tokens.

**Acceptance criteria**

- [ ] All colors in `frontend/src/App.css` come from custom properties; no raw hex outside the `:root` blocks.
- [ ] Safety-state colors (blocked/high-risk, low-confidence amber, escalation, critical) keep ≥ 4.5:1 text contrast in both light and dark schemes.
- [ ] Forced-colors behavior is unchanged (existing `forced-colors` rules still apply).
- [ ] No TSX/markup changes in this commit.

**Verify:** `npm.cmd --prefix frontend test && npm.cmd --prefix frontend run build && npm.cmd --prefix frontend run e2e`

### FIX-02 — App shell restyle and sticky-header stacking bug

**Files:** `frontend/src/App.tsx` (`.product-shell` header, lines ~24–64), `frontend/src/App.css`.

1. Fix the stacking bug first: on the device-check capture the page `<h1>` paints above/behind the sticky header. Give the sticky header an explicit `z-index` above page content and audit for any `position`/`transform` on page containers creating competing stacking contexts.
2. Restyle the header to match the landing header (`site/`): logo + breadcrumb on the left, status note, VI/EN pill toggle, and the "Tất cả chức năng" link styled as the landing's dark link-button.
3. At 360px the header must not wrap mid-word or truncate the toggle: collapse to logo + toggle with the breadcrumb text truncating with ellipsis, or stack in a defined two-row layout.

**Acceptance criteria**

- [ ] No content ever paints over the sticky header on any onboarding or console screen.
- [ ] Header is visually consistent with the landing header (same tokens, radii, weights).
- [ ] At 360×800 and 390×844: no horizontal overflow, no mid-word wraps, toggle fully visible.

**Verify:** frontend commands above.

### FIX-03 — Unified onboarding frame; stepper on every step

**Files:** `frontend/src/App.tsx` (screen ladder, lines ~106–117), `frontend/src/components/OnboardingStepper.tsx`, `frontend/src/components/ConsentGate.tsx`, `frontend/src/components/IntentQuiz.tsx`, `frontend/src/components/DeviceCheck.tsx`, `frontend/src/App.css`.

Create one shared onboarding layout — centered max-width column (~40rem), product kicker + screen title, compact **horizontal** stepper at top — and use it for the quiz, consent, and device-check screens. Today the stepper renders only inside ConsentGate, so the quiz and device screens float context-free. Restyle `OnboardingStepper` from the gray box-stack with uppercase text statuses ("ĐÃ HOÀN THÀNH") to numbered dots with check marks for completed steps and a filled current step.

**Scope guard:** presentation only. Do not change the screen-selection ladder logic, the honest-progress completion logic, localStorage keys, or when each screen mounts.

**Acceptance criteria**

- [ ] Quiz, consent, and device check all render inside the same frame with the stepper visible.
- [ ] Stepper uses dots/checks; state is conveyed by text and structure too (visually-hidden or short label per step), not color alone; current step keeps `aria-current="step"`.
- [ ] Consent step never shows complete before both attestations are checked and submitted (existing tests in `OnboardingStepper.test.tsx` stay green).
- [ ] No horizontal overflow at 360×800; stepper labels may collapse to numbers + current-step label on narrow widths.

**Verify:** frontend commands above.

### FIX-04 — Intent quiz option cards

**Files:** `frontend/src/components/IntentQuiz.tsx`, `frontend/src/copy.ts`, `frontend/src/App.css`.

Replace the bare fieldset radios with large selectable option cards: full-row click targets, visible selected state (border + check), a small "Đề xuất" badge on the recommended default (Bác sĩ, VI→EN), one question per screen as today. Keep native radio inputs inside the cards for semantics; keep the skip link.

**Scope guard:** keep localStorage keys `carepath-onboarding-role` / `carepath-onboarding-direction`, the two-step order, defaults, and the skip behavior. The Playwright flow clicks "Tiếp tục" twice — do not rename it.

**Acceptance criteria**

- [ ] Options are card-sized targets (≥ 44px tall), operable by mouse, touch, and arrow keys as a radio group.
- [ ] Selected state visible in forced-colors mode (border/outline, not background alone).
- [ ] Recommended badge is presentation only — the default is still just a pre-selected radio, and skip still applies defaults.

**Verify:** frontend commands above.

### FIX-05 — Consent screen hierarchy

**Files:** `frontend/src/components/ConsentGate.tsx`, `frontend/src/copy.ts`, `frontend/src/App.css`.

Replace the two-column layout (text left, stepper-box-stack right) with a single centered column: title → one-paragraph what-it-does (bilingual pair as today) → demo simulation card → attestations → start button. Style each attestation as a bordered full-row label (checkbox + VI text + EN companion) so the whole row is the tap target. The demo preview becomes a visually distinct card labeled "Mô phỏng" with its existing disclaimer. Give the disabled start button an adjacent hint line ("Đánh dấu cả hai xác nhận để bắt đầu" + EN companion) instead of relying on a gray bar to explain itself.

**Scope guard:** consent payload shape, both-required logic, session-creation timing, and error announcement behavior unchanged. Checkboxes never pre-checked. The button label "Bắt đầu phiên dịch" is asserted by Playwright — keep it.

**Acceptance criteria**

- [ ] Single-column flow with no dead zones at 1440×900; content column ≤ ~44rem.
- [ ] Attestation rows are full-width click targets; checkbox focus ring visible.
- [ ] Hint next to the disabled button; hint disappears (or turns confirmatory) when both are checked.
- [ ] Disabled state distinguishable in forced-colors mode.

**Verify:** frontend commands above.

### FIX-06 — Device-check green room

**Files:** `frontend/src/components/DeviceCheck.tsx`, `frontend/src/copy.ts`, `frontend/src/App.css`.

Lay the screen out as a "green room" card inside the FIX-03 frame: mic icon + title, device picker (already implemented — make it visible in the idle frame, not only post-test), the live level meter with a labeled scale, and a state line for each of the existing states `idle | ready | unavailable | denied` with Vietnamese-first remediation copy for denied/unavailable. Primary action "Tiếp tục bằng micrô" appears/enables only after a passed check (the existing fail-closed rule); "Tiếp tục bằng văn bản" stays as the secondary path.

**Scope guard:** no changes to `getUserMedia`/`enumerateDevices`/AudioContext logic, track-stopping cleanup, or the `onComplete` payload. Both continue-button labels are asserted by Playwright — keep them.

**Acceptance criteria**

- [ ] Device picker and meter are visible in the card before testing (meter idle/empty until test starts).
- [ ] The meter visibly responds to speech during the test; state changes are announced (existing live region preserved).
- [ ] Denied/unavailable states show remediation copy and a retry action, styled as states of the card rather than bare text.
- [ ] Heading no longer collides with the sticky header (regression check on the FIX-02 bug).

**Verify:** frontend commands above.

### FIX-07 — Console first-run polish

**Files:** `frontend/src/components/InterpreterConsole.tsx`, `frontend/src/components/SessionChecklist.tsx`, `frontend/src/App.css`.

Presentation-only fixes to the console's first-run state:

1. **Session-action chips** ("Kết thúc phiên", "Rút lại xác nhận", "Xóa dữ liệu phiên") currently overlap the checklist card edge. Move them into a proper toolbar row (right-aligned under the page header or grouped in a session menu region) with normal document flow — no negative margins/absolute positioning.
2. **Push-to-talk** is a flat gray box that reads as disabled. Restyle as the page's primary control: teal ready state with mic glyph, distinct recording state (filled + pulse, gated by `prefers-reduced-motion`), processing state (spinner/label), true disabled state visually distinct from ready.
3. **First-session checklist** becomes a compact dismissible panel that does not push the speaker regions below the fold at 1440×900 (collapse to a slim bar after first render, or dock aside the transcript).
4. **Empty states:** the patient panel and transcript get one-line guidance ("Lượt dịch sẽ hiện ở đây…" + EN) instead of blank white boxes.

**Scope guard:** `InputState` machine, recording handlers, WebSocket handling, risk masking, confirmation, escalation, TTS suppression, and checklist completion logic unchanged. "Nhấn giữ để nói" and the session-action labels are asserted by Playwright — keep them.

**Acceptance criteria**

- [ ] No overlapping elements at any of the four QA viewports.
- [ ] PTT states ready/recording/processing/disabled are each visually distinct, announced as today, and distinguishable in forced-colors mode.
- [ ] Speaker regions and PTT are above the fold at 1440×900 with the checklist present.
- [ ] Recording pulse animation disabled under `prefers-reduced-motion`.

**Verify:** frontend commands above, plus `python -m pytest` (safety suite) once.

### FIX-08 — Scribe onboarding layout fixes

**Files:** `site/src/scribe/ScribeTool.tsx` (pre-start explainer at ~line 305, processing steps at ~line 374), `site/src/styles.css`, `site/src/content/strings.ts` only if a label must change.

1. Fix the pre-start explainer (`preStartSteps`) grid: steps 1–4 must read in order without step 4 orphan-wrapping under step 1 — use a 2×2 grid at desktop and a single column on mobile, or one vertical list.
2. Remove the dead space inside the pre-start card (large empty band between steps and disclaimer).
3. Prevent mid-word H1 wraps: `text-wrap: balance` on the heading plus a non-breaking space in "bệnh án" (and check other compounds: "bản nháp", "phiên âm").
4. Fix the 360px header: VI/EN toggle fully visible, breadcrumb truncates with ellipsis instead of pushing the toggle off-canvas.
5. The processing step-progress UI already exists (`doneSteps` timers) — visually align it with the explainer's numbered-step styling so pre-start and processing read as the same system. No timer/logic changes.

**Scope guard:** upload validation, API calls, response rendering, and routes unchanged. Copy changes only if required for wrapping, mirrored in `strings.ts` for both languages.

**Acceptance criteria**

- [ ] Explainer steps read 1→4 in visual order at all four QA viewports; no orphan wrap.
- [ ] No mid-word breaks in Vietnamese headings at 360/390/768/1440.
- [ ] Header intact at 360×800.
- [ ] Existing `ScribeTool.test.tsx` and site e2e stay green.

**Verify:** `npm.cmd --prefix site test && npm.cmd --prefix site run build && npm.cmd --prefix site run e2e`

### FIX-09 — Landing → product handoff continuity

**Files:** `site/src/LandingPage.tsx` (product-card CTAs), `frontend/src/App.tsx` / first onboarding screen styles.

1. Confirm both product-card CTAs carry `?lang=vi|en` when crossing origins (CP-ROUTE-02 rule); add it where missing so the interpreter app opens in the visitor's chosen language.
2. Make the first interpreter onboarding screen (quiz, post-FIX-04) visually echo the landing product card: same kicker style ("Trong buổi khám"), same product name treatment, so clicking "Bắt đầu phiên dịch" on the landing feels like entering the same product, not a different app.

**Scope guard:** no route changes, no new query params beyond `lang`, no session/consent behavior changes.

**Acceptance criteria**

- [ ] Landing (VI and EN) → interpreter app preserves language without the user re-toggling.
- [ ] Kicker/title treatment on the quiz screen uses the same token-driven styles as the landing cards.

**Verify:** both frontend and site command sets.

### FIX-10 — QA gate and evidence refresh

**Files:** tests + a fresh evidence directory (e.g. `.codex/qa-evidence-v2/` or `docs/qa-evidence/`).

- Re-capture: landing, scribe pre-start, scribe processing/result, quiz (both questions), consent (unchecked + checked), device check (idle/ready/denied), console first-run, console high-risk blocked — at 360×800, 390×844, 768×1024, 1440×900, plus forced-colors for consent/device/console.
- Assert the pre-consent invariants still hold (no `getUserMedia`/`/api/`/WebSocket before consent submission; `scrollY === 0` after transitions).
- Keyboard-only pass: quiz → consent → device → typed turn → PTT → high-risk confirm → escalation → end/delete.
- Axe checks: no serious/critical violations on any onboarding screen.
- Manual: 200% zoom, reduced motion, NVDA reading order on consent and device check.

**Full command list**

    python -m ruff check .
    python -m pytest
    npm.cmd --prefix frontend run lint
    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build
    npm.cmd --prefix frontend run e2e
    npm.cmd --prefix site run lint
    npm.cmd --prefix site test
    npm.cmd --prefix site run build
    npm.cmd --prefix site run e2e

If QA finds a defect, reopen the owning FIX task — do not patch inside FIX-10.

## Deferred unless separately approved

- Any change to risk rules, confidence thresholds, provider behavior, API schemas, retention policy, or routes
- New dependencies of any kind (including icon libraries — use inline SVG)
- Redesigning the landing page itself (it is the design reference, not a target)
- Dark-mode work in the interpreter app beyond inheriting the ported token overrides
