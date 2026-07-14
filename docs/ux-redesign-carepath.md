# CarePath Vietnamese-first UX implementation stories

**Status:** active UX implementation contract and backlog.

**Objective:** make CarePath Vietnamese-first and make its two products unmistakably different:

1. **CarePath Trợ lý ghi chép lâm sàng** — creates a clinician-reviewed draft from uploaded Vietnamese visit audio.
2. **CarePath Phiên dịch y khoa Việt–Anh** — supports turn-by-turn conversation and blocks risky output until clinician confirmation.

## Current priority update: Scribe-led public landing

### Current UX problem

The public landing technically labels the Interpreter as being in development,
but still presents it as a peer product choice and sends its card to the pilot
form. That affordance competes with the only available web workflow and leaves
the Scribe value story fragmented across unrelated product and safety sections.

### Proposed flow

1. Show a prominent, non-interactive status rail stating that **Phiên dịch khám
   bệnh trực tiếp** is in development and cannot currently be accessed on the
   web.
2. Lead with the documentation burden after a consultation, then show how an
   approved audio upload becomes a clinician-reviewed structured draft.
3. Keep **Bắt đầu ghi chép** as the only product-launch action.
4. Keep the pilot form as a secondary Scribe-only contact path.

### Affected routes, pages, and components

- `/` in `scribe/frontend/src/LandingPage.tsx`
- Landing copy and metadata in `scribe/frontend/src/content/strings.ts`
- Landing presentation and reduced-motion behavior in `scribe/frontend/src/styles.css`
- The reusable pilot form's optional product-interest field
- `/ghi-chep-lam-sang/` remains unchanged

### Vietnamese-first copy

- Interpreter status: `Đang phát triển — hiện chưa thể truy cập trên web.`
- Hero: `Tập trung vào người bệnh. Để CarePath soạn bản nháp sau buổi khám.`
- Hero detail: `Tải lên tệp âm thanh buổi khám đã được phép sử dụng. CarePath
  chép lời, chuẩn hóa thuật ngữ và tạo bản nháp bệnh án có cấu trúc để bác sĩ
  kiểm tra.`
- Primary action: `Bắt đầu ghi chép`
- Secondary action: `Xem cách hoạt động`
- Problem chapter: `Một buổi khám không nên biến thành hai ca làm việc.`
- Safety limit: `Bản nháp chỉ được dùng sau khi bác sĩ kiểm tra.`
- Final action: `Bắt đầu từ một tệp âm thanh đã được phép sử dụng.`

### Implementation story: CP-UX-10

- Replace the two-product decision accordion with a Scribe-led AIDA narrative.
- Use the existing Geist font, CarePath mark, sanitized Scribe sample, and
  existing form; add only GSAP and its React adapter for the approved motion.
- Add a gapless 12-column problem bento, native horizontal workflow accordion,
  decorative process marquee, and desktop-only pinned workflow visuals.
- Lock the landing pilot form to Scribe and hide its product-interest selector.
- Remove landing-only Interpreter evidence and obsolete selector rules.

### Dependencies

- CP-UX-09 keeps the Interpreter browser routes blocked.
- CP-BASE-003 supplies the existing public-site test and deployment gates.
- The Vercel project continues to build from `scribe/frontend` on `main`.

### Acceptance criteria

- Scribe is the only active product journey and its CTA opens
  `/ghi-chep-lam-sang/`.
- Interpreter status is visible near the top of the page and contains no link
  or button.
- The page explains the post-consultation documentation problem, the Scribe
  workflow, and mandatory clinician review without unsupported claims.
- Vietnamese and English layouts work at 320, 360, 390, 768, and 1440 pixels
  without horizontal overflow.
- Keyboard navigation, reduced motion, diacritics, and serious Axe checks pass.
- Existing Scribe functionality works and Interpreter browser routes remain 404.

### Validation commands

```powershell
cd scribe\frontend
npm.cmd run lint
npm.cmd test
npm.cmd run test:deploy-env
npm.cmd run build
npm.cmd run e2e
npm.cmd run lighthouse
cd ..\..
python -m pytest scribe/tests/test_combined_app.py
```

### Risks and fallback behavior

- GSAP runs only on desktop when reduced motion is not requested; without it,
  all content remains in normal document flow.
- The marquee is decorative and stops for reduced motion. Its meaning is also
  available as static text.
- No Interpreter route, API, WebSocket, consent, microphone, TTS, or risk logic
  changes. If the status presentation fails, it remains plain static text and
  never becomes a launch action.

## Current priority update: problem-led Vietnamese Scribe onboarding

### Current UX problem

The Scribe-led landing explains the product before it earns attention from the
doctor's daily problem. Large decorative panels, 8–14rem section gaps, a 31rem
hero visual, and a 29rem accordion create long stretches with little actionable
information. The working Scribe route then adds another obstacle: visitors must
read a separate pre-start screen and click continue before they can even see the
upload control. The VI/EN switch also adds a choice that is not needed for this
Vietnamese-first release.

### Proposed flow

1. Keep the non-interactive Interpreter development status near the top.
2. Lead with `Dành thời gian cho người bệnh, không phải cho việc gõ bệnh án.`
3. Let doctors recognize their day and calculate their current documentation
   time from four short inputs. Show current burden only, never a promised
   CarePath saving.
4. Reuse one guided sample to show conversation → clarified transcript →
   structured draft → doctor review.
5. Show evidence in three honest levels: the dated Vietnamese workload norm,
   international ambient-scribe evidence, and what CarePath still needs to
   prove locally.
6. Put trust limits before the action, then offer the working Scribe tool first
   and the organization pilot form as a secondary disclosure.
7. On the Scribe route, show brief instructions and the upload control together.

### Affected routes, pages, and components

- `/` in `scribe/frontend/src/LandingPage.tsx`
- `/ghi-chep-lam-sang/` in `scribe/frontend/src/scribe/ScribeTool.tsx`
- `scribe/frontend/src/scribe/ScribeShowcase.tsx`
- Vietnamese landing, sample, metadata, and Scribe-tool copy
- Focused unit, Playwright, stylesheet, package, and Harness proof files

### Vietnamese-first copy

- Hero: `Dành thời gian cho người bệnh, không phải cho việc gõ bệnh án.`
- Hero detail: `CarePath chuẩn bị ghi chú lâm sàng từ cuộc trao đổi để bác sĩ
  kiểm tra và xác nhận.`
- Primary action: `Trải nghiệm ca khám mẫu`
- Secondary action: `Tính thời gian ghi chép`
- Calculator result: current daily documentation time only, plus a clearly
  labelled five-day equivalent.
- Sample limit: `Nhận định` and `Kế hoạch` display
  `Chờ bác sĩ nhập hoặc xác nhận.`
- Tool helper: `Xem ca khám mẫu` links back to `/#demo`.

### Implementation story: CP-UX-11

- Delete the decorative marquee, bento, horizontal accordion, pinned gallery,
  language toggle, and GSAP dependencies.
- Use semantic HTML, the existing Geist font, existing logo, existing lead form,
  and the existing Scribe showcase; add no dependency or remote asset.
- Add the calculator as local React state with the transparent formula
  `số bệnh nhân × phút ghi chép mỗi bệnh nhân`.
- Keep English copy data that other frozen demo code may still consume, but the
  public App always renders Vietnamese and exposes no language control.
- Remove the Scribe tool's `readyToRecord` gate without changing validation,
  upload, progress, error, API, or result behavior.

### Dependencies

- CP-UX-10 supplies the current Scribe-only public route and Scribe-only form.
- CP-UX-09 keeps both Interpreter browser paths at 404.
- CP-BASE-003 supplies deployment, accessibility, and responsive test gates.

### Acceptance criteria

- The site starts with the doctor's documentation problem, not a definition of
  AI Medical Scribe.
- There is no public EN toggle; all visible onboarding and tool copy is
  Vietnamese.
- The calculator works without storage, analytics, network requests, or a
  CarePath productivity prediction.
- The guided sample teaches the workflow and leaves diagnosis and treatment
  decisions to the doctor.
- The upload control is visible on first entry to the Scribe tool.
- The landing has no horizontal overflow at 320, 360, 390, 768, and 1440px and
  no oversized empty instructional panel.
- Keyboard, Axe, reduced-motion, dark/light, diacritics, Scribe-route, lead,
  Lighthouse, and Interpreter-404 checks pass.

### Validation commands

```powershell
cd scribe\frontend
npm.cmd run lint
npm.cmd test
npm.cmd run test:deploy-env
npm.cmd run build
npm.cmd run e2e
npm.cmd run lighthouse
cd ..\..
python -m pytest scribe/tests/test_combined_app.py
```

### Risks and fallback behavior

- The calculator is an estimate based only on answers entered in the browser;
  if JavaScript is unavailable, the surrounding problem and workflow copy still
  explains the value without a numeric claim.
- The workload source is explicitly dated and must not be presented as a current
  national productivity measurement. International studies are labelled as
  external evidence, not CarePath outcomes.
- The sample uses sanitized fixed content and leaves Assessment and Plan blank
  for clinician input. It never becomes medical advice.
- No Interpreter route, API, WebSocket, audio, consent, retention, or safety
  behavior changes.

## Current priority update: professional landing polish

### Current UX problem

The problem-led landing (CP-UX-11) has the right content in the right order,
but its presentation undercuts onboarding:

1. The hero states the problem yet never shows the product. The draft payoff
   sits behind the third tab of the guided sample, so a scanning doctor sees
   no evidence of what CarePath actually produces.
2. The two hero actions wrap into a vertical stack at desktop widths and read
   as a rendering fault rather than a hierarchy.
3. The Interpreter development notice is a full-width dark band directly under
   the navigation; the most dominant element above the fold announces a
   product that cannot be used.
4. The final third of the page is three consecutive dark slabs (trust, start,
   footer) that merge into one block and bury the trust checklist.
5. A late `.site-footer` column override defeats the responsive footer rules,
   so footer text squeezes into unreadable columns at phone widths.
6. Section paddings differ per chapter, leaving long empty stretches between
   the calculator, sample, and evidence sections on desktop.

### Proposed flow

Section order, routes, copy contract, and all interactive behavior stay as
CP-UX-11 delivered them. Only presentation changes:

1. Render the Interpreter status as a quiet bordered notice under the
   navigation. Same element, same strings, still non-interactive.
2. Split the hero: problem headline and actions on the left, and a compact
   conversation-to-draft proof panel on the right that reuses the sanitized
   sample. Subjective and Objective rows only; Assessment and Plan never
   appear before the doctor reaches the guided sample. Actions sit on one row
   on desktop.
3. Keep calculator, guided sample, and evidence sections unchanged in
   behavior; align them to one shared section-padding token.
4. Restyle the trust section as a light panel so the closing start section is
   the single dark moment before the footer.
5. Fix the footer override ordering and stack it into readable rows at phone
   widths.

### Affected routes, pages, and components

- `/` in `scribe/frontend/src/LandingPage.tsx` (hero proof panel replaces the
  abstract daily-flow table)
- `scribe/frontend/src/styles.css` (status notice, hero grid, section rhythm,
  trust section, footer)
- `scribe/frontend/src/LandingPage.test.tsx` (hero proof assertions)
- No route, API, form, showcase-interaction, or Scribe-tool changes

### Vietnamese-first copy (new strings only)

- Proof panel title: `Từ cuộc trao đổi đến bản nháp`
- Conversation label: `Trong ghi âm`
- Reused sample line: `Tôi bị đau tức ngực thoáng qua từ sáng, hơi khó thở.`
- Draft label: `Bản nháp cho bác sĩ kiểm tra`
- Draft rows: existing `Triệu chứng chủ quan` and `Thông tin khách quan`
  sample content; the Objective row reads
  `Chưa có kết quả cận lâm sàng trong nội dung ghi âm.`
- Caption: `Ca khám mẫu đã làm sạch. Nhận định và kế hoạch luôn thuộc về bác sĩ.`

### Implementation story: CP-UX-12

- Replace the hero `daily-flow` table with the conversation-to-draft proof
  panel; delete the orphaned `daily-flow` styles.
- De-emphasize the Interpreter status into a bordered notice.
- One shared section padding; trust section light; footer stacking fixed at
  its root (remove the post-media-query `.site-footer` override).
- No new dependency, motion, image, or remote asset. Semantic HTML only.

### Dependencies

- CP-UX-11 supplies the problem-led structure, calculator, and guided sample.
- CP-UX-09 keeps Interpreter browser routes blocked.
- CP-BASE-003 supplies the site test and deployment gates.

### Acceptance criteria

- The hero shows a conversation-to-draft glimpse labeled as a cleaned sample;
  `Chờ bác sĩ nhập hoặc xác nhận.` still never renders before the doctor opens
  the draft step (existing e2e assertion stays green).
- Both hero actions render on one row at 1024 px and wider.
- The Interpreter status keeps its exact strings and zero links or buttons,
  and no longer uses the dark band treatment.
- Exactly one dark section (the start section) renders between the evidence
  grid and the footer.
- The footer stacks into readable rows at 320, 360, and 390 px.
- Hero height stays under 800 px at 1440×900; H1 line limits hold; no
  horizontal overflow from 320 to 1440 px.
- Lint, unit, deploy-env, build with diacritics gate, Playwright, Lighthouse,
  and combined-app checks pass.

### Validation commands

```powershell
cd scribe\frontend
npm.cmd run lint
npm.cmd test
npm.cmd run test:deploy-env
npm.cmd run build
npm.cmd run e2e
npm.cmd run lighthouse
cd ..\..
python -m pytest scribe/tests/test_combined_app.py
```

### Risks and fallback behavior

- Presentation-only: no route, API, consent, microphone, retention, or safety
  copy changes. The pilot form and showcase interactions are untouched.
- The proof panel is static text from the existing sanitized sample; if it
  threatens the hero height budget, the conversation line drops first and the
  panel degrades to a draft-only card.
- All new strings are NFC-normalized Vietnamese; the build diacritics gate is
  the enforcement.

## Backlog rules

- Implement one story per commit or pull request.
- A story may start only when its listed dependencies are complete.
- UX/copy stories must not change routes, API contracts, microphone behavior, WebSocket behavior, TTS eligibility, or risk rules.
- Routing stories must not redesign the homepage or change clinical/audio workflow behavior.
- Functional stories may consume approved copy but must not reopen the homepage design or route structure.
- Keep the internal identifiers scribe, interpreter, doctor, patient, vi, and en, plus all API paths, WebSocket events, and schema fields unchanged.
- Do not add a router, state library, or i18n dependency. Current React state, pathname/hash checks, browser APIs, CSS, and tests are sufficient.
- Preserve every safety invariant in AGENTS.md. A UI failure must never release blocked content or start audio before consent.
- Persuasion techniques (smart defaults, endowed progress, gamification) may only be applied as permitted by the persuasion boundary matrix in the onboarding section. Legal consent controls are never defaulted, pre-checked, or gamified.

## Current priority update: Scribe-only public availability

### Current UX problem

The public site correctly makes Scribe the primary action, but the direct
Interpreter browser path remains reachable on the Space. A visitor who knows
that URL can still open the unfinished workflow.

### Proposed flow

1. The public landing keeps **Ghi chép bệnh án AI** and **Bắt đầu ghi chép**
   as the only route into a working product.
2. Every browser request to `/phien-dich-y-khoa/*` and `/console/*` returns
   HTTP 404 instead of the Interpreter frontend.
3. Interpreter APIs, WebSockets, backend safety behavior, and automated tests
   remain available only for frozen internal maintenance; no public page links
   to them.

### Affected routes, pages, and components

- `/phien-dich-y-khoa/*` and `/console/*` in `scribe/carepath/main.py`
- `scribe/tests/test_combined_app.py`
- `docs/product/live-interpreter.md`
- `README.md`, `README.hf-space.md`, and `docs/deploy.md`

### Vietnamese-first copy

- Primary feature: `Ghi chép bệnh án AI`
- Primary action: `Bắt đầu ghi chép`
- Blocked route: standard HTTP 404; no unfinished clinical workflow is
  presented to visitors.
- Internal documentation: `Phiên dịch khám bệnh trực tiếp hiện chưa mở cho
  người dùng trên web.`

### Implementation story: CP-UX-09

- Remove the Interpreter static mount and add exact browser-path guards before
  the public static-site mount.
- Keep the current Scribe-first landing unchanged because it already has no
  Interpreter launch link.
- Keep APIs, WebSockets, consent, microphone behavior, TTS, risk rules, and
  the pilot form schema unchanged.

### Dependencies

- CP-UX-08 provides the existing Scribe-first landing state.
- CP-ROUTE-02 is superseded for public browser access, but its API and
  WebSocket boundaries remain unchanged.

### Acceptance criteria

- The public site has no Interpreter launch link and retains Scribe as the
  only working-product action.
- `/phien-dich-y-khoa/`, child paths, `/console`, and `/console/` return 404.
- `/api/v1/health`, `/api/health`, `/api/*`, and `/ws/*` retain their current
  contracts and safety behavior.
- Scribe routes and the Vietnamese public landing still return HTTP 200.

### Validation commands

```powershell
python -m pytest scribe/tests/test_combined_app.py
cd scribe\frontend; npm.cmd test; npm.cmd run build; npm.cmd run e2e
```

### Risks and fallback behavior

- Do not disable `/api/*` or `/ws/*`: that would change the Interpreter
  development and safety contract rather than block its public browser UI.
  Re-enable the static mount only when the product is ready for public access
  and its pre-start safety flow has passed its normal release checks.

## Delivery order

| Order | Story | Type | Depends on |
|---:|---|---|---|
| 1 | CP-UX-01 Vietnamese product names and vocabulary | UX/copy | None |
| 2 | CP-UX-02 Homepage decision gateway | UX/presentation | CP-UX-01 |
| 3 | CP-UX-03 Homepage trust and proof sections | UX/presentation | CP-UX-02 |
| 4 | CP-UX-04 Clinical-note product copy | UX/copy | CP-UX-01 |
| 5 | CP-UX-05 Interpreter locale foundation | UX/copy infrastructure | CP-UX-01 |
| 6 | CP-UX-06 Vietnamese-first consent copy | UX/copy | CP-UX-05 |
| 7 | CP-UX-07 Interpreter workspace terminology | UX/copy | CP-UX-05 |
| 8 | CP-ROUTE-01 Clinical-note canonical route | Routing | CP-UX-02, CP-UX-04 |
| 9 | CP-ROUTE-02 Interpreter canonical route | Routing/deploy | CP-UX-02, CP-UX-05 |
| 10 | CP-ROUTE-03 Internal review route | Routing | CP-ROUTE-02 |
| 11 | CP-FORM-01 Honest pilot form behavior | Functional | CP-UX-03 |
| 12 | CP-NOTES-01 Clinical-note review evidence | Functional | CP-UX-04, CP-ROUTE-01 |
| 13 | CP-NOTES-02 Clinical-note errors and privacy states | Functional | CP-UX-04 |
| 14 | CP-INT-01 Clear doctor and patient input regions | Functional UI | CP-UX-07 |
| 15 | CP-INT-02 Stateful and keyboard-accessible push-to-talk | Audio workflow | CP-INT-01 |
| 16 | CP-INT-03 Clinician-only high-risk review | Safety workflow | CP-UX-07, CP-INT-02 |
| 17 | CP-INT-04 Human-interpreter escalation stops TTS | Safety workflow | CP-INT-02, CP-INT-03 |
| 18 | CP-INT-05 Per-turn low-confidence recovery | Safety workflow | CP-UX-07, CP-INT-02, CP-INT-04 |
| 19 | CP-INT-06 End, delete, and withdraw-consent flow | Session lifecycle | CP-UX-06, CP-INT-02, CP-INT-04 |
| 20 | CP-ONB-01 Pre-consent value demo | Onboarding UI | CP-UX-06 |
| 21 | CP-ONB-02 Two-question intent quiz | Onboarding UI | CP-UX-05 |
| 22 | CP-ONB-03 Honest-progress onboarding stepper | Onboarding UI | CP-ONB-02, CP-UX-06 |
| 23 | CP-ONB-04 Post-consent device readiness check | Onboarding/audio workflow | CP-ONB-03, CP-INT-02 |
| 24 | CP-ONB-05 Embedded first-session checklist | Onboarding UI | CP-INT-02, CP-INT-03, CP-INT-04, CP-INT-05 |
| 25 | CP-QA-01 Full release and visual verification | QA only | CP-ROUTE-03, CP-FORM-01, CP-NOTES-01, CP-NOTES-02, CP-INT-03, CP-INT-04, CP-INT-05, CP-INT-06, CP-ONB-04, CP-ONB-05 |

UX/copy stories 4 and 5 can run in parallel after CP-UX-01. Product-specific functional stories can run independently once their own dependencies are satisfied. CP-ONB-01 and CP-ONB-02 can start any time after CP-UX-06 and CP-UX-05 respectively; only CP-ONB-04 and CP-ONB-05 wait on the interpreter workflow stories.

---

## UX and copy stories

### CP-UX-01 — Encode Vietnamese product names and vocabulary

**Type:** UX/copy only

**User story**

> As a Vietnamese doctor, I want each product named by the job it performs so that I can choose a tool without understanding “Scribe” or “Interpreter.”

**Files likely affected**

- scribe/frontend/src/content/strings.ts
- scribe/frontend/src/content/strings.test.ts
- scribe/frontend/index.html
- scribe/frontend/src/LandingPage.test.tsx

**Dependencies**

- None.
- Product owner approval of these names:
  - CarePath Trợ lý ghi chép lâm sàng
  - CarePath Phiên dịch y khoa Việt–Anh

**Scope guard**

- Copy and metadata only.
- Do not change component structure, routes, link destinations, form payload values, APIs, or interpreter workflow behavior.

**Acceptance criteria**

- [ ] Vietnamese product names, short labels, statuses, and CTA labels use plain Vietnamese.
- [ ] “Scribe,” “Interpreter,” and “Console” are absent from Vietnamese navigation, product names, statuses, and CTAs.
- [ ] First-use terminology says “phiên âm tự động,” “đọc lại để xác nhận,” and “bản ghi y khoa theo bốn mục SOAP.”
- [ ] Later references may use “bản nháp SOAP,” but never imply a completed medical record.
- [ ] English mode remains complete.
- [ ] Internal product keys remain scribe and interpreter.
- [ ] New Vietnamese strings are NFC-normalized and retain diacritics.

**Test/validation command**

    npm.cmd --prefix site test
    npm.cmd --prefix site run build

### CP-UX-02 — Replace repeated homepage choices with one decision gateway

**Type:** UX/presentation

**User story**

> As a first-time visitor, I want one clear two-product choice near the top of the homepage so that I can enter the correct workflow in one decision.

**Files likely affected**

- scribe/frontend/src/LandingPage.tsx
- scribe/frontend/src/components/ProductChoiceCard.tsx (new)
- scribe/frontend/src/content/strings.ts
- scribe/frontend/src/styles.css
- scribe/frontend/src/landing/useLandingMotion.ts
- scribe/frontend/src/LandingPage.test.tsx
- scribe/frontend/tests/demo-flow.spec.ts
- scribe/frontend/package.json and lockfile only if removing the obsolete homepage motion makes GSAP unused

**Dependencies**

- CP-UX-01.

**Scope guard**

- Homepage structure and styling only.
- Keep current link destinations until the routing stories.
- Do not change lead submission behavior, Scribe upload behavior, Interpreter controls, or API calls.

**Acceptance criteria**

- [ ] The homepage contains one product-choice layer, not hero choices plus gateway choices plus a second product index.
- [ ] The hero states that the products serve two different jobs.
- [ ] Each card shows workflow moment, Vietnamese name, status, one-line outcome, input, output, safety sentence, and one primary action.
- [ ] The cards use “Sau buổi khám” and “Trong buổi khám” to distinguish timing.
- [ ] Both cards have equal visual priority.
- [ ] The full Interpreter and clinical-note workflows are no longer interleaved in one long decision path.
- [ ] Existing product destinations still work until CP-ROUTE-01 and CP-ROUTE-02 replace them.
- [ ] At 360×800, 390×844, 768×1024, and 1440×900, the choices have no horizontal overflow and the product names, statuses, and actions remain discoverable.
- [ ] Keyboard focus order follows visual order and each card has explicit links rather than invalid nested interactive controls.
- [ ] Obsolete product-story CSS and motion code is deleted rather than covered by another override layer.

**Test/validation command**

    npm.cmd --prefix site test
    npm.cmd --prefix site run build
    npm.cmd --prefix site run e2e

### CP-UX-03 — Simplify homepage trust and proof sections

**Type:** UX/presentation

**User story**

> As a doctor evaluating CarePath, I want concise safety promises and plainly labeled evidence so that I can assess the demo without scrolling through repeated marketing sections.

**Files likely affected**

- scribe/frontend/src/LandingPage.tsx
- scribe/frontend/src/content/strings.ts
- scribe/frontend/src/styles.css
- scribe/frontend/src/scribe/ScribeShowcase.tsx
- scribe/frontend/src/demo/DemoPlayer.tsx
- scribe/frontend/src/LandingPage.test.tsx
- scribe/frontend/tests/demo-flow.spec.ts

**Dependencies**

- CP-UX-02.
- Approved sanitized sample content for the two proof blocks; do not invent outcome claims or testimonials.

**Scope guard**

- Supporting homepage presentation only.
- Do not change product routes, pilot form payload/submission, audio behavior, or product APIs.

**Acceptance criteria**

- [ ] A three-item trust strip follows the product chooser.
- [ ] The trust strip states clinician review, visible uncertainty, and no replacement of diagnosis/advice.
- [ ] The decorative marquee is removed from the primary flow.
- [ ] Product proof is static and clearly labeled as sample or simulation data.
- [ ] The research source link is always visible rather than hidden behind a carousel step.
- [ ] Simulation, pilot, and draft statuses are visible without interacting with a carousel.
- [ ] The pilot section remains present but its behavior is unchanged until CP-FORM-01.
- [ ] Reduced-motion behavior remains valid.

**Test/validation command**

    npm.cmd --prefix site test
    npm.cmd --prefix site run build
    npm.cmd --prefix site run e2e

### CP-UX-04 — Make clinical-note copy draft-first and plain-language

**Type:** UX/copy only

**User story**

> As a Vietnamese doctor, I want the clinical-note tool to say exactly what is a draft and what still needs review so that I do not mistake AI output for a completed medical record.

**Files likely affected**

- scribe/frontend/src/content/strings.ts
- scribe/frontend/src/scribe/ScribeTool.tsx
- scribe/frontend/src/scribe/ScribeShowcase.tsx
- scribe/frontend/src/scribe/ScribeTool.test.tsx
- scribe/frontend/src/scribe/ScribeShowcase.test.tsx

**Dependencies**

- CP-UX-01.

**Scope guard**

- Visible labels, descriptions, breadcrumbs, and help text only.
- Do not change fetch logic, upload validation, response types, rendering states, routes, or API payloads.

**Acceptance criteria**

- [ ] Breadcrumb and product heading use “Trợ lý ghi chép lâm sàng.”
- [ ] Page title, submit action, loading steps, result heading, copied heading, and new-note action all say “bản nháp.”
- [ ] ASR is introduced as “phiên âm tự động.”
- [ ] SOAP is explained in plain Vietnamese on first use.
- [ ] Copy clearly says the draft does not enter the record automatically.
- [ ] Missing information and clinician-review requirements remain visible.
- [ ] English copy remains complete and equally explicit.

**Test/validation command**

    npm.cmd --prefix site test
    npm.cmd --prefix site run build

### CP-UX-05 — Create one locale source for the Interpreter app

**Type:** UX/copy infrastructure

**User story**

> As a Vietnamese doctor, I want my language choice to apply to the whole Interpreter product so that the VI control is not limited to the header.

**Files likely affected**

- interpreter/frontend/src/copy.ts (new)
- interpreter/frontend/src/App.tsx
- interpreter/frontend/src/App.test.tsx
- interpreter/frontend/index.html
- interpreter/frontend/src/components/ConsentGate.tsx
- interpreter/frontend/src/components/InterpreterConsole.tsx

**Dependencies**

- CP-UX-01.

**Scope guard**

- Locale state, copy plumbing, shell copy, and document language only.
- Do not change product routes, consent payloads, session creation, WebSocket handling, microphone handling, risk gating, or TTS.

**Acceptance criteria**

- [ ] App owns one vi/en locale state and passes it to every doctor-facing screen.
- [ ] The destination reads a valid lang query value once, then persists it in carepath-demo-language.
- [ ] An invalid language value falls back to Vietnamese.
- [ ] The product shell, page title, and document language update together.
- [ ] No new i18n dependency or context abstraction is added unless plain props cannot cover the current tree.
- [ ] Existing consent and session behavior remains unchanged.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build

### CP-UX-06 — Rewrite consent as Vietnamese-first attestation

**Type:** UX/copy only

**User story**

> As a Vietnamese doctor starting an interpreted encounter, I want clear consent statements in Vietnamese with an English companion so that I know what was explained and agreed before microphone access can begin.

**Files likely affected**

- interpreter/frontend/src/copy.ts
- interpreter/frontend/src/components/ConsentGate.tsx
- interpreter/frontend/src/components/ConsentGate.test.tsx
- interpreter/frontend/src/App.test.tsx

**Dependencies**

- CP-UX-05.
- Clinical, privacy, and legal approval of the final attestation text before production release.

**Scope guard**

- Copy, language markup, grouping, and error announcement only.
- Do not change the consent payload shape, the requirement for both checks, session creation timing, or microphone gating.

**Acceptance criteria**

- [ ] Vietnamese is the primary clinician language.
- [ ] English patient-facing companion text has lang="en"; Vietnamese text has lang="vi".
- [ ] Statements explicitly identify that AI fallibility and the right to a human interpreter were explained.
- [ ] Both acknowledgements remain required before the start button is enabled.
- [ ] The translate-only limitation remains explicit.
- [ ] Start, loading, retry, and error copy are localized.
- [ ] Consent errors are announced without moving microphone controls before consent.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build

### CP-UX-07 — Localize workspace, transcript, risk, and feedback terminology

**Type:** UX/copy only

**User story**

> As a Vietnamese doctor, I want conversation controls and safety states described in plain Vietnamese so that I can understand the current turn without decoding developer terms.

**Files likely affected**

- interpreter/frontend/src/copy.ts
- interpreter/frontend/src/components/InterpreterConsole.tsx
- interpreter/frontend/src/components/Transcript.tsx
- interpreter/frontend/src/components/InterpreterConsole.test.tsx
- interpreter/frontend/src/components/Transcript.test.tsx

**Dependencies**

- CP-UX-05.

**Scope guard**

- Display mapping and language attributes only.
- Do not change speaker payloads, recording handlers, WebSocket state, confirmation behavior, TTS, escalation behavior, or feedback API calls.

**Acceptance criteria**

- [ ] Visible labels for doctor, patient, language, connection, recording, risk, confirmation, transcript, and feedback are localized.
- [ ] Raw enum values such as dose_number, awaiting_confirm, confirmed, and provider mode are not shown directly.
- [ ] Each utterance has the correct lang attribute.
- [ ] Mock status says the product is not for real clinical care.
- [ ] English mode remains complete.
- [ ] Existing delivery, confirmation, escalation, and feedback behavior is unchanged.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build

---

## Routing stories

### CP-ROUTE-01 — Add the canonical clinical-note route

**Type:** routing only

**User story**

> As a visitor, I want a shareable clinical-note URL so that I can open the correct product without understanding a hash route.

**Files likely affected**

- scribe/frontend/src/App.tsx
- scribe/frontend/src/pages/ClinicalNotesPage.tsx (new thin wrapper)
- scribe/frontend/src/App.test.tsx
- scribe/frontend/tests/demo-flow.spec.ts
- scribe/carepath/main.py
- scribe/tests/test_combined_app.py

**Dependencies**

- CP-UX-02.
- CP-UX-04.

**Scope guard**

- Route recognition, page ownership, legacy migration, and server fallback only.
- Do not redesign the homepage, change Scribe upload/result behavior, or touch Interpreter routing/audio.

**Acceptance criteria**

- [ ] /ghi-chep-lam-sang/ is the canonical clinical-note page.
- [ ] A direct production load and refresh return 200.
- [ ] The page renders the existing Scribe tool inside a thin product-page wrapper.
- [ ] /#/scribe performs a client-side replace to the canonical path.
- [ ] Browser back and forward behave predictably.
- [ ] Existing /api/v1 routes are unchanged.
- [ ] No router dependency is added.

**Test/validation command**

    npm.cmd --prefix site test
    npm.cmd --prefix site run build
    npm.cmd --prefix site run e2e
    python -m pytest scribe/tests/test_combined_app.py

### CP-ROUTE-02 — Move the Interpreter entry to a task-based canonical route

**Type:** routing and deployment only

**User story**

> As a visitor, I want a Vietnamese task-based Interpreter URL so that the address describes the product instead of exposing the technical word “console.”

**Files likely affected**

- interpreter/frontend/vite.config.ts
- interpreter/frontend/package.json
- interpreter/frontend/playwright.config.ts
- interpreter/frontend/playwright.prod.config.ts (new, or an equivalently small production-base config)
- scribe/carepath/main.py
- scribe/frontend/src/LandingPage.tsx
- scribe/frontend/vercel.json
- scribe/frontend/.env.e2e
- scribe/frontend/.env.example
- scribe/frontend/scripts/validate-deploy-env.mjs
- scribe/frontend/scripts/validate-deploy-env.test.mjs
- scribe/tests/test_combined_app.py
- Dockerfile
- .env.example
- README.md
- README.hf-space.md
- scribe/frontend/README.md
- docs/deploy.md

**Dependencies**

- CP-UX-02.
- CP-UX-05.
- Product-owner decision for the canonical public-site origin used by “Tất cả sản phẩm.”

**Scope guard**

- Canonical mount, build base, redirects, environment validation, and route documentation only.
- Do not change homepage layout, consent/session behavior, microphone/WebSocket/TTS logic, or admin routing.

**Acceptance criteria**

- [ ] /phien-dich-y-khoa/ serves the built Interpreter app and supports direct refresh.
- [ ] /console and /console/ redirect to the canonical path.
- [ ] The public product link carries lang=vi or lang=en when it crosses origins.
- [ ] Vite assets load under the new production base.
- [ ] VITE_CONSOLE_URL validation expects the new canonical pathname.
- [ ] The Vercel build rewrites /ghi-chep-lam-sang/ to the site index so direct loads work.
- [ ] A configured public-site URL makes “Tất cả sản phẩm” return to the canonical site rather than an arbitrary HF Space root, and preserves lang.
- [ ] A production-base e2e command verifies built assets under /phien-dich-y-khoa/ without replacing the existing dev e2e command.
- [ ] /api/* and /ws/* remain unchanged and win before static mounts.
- [ ] Deployment and local-run documentation use the canonical route.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build
    npm.cmd --prefix frontend run e2e:prod
    npm.cmd --prefix site run test:deploy-env
    npm.cmd --prefix site run build
    python -m pytest scribe/tests/test_combined_app.py

### CP-ROUTE-03 — Make internal review reachable without exposing it publicly

**Type:** routing only

**User story**

> As an authorized reviewer, I want one production-safe review URL so that I can reach the existing admin component without adding it to public navigation.

**Files likely affected**

- interpreter/frontend/src/App.tsx
- interpreter/frontend/src/App.test.tsx
- interpreter/frontend/src/components/AdminReview.tsx
- interpreter/frontend/tests/mock-mode.spec.ts
- docs/deploy.md

**Dependencies**

- CP-ROUTE-02.

**Scope guard**

- Hash recognition and return navigation only.
- Do not change admin API contracts, token persistence, filters, CSV behavior, public navigation, or Interpreter audio workflow.

**Acceptance criteria**

- [ ] /phien-dich-y-khoa/#/kiem-duyet renders AdminReview in the production build.
- [ ] The review route is absent from public navigation and sitemap-like content.
- [ ] The admin token remains memory-only.
- [ ] A clear link returns to the Interpreter entry.
- [ ] Old unreachable /admin and /console/admin assumptions are removed from tests/docs.
- [ ] Direct refresh works because the server receives only the canonical product path.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build
    npm.cmd --prefix frontend run e2e

---

## Functional product stories

### CP-FORM-01 — Remove hidden sample data and make pilot submission honest

**Type:** functional form behavior

**User story**

> As a clinic representative, I want to review exactly what a pilot request will contain and how it will be sent so that I do not submit fictitious clinic or demo transcript data.

**Files likely affected**

- scribe/frontend/src/LandingPage.tsx
- scribe/frontend/src/LeadForm.tsx
- scribe/frontend/src/leads.ts
- scribe/frontend/src/content/strings.ts
- scribe/frontend/src/LeadForm.test.tsx
- scribe/frontend/src/leads.test.ts
- scribe/frontend/tests/demo-flow.spec.ts

**Dependencies**

- CP-UX-03.

**Scope guard**

- Form defaults, editable fields, context opt-in, payload, and submit-mode messaging only.
- Do not change homepage card layout, product routing, product APIs, or audio workflows.

**Acceptance criteria**

- [ ] Clinic and specialty start blank, or sample values are unmistakably labeled and excluded from submissions until edited.
- [ ] Clinic information is editable in the form.
- [ ] Interpreter demo context/transcript is excluded by default and requires explicit opt-in.
- [ ] Endpoint mode says “Gửi yêu cầu thí điểm.”
- [ ] Mail mode says “Mở email đã điền sẵn” and never reports the request as sent.
- [ ] The confirmation/error state accurately reflects the configured submission mode.
- [ ] Existing stable interest payload values remain interpreter, scribe, and both.

**Test/validation command**

    npm.cmd --prefix site test
    npm.cmd --prefix site run build
    npm.cmd --prefix site run e2e

### CP-NOTES-01 — Show the clinical-note evidence chain already returned by the API

**Type:** functional clinical-note review

**User story**

> As a doctor reviewing a generated note, I want to compare the raw transcript, corrected transcript, corrected terms, missing information, and SOAP draft so that I can verify the draft before using it.

**Files likely affected**

- scribe/frontend/src/scribe/ScribeTool.tsx
- scribe/frontend/src/scribe/ScribeTool.test.tsx
- scribe/frontend/src/styles.css
- scribe/frontend/tests/demo-flow.spec.ts

**Dependencies**

- CP-UX-04.
- CP-ROUTE-01.

**Scope guard**

- Consume and present fields already returned by POST /api/v1/soap-notes.
- Do not change the Scribe API schema, pipeline, model prompts, upload flow, or product routing.

**Acceptance criteria**

- [ ] The frontend response type retains raw_transcript, corrected_transcript, retrieved_terms, soap, and metadata.
- [ ] Review order is raw transcript → corrected transcript/terms → missing information → draft SOAP.
- [ ] Empty optional fields render a clear empty state rather than invented text.
- [ ] Every displayed SOAP section remains labeled as a draft requiring review.
- [ ] Rendering escapes model text and preserves current RichText safety.
- [ ] Copy/download output still labels the result as a draft.

**Test/validation command**

    npm.cmd --prefix site test
    npm.cmd --prefix site run build
    npm.cmd --prefix site run e2e

### CP-NOTES-02 — Localize clinical-note failures and state accurate privacy

**Type:** functional error handling

**User story**

> As a doctor using the clinical-note tool, I want actionable Vietnamese errors and accurate audio-handling copy so that I know what failed without seeing raw backend messages.

**Files likely affected**

- scribe/frontend/src/scribe/ScribeTool.tsx
- scribe/frontend/src/content/strings.ts
- scribe/frontend/src/scribe/ScribeTool.test.tsx
- scribe/frontend/src/styles.css

**Dependencies**

- CP-UX-04.

**Scope guard**

- Error classification, localized state, retry behavior, and product-specific privacy copy only.
- Do not change backend status codes, upload limits, pipeline behavior, routes, or Interpreter privacy copy.

**Acceptance criteria**

- [ ] Unsupported file, oversized file, rate limit, ASR failure, LLM failure, offline, and unknown failure have localized messages.
- [ ] Raw server detail is not shown to the user.
- [ ] Retry preserves the selected file when safe and does not submit automatically.
- [ ] Privacy copy describes deliberate upload and request-scoped temporary processing accurately.
- [ ] The note tool does not reuse the Interpreter's memory-only audio claim.
- [ ] Technical details remain available only in logs/developer diagnostics.

**Test/validation command**

    npm.cmd --prefix site test
    npm.cmd --prefix site run build

### CP-INT-01 — Separate doctor and patient input regions

**Type:** functional UI

**User story**

> As a doctor sharing one device with a patient, I want clearly different doctor-Vietnamese and patient-English input regions so that I do not attribute a turn to the wrong person.

**Files likely affected**

- interpreter/frontend/src/components/InterpreterConsole.tsx
- interpreter/frontend/src/components/InterpreterConsole.test.tsx
- interpreter/frontend/src/App.css
- interpreter/frontend/tests/mock-mode.spec.ts

**Dependencies**

- CP-UX-07.

**Scope guard**

- Speaker selection layout and typed-entry placement only.
- Reuse existing speaker values and existing recording functions.
- Do not add recording state, keyboard PTT, risk-review, escalation, or route changes.

**Acceptance criteria**

- [ ] One region is labeled “Bác sĩ · Tiếng Việt.”
- [ ] One region is labeled “Người bệnh · English.”
- [ ] Voice and typed fallback live within the selected speaker region; the separate generic speaker dropdown is removed.
- [ ] Role distinction uses text and structure, not color alone.
- [ ] Submitted payloads still use doctor/patient and vi/en.
- [ ] No microphone request occurs before consent.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build
    npm.cmd --prefix frontend run e2e

### CP-INT-02 — Make push-to-talk stateful and keyboard accessible

**Type:** audio workflow

**User story**

> As a clinician using mouse, touch, or keyboard, I want one clear recording and processing state so that I cannot start overlapping turns or lose track of what the microphone is doing.

**Files likely affected**

- interpreter/frontend/src/components/InterpreterConsole.tsx
- interpreter/frontend/src/components/InterpreterConsole.test.tsx
- interpreter/frontend/src/App.css
- interpreter/frontend/tests/mock-mode.spec.ts

**Dependencies**

- CP-INT-01.

**Scope guard**

- Microphone input state and PTT interaction only.
- Do not change translation, risk classification, confirmation, escalation/TTS policy, low-confidence recovery, routes, or marketing copy.

**Acceptance criteria**

- [ ] The visible state sequence is ready → recording → processing → delivered or review required.
- [ ] The busy phase is set synchronously before awaiting microphone permission, so two rapid starts cannot overlap.
- [ ] Only one speaker can record or submit while a turn is active.
- [ ] Disconnected and processing states disable new audio/text submission.
- [ ] Pointer, touch, Space, and Enter can start/stop PTT.
- [ ] Recording exposes an accessible pressed/state announcement.
- [ ] Pointer cancel, permission denial, component unmount, and failure stop every media track.
- [ ] Typed fallback remains usable when microphone access is unavailable.
- [ ] Existing consent gate remains the only path to mounting microphone controls.
- [ ] Interpreter audio remains in memory and is never written to localStorage, IndexedDB, or temporary files.
- [ ] The existing backend overlap guard remains a second line of defense.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build
    npm.cmd --prefix frontend run e2e
    python -m pytest interpreter/tests/test_api.py::test_websocket_rejects_overlapping_turns interpreter/tests/test_api.py::test_dropped_turn_does_not_block_reconnect

### CP-INT-03 — Add clinician-only review for high and critical risk

**Type:** safety workflow

**User story**

> As a doctor, I want high-risk translations isolated in a clinician-only review state so that the patient cannot see or hear them before I confirm the content.

**Files likely affected**

- interpreter/frontend/src/components/InterpreterConsole.tsx
- interpreter/frontend/src/components/Transcript.tsx
- interpreter/frontend/src/components/InterpreterConsole.test.tsx
- interpreter/frontend/src/components/Transcript.test.tsx
- interpreter/frontend/src/App.css
- interpreter/frontend/tests/mock-mode.spec.ts

**Dependencies**

- CP-UX-07.
- CP-INT-02.
- Clinician/product-owner approval of the shared-device patient-masking interaction.

**Scope guard**

- Presentation and release behavior for turns already classified high/critical.
- Do not change risk lexicons, thresholds, fixtures, backend classification, product routes, or general audio state.

**Acceptance criteria**

- [ ] A newly blocked turn first renders a patient-safe mask; its draft translation is absent from the DOM until the clinician explicitly opens review.
- [ ] The clinician review labels source, draft translation, speaker, language, risk reason, and critical entities.
- [ ] The review receives focus and an accessible announcement when created.
- [ ] Unchanged text offers one action: “Xác nhận và phát.”
- [ ] Edited text offers one action: “Lưu chỉnh sửa và phát.”
- [ ] Confirming without saving cannot silently discard a visible edit.
- [ ] An empty edited translation cannot be submitted.
- [ ] TTS is never called before successful confirmation.
- [ ] Confirmation failure leaves the turn blocked and keeps source, draft translation, and escalation available.
- [ ] Critical content keeps human-interpreter escalation visible.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run e2e
    python -m pytest
    python interpreter/eval/run_eval.py --set interpreter/eval/fixtures/eval_starter.tsv --providers mock

### CP-INT-04 — Suppress automated playback after human escalation

**Type:** safety workflow

**User story**

> As a doctor who requested a human interpreter, I want automated speech stopped until I explicitly resume it so that the interface behavior matches the escalation warning.

**Files likely affected**

- interpreter/frontend/src/components/InterpreterConsole.tsx
- interpreter/frontend/src/components/InterpreterConsole.test.tsx
- interpreter/frontend/src/tts.ts
- interpreter/frontend/src/tts.test.ts (new)
- interpreter/frontend/src/App.css
- interpreter/frontend/tests/mock-mode.spec.ts

**Dependencies**

- CP-INT-02.
- CP-INT-03.
- Clinician/product-owner approval that “resume” restores local playback only and does not clear the backend escalation record.

**Scope guard**

- Escalation and TTS eligibility only.
- Do not change risk classification, low-confidence handling, recording state, session deletion, or routes.

**Acceptance criteria**

- [ ] Human-interpreter escalation remains one action away from every active state.
- [ ] One pure eligibility check permits speech only for deliverable, confirmed/corrected turns that are not low-confidence, blocked, ended, or playback-suppressed; every TTS call uses it.
- [ ] Selecting escalation immediately cancels pending browser speech and suppresses future automatic TTS, even if the escalation API later fails.
- [ ] Transcript and typed text remain available for the existing escalated-session workflow.
- [ ] Confirming a turn while escalated does not speak it.
- [ ] Resuming automated playback requires an explicit clinician action and clear warning.
- [ ] Failed escalation shows a localized error but remains fail-closed for playback until the clinician explicitly chooses a safe next action.
- [ ] Unit/e2e tests stub speechSynthesis and prove no playback after escalation.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build
    npm.cmd --prefix frontend run e2e
    python -m pytest

### CP-INT-05 — Attach low-confidence recovery to the affected turn

**Type:** safety workflow

**User story**

> As a doctor, I want uncertainty shown on the specific affected turn with a clear recovery action so that an old warning does not make the whole session appear unreliable.

**Files likely affected**

- interpreter/frontend/src/components/InterpreterConsole.tsx
- interpreter/frontend/src/components/Transcript.tsx
- interpreter/frontend/src/components/InterpreterConsole.test.tsx
- interpreter/frontend/src/components/Transcript.test.tsx
- interpreter/frontend/src/App.css
- interpreter/frontend/tests/mock-mode.spec.ts

**Dependencies**

- CP-UX-07.
- CP-INT-02.
- CP-INT-04.

**Scope guard**

- Per-turn low-confidence display and recovery only.
- Do not change confidence thresholds, backend/provider logic, high-risk confirmation, escalation, routes, or session lifecycle.

**Acceptance criteria**

- [ ] The low-confidence warning appears on the affected turn.
- [ ] The stale global turns.some(low_confidence) banner is removed; operational errors retain a separate transient status area.
- [ ] The turn offers “Nói lại” and “Nhập văn bản” recovery paths.
- [ ] “Nói lại” focuses the correct speaker control but does not begin recording automatically.
- [ ] “Nhập văn bản” focuses the correct typed input.
- [ ] Low-confidence content is not sent to TTS automatically.
- [ ] A later safe turn does not retain a stale global low-confidence warning.
- [ ] Multiple low-confidence turns retain their own state independently.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run e2e
    python -m pytest
    python interpreter/eval/run_eval.py --set interpreter/eval/fixtures/eval_starter.tsv --providers mock

### CP-INT-06 — Add end, delete, and withdraw-consent lifecycle actions

**Type:** session lifecycle

**User story**

> As a doctor or patient, I want to end the session, withdraw consent, and delete session data through clear actions so that audio and automated playback cannot continue after the encounter ends.

**Files likely affected**

- interpreter/frontend/src/api.ts
- interpreter/frontend/src/App.tsx
- interpreter/frontend/src/components/ConsentGate.tsx
- interpreter/frontend/src/components/InterpreterConsole.tsx
- interpreter/frontend/src/components/InterpreterConsole.test.tsx
- interpreter/frontend/src/App.css
- interpreter/frontend/tests/mock-mode.spec.ts

**Dependencies**

- CP-UX-06.
- CP-INT-02.
- CP-INT-04.

**Scope guard**

- Client use of existing end/delete endpoints and local cleanup only.
- Do not change backend retention policy, endpoint schemas, risk rules, routes, or general recording UX.

**Acceptance criteria**

- [ ] The doctor can end an active session without deleting it.
- [ ] Consent withdrawal immediately stops recording, media tracks, WebSocket use, and TTS.
- [ ] Delete requires an explicit confirmation and calls the existing delete endpoint.
- [ ] After end/delete/withdrawal, no turn can be submitted or spoken.
- [ ] Success returns to a clear completed/consent state without silently starting a new session.
- [ ] Starting another session always returns through consent; prior consent is not silently reused.
- [ ] API failure keeps the interface fail-closed and provides a localized retry path.
- [ ] Unmount cleanup closes the socket and releases all media tracks.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build
    npm.cmd --prefix frontend run e2e
    python -m pytest

---

## Onboarding stories

**Strategy basis.** These stories adapt five evidence-based onboarding principles to a clinical consent flow: smart defaults reduce decision fatigue (choices become "confirm a recommendation," not "author a configuration"); the goal-gradient effect (Nunes & Drèze 2006: an endowed head start raised loyalty-card completion 82%) motivates completion when — and only when — the head start is genuinely earned; reciprocity (Duolingo's lesson-before-signup raised DAU 20%) means showing the interpreter working before the legal gate; the IKEA effect means a small personalization investment raises commitment; and longer flows feel short when each screen asks one thing and embedded checklists replace pop-up tours. The telehealth "green room" pre-call check (live mic meter, device picker) is the standard pattern for device readiness.

**Persuasion boundary matrix.** Every onboarding element belongs to exactly one class:

| Class | Elements | Allowed | Forbidden |
| --- | --- | --- | --- |
| Legal | The two consent attestations | Plain language, VI-first copy, seeing the value demo beforehand | Pre-checking, defaults, gamified or animated progress rewards, urgency cues |
| Safety | Device readiness, translate-only reminder | Momentum framing (stepper position), smart default for detected working mic | Silent skipping; voice mode without a passed mic check |
| Preference | Interface language, role, session language direction, mic selection | Smart defaults, localStorage persistence, skip paths | — |

**Honest-progress policy.** A stepper step may display as complete only when the user actually completed it in this or a prior visit (persisted preference). No fabricated pre-fill. The consent step never displays complete before both attestations are checked and submitted.

**Target flow.** 1. Ngôn ngữ (auto-complete from persisted `carepath-demo-language`) → 2. Về bạn (intent quiz) → 3. Xác nhận (consent attestation, with value demo available) → 4. Kiểm tra thiết bị (green room) → 5. Bắt đầu (console, with embedded first-session checklist).

### CP-ONB-01 — Show a simulated interpreting exchange before consent

**Type:** onboarding UI, presentation only

**User story**

> As a doctor seeing CarePath for the first time, I want to watch a short simulated interpreting exchange — including how uncertainty and risky content are handled — before I attest to anything, so that my consent is informed by what the product actually does.

**Files likely affected**

- interpreter/frontend/src/components/DemoPreview.tsx (new)
- interpreter/frontend/src/components/DemoPreview.test.tsx (new)
- interpreter/frontend/src/components/ConsentGate.tsx
- interpreter/frontend/src/copy.ts
- interpreter/frontend/src/App.css
- interpreter/frontend/tests/mock-mode.spec.ts

**Dependencies**

- CP-UX-06.

**Scope guard**

- A canned, client-side replay of hardcoded turns only.
- No API calls, no WebSocket, no microphone access, no session creation, and no change to consent payload shape, checkbox requirements, or submit timing.

**Acceptance criteria**

- [ ] The pre-consent screen offers a clearly labeled simulation ("mô phỏng") that replays a canned VI↔EN exchange with three moments: a normal delivered turn, a low-confidence flagged turn, and a high-risk blocked turn awaiting clinician confirmation.
- [ ] The replay uses the localized terminology from CP-UX-07 so the demo teaches the real vocabulary.
- [ ] No network request, `getUserMedia` call, or WebSocket connection occurs during the demo.
- [ ] The demo is keyboard operable and respects `prefers-reduced-motion` (instant step-through instead of animation).
- [ ] Both consent checkboxes still start unchecked and both remain required.
- [ ] The demo never claims real clinical capability; the existing mock/simulation disclaimer remains visible.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build
    npm.cmd --prefix frontend run e2e

### CP-ONB-02 — Add a two-question intent quiz before consent

**Type:** onboarding UI

**User story**

> As a doctor starting a session, I want to answer two quick questions about who I am and which language direction I need so that the rest of the flow is already set up for me.

**Files likely affected**

- interpreter/frontend/src/components/IntentQuiz.tsx (new)
- interpreter/frontend/src/components/IntentQuiz.test.tsx (new)
- interpreter/frontend/src/App.tsx
- interpreter/frontend/src/App.test.tsx
- interpreter/frontend/src/copy.ts
- interpreter/frontend/src/App.css

**Dependencies**

- CP-UX-05.

**Scope guard**

- Local UI state and localStorage persistence only.
- Answers pre-select later controls but must not change consent payload, session creation, API calls, or the internal speaker/language values doctor, patient, vi, en.

**Acceptance criteria**

- [ ] Exactly two questions, one per screen: role ("Hôm nay bạn là ai?" — Bác sĩ / Nhân viên phòng khám) and session language direction.
- [ ] Both questions show a pre-selected recommended default (Bác sĩ, VI→EN) so the fast path is two confirms, not two blank choices.
- [ ] A visible skip action applies the defaults and continues.
- [ ] Answers persist in localStorage under a `carepath-onboarding-` prefix and pre-select the corresponding console controls after consent.
- [ ] Returning users with persisted answers see the quiz pre-filled from storage.
- [ ] No new dependency is added.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build

### CP-ONB-03 — Add an honest-progress onboarding stepper

**Type:** onboarding UI, presentation only

**User story**

> As a doctor moving toward a session, I want to see where I am in a short sequence of steps — with the steps I have already satisfied marked done — so that the mandatory consent and device check feel like finishing something already underway.

**Files likely affected**

- interpreter/frontend/src/components/OnboardingStepper.tsx (new)
- interpreter/frontend/src/components/OnboardingStepper.test.tsx (new)
- interpreter/frontend/src/App.tsx
- interpreter/frontend/src/components/ConsentGate.tsx
- interpreter/frontend/src/copy.ts
- interpreter/frontend/src/App.css

**Dependencies**

- CP-ONB-02.
- CP-UX-06.

**Scope guard**

- Progress presentation only, replacing the static consent-steps list in ConsentGate.
- Step completion must follow the honest-progress policy above; no step may display complete without a real completed action or persisted prior choice.
- Do not change consent requirements, payload, session creation, or audio behavior.

**Acceptance criteria**

- [ ] Five steps: Ngôn ngữ → Về bạn → Xác nhận → Kiểm tra thiết bị → Bắt đầu.
- [ ] The language step shows complete only when a persisted `carepath-demo-language` value exists; the quiz step only after CP-ONB-02 answers exist.
- [ ] The consent step never displays complete before both attestations are checked and submitted.
- [ ] The static `consent-steps` ordered list is removed rather than duplicated.
- [ ] Current step uses `aria-current="step"`; state is conveyed by text and structure, not color alone.
- [ ] No horizontal overflow at 360×800.
- [ ] In mock mode, each step transition logs one debug-level view/complete event so per-step drop-off is measurable.
- [ ] Plain CSS only; no new dependency.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build
    npm.cmd --prefix frontend run e2e

### CP-ONB-04 — Add a post-consent device readiness check

**Type:** onboarding and audio workflow

**User story**

> As a doctor about to start an interpreted encounter, I want to confirm my microphone works before the patient is in front of me so that the first clinical turn is not spent troubleshooting audio.

**Files likely affected**

- interpreter/frontend/src/components/DeviceCheck.tsx (new)
- interpreter/frontend/src/components/DeviceCheck.test.tsx (new)
- interpreter/frontend/src/App.tsx
- interpreter/frontend/src/components/InterpreterConsole.tsx
- interpreter/frontend/src/copy.ts
- interpreter/frontend/src/App.css
- interpreter/frontend/tests/mock-mode.spec.ts

**Dependencies**

- CP-ONB-03.
- CP-INT-02.

**Scope guard**

- Rendered only after consent is recorded and the session is created, before the console mounts.
- Browser-native APIs only: `enumerateDevices`, `getUserMedia`, Web Audio API for the level meter. Test audio stays in memory, is never transmitted or persisted, and every track stops on unmount or navigation.
- Do not change WebSocket behavior, session endpoints, risk rules, or TTS.

**Acceptance criteria**

- [ ] No `getUserMedia` call occurs before the consent submission; an e2e test asserts this ordering.
- [ ] The screen shows a live input-level indicator that visibly responds to speech.
- [ ] When multiple microphones exist, a picker is offered and the detected working device is pre-selected; the choice persists for the session.
- [ ] Permission denial and no-device states show localized Vietnamese-first remediation copy and a retry action.
- [ ] The doctor may explicitly continue in typed-only mode; voice mode is unavailable until a mic check passes (fail-closed).
- [ ] All media tracks are stopped when leaving the screen in any direction.
- [ ] The console reuses the granted permission and no longer surprises the doctor with a first-turn permission prompt.
- [ ] The check is keyboard operable and announced to screen readers.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build
    npm.cmd --prefix frontend run e2e

### CP-ONB-05 — Embed a first-session checklist in the console

**Type:** onboarding UI, presentation only

**User story**

> As a doctor in my first session, I want a small in-page checklist of the core safety actions so that I learn the workflow from real events instead of a pop-up tour blocking my controls.

**Files likely affected**

- interpreter/frontend/src/components/SessionChecklist.tsx (new)
- interpreter/frontend/src/components/SessionChecklist.test.tsx (new)
- interpreter/frontend/src/components/InterpreterConsole.tsx
- interpreter/frontend/src/copy.ts
- interpreter/frontend/src/App.css

**Dependencies**

- CP-INT-02.
- CP-INT-03.
- CP-INT-04.
- CP-INT-05.

**Scope guard**

- A display-only panel driven by state the console already holds. No new events, API calls, or workflow changes.
- Never a modal, overlay, or tour; it must not cover or disable any clinical control.

**Acceptance criteria**

- [ ] Checklist items map to real outcome events: first turn delivered, a read-back/confirmation completed, and the human-interpreter escalation control located (focused or opened).
- [ ] Items check themselves off from real console state; they cannot be checked manually.
- [ ] The panel is dismissible, the dismissal persists in localStorage, and it never reappears modally.
- [ ] Checklist announcements use polite live-region priority and never compete with risk or escalation alerts.
- [ ] Vietnamese-first with complete English mode.
- [ ] Existing risk, confirmation, escalation, and low-confidence behavior is unchanged.

**Test/validation command**

    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build
    npm.cmd --prefix frontend run e2e

---

## Final QA story

### CP-QA-01 — Run the complete release, accessibility, and visual gate

**Type:** QA only

**User story**

> As the CarePath team, we want one final production-like verification pass so that Vietnamese copy, canonical routes, clinical safety, responsive behavior, and accessibility ship together.

**Files likely affected**

- scribe/frontend/tests/demo-flow.spec.ts
- scribe/frontend/tests/combined-product.spec.ts (new, if used as the production browser harness)
- interpreter/frontend/tests/mock-mode.spec.ts
- scribe/tests/test_combined_app.py
- scribe/frontend/scripts/validate-deploy-env.test.mjs
- README.md
- README.hf-space.md
- scribe/frontend/README.md
- docs/deploy.md
- docs/ux-redesign-carepath.md

**Dependencies**

- Every story listed in the delivery table.
- A working browser capture surface for visual evidence.

**Scope guard**

- Tests, evidence, and documentation only.
- If QA finds a feature defect, reopen the owning story or create a narrow follow-up; do not hide feature work inside the QA story.

**Acceptance criteria**

- [ ] Direct production-like loads return 200 for /, /ghi-chep-lam-sang/, and /phien-dich-y-khoa/.
- [ ] Legacy /console, /console/, and /#/scribe links reach the canonical product.
- [ ] The internal review route works and is absent from public navigation.
- [ ] Homepage and both products are captured at 360×800, 390×844, 768×1024, and 1440×900.
- [ ] Captures show no clipping, hidden action, broken Vietnamese wrapping, horizontal overflow, or accidental patient exposure.
- [ ] Keyboard-only flows cover homepage selection, the intent quiz, consent, the device readiness check, typed turn, PTT, high-risk confirmation, escalation, low-confidence recovery, end, and delete.
- [ ] The onboarding screens (quiz, stepper, device check) are captured at the four viewports and pass the axe checks.
- [ ] An e2e assertion proves no `getUserMedia` call occurs before consent submission, including on the device-check screen.
- [ ] The stepper never displays the consent step as complete before both attestations are submitted, and no consent control is ever pre-checked.
- [ ] Automated axe checks have no serious or critical violations in key states.
- [ ] Frontend accessibility checks reuse the repository's existing axe package through the combined production harness; no duplicate accessibility dependency is added to frontend solely for this gate.
- [ ] Manual checks cover 200% zoom, Windows high contrast, reduced motion, and NVDA reading/focus order.
- [ ] High/critical-risk content never reaches patient display or TTS before confirmation.
- [ ] Low-confidence content remains visibly flagged.
- [ ] Microphone capture never occurs before consent and all tracks stop on end/withdraw/delete.
- [ ] Vietnamese NFC/diacritics validation passes.
- [ ] README and deploy docs match the implemented routes and readiness claims.

**Test/validation command**

    python -m ruff check .
    python -m pytest
    python scripts/smoke_backend.py
    npm.cmd --prefix frontend run lint
    npm.cmd --prefix frontend test
    npm.cmd --prefix frontend run build
    npm.cmd --prefix frontend run e2e
    npm.cmd --prefix frontend run e2e:prod
    npm.cmd --prefix site run lint
    npm.cmd --prefix site test
    npm.cmd --prefix site run build
    npm.cmd --prefix site run e2e
    npm.cmd --prefix site run build
    npm.cmd --prefix site run test:deploy-env
    npm.cmd --prefix site run lighthouse
    python interpreter/eval/run_eval.py --set interpreter/eval/fixtures/eval_starter.tsv --providers mock

## Deferred unless separately approved

- Changing risk rules, confidence thresholds, provider behavior, API schemas, or retention policy
- Claiming production readiness for real-time medical interpretation
- Adding a routing, state-management, or localization dependency
- Reworking authentication beyond making the existing token-gated review page reachable
- Rebranding runtime assets from the generated CarePath Translate brand board
- Rewriting historical plans in `docs/history/`
