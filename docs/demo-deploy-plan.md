# CarePath free demo deployment — execution goals

**Executor split:** UI/UX goals (3, 4) → **Claude Opus 4.8**. Backend/infra goals (1, 2, 5) → **GPT-5.5 (Codex) xhigh**. Claude judges the finished demo against the rubric at the end.

## Context

CarePath demo must go live, free tier, for real users. Two user problems:

1. **Phone audio.** Users record consults on phones. Current tool page ([apps/web/app/index.html:52-61](apps/web/app/index.html#L52-L61)) only has desktop file picker + drag-drop — no in-browser recording, no mobile-first UI.
2. **Cost.** User wants Next.js/Vercel stack where it saves money. Reality check from exploration: the cost center is the Python backend (FastAPI + sherpa-onnx Gipformer ASR + CKey LLM at api.xah.io) — it cannot run on Vercel serverless. Frontend is the only part Vercel can host.

**Decided architecture** (user confirmed):
- **Hugging Face Space (Docker, free tier, 2 vCPU/16GB)** runs the existing FastAPI app (`apps/api/carepath/`) — API only. CKey key as Space secret.
- **Vercel Hobby (free)** hosts a new Next.js frontend (rewrite of the 2 vanilla pages). Browser calls the Space directly with CORS — big uploads never touch Vercel bandwidth.
- **GitHub Actions cron** pings Space `/health` every 12h so it never hits the 48h idle sleep.
- **Clerk and Convex deferred** — user chose rate-limit + team code over auth; demo persists nothing. Add when billing starts.

## Current-state facts executors must respect

- Frontend today is vanilla, served same-origin by FastAPI static mount ([apps/api/carepath/main.py:160-165](apps/api/carepath/main.py#L160-L165)). Keep that mount working for local dev.
- API: `GET /api/v1/health`, `POST /api/v1/soap-notes` (multipart: `audio` file + optional `encounter_context`). Response schema in [apps/api/carepath/schemas.py:69-76](apps/api/carepath/schemas.py#L69-L76).
- Server accepts `.wav .mp3 .m4a .aac .flac .ogg .oga .opus .webm`, 25MB cap ([main.py:28-39](apps/api/carepath/main.py#L28-L39)). MediaRecorder output (webm on Android, mp4/m4a on iOS) already passes — just name the Blob with correct extension.
- ASR model (~65M ONNX) downloads from HF on first request ([services/asr.py:366-395](apps/api/carepath/services/asr.py#L366-L395)); `pipeline.warmup()` exists.
- No auth anywhere. No deployment config anywhere. No `package.json` anywhere.
- Design constraints (non-negotiable, from project memory): light-theme-locked, **no fake social proof/testimonials**, current visual identity (Plus Jakarta Sans, existing logo/assets in `apps/web/assets/`). Vietnamese UI text.
- Never commit secrets. `LLM_PROVIDER=ckey`, `LLM_API_KEY` are env-only. Verify gateway with `scripts/preflight.py` (gpt-5.4 works; claude-opus-4-7-kiro is rejected — don't switch models).

---

## Goal 1 — Backend deployable to HF Spaces (Docker)

**Executor: Codex 5.5 xhigh.** Scope: repo root `Dockerfile`, Space metadata, CORS, warmup.

- `Dockerfile`: python slim base, install package from `pyproject.toml` (runtime deps only — **exclude** `[training]` extras; no torch), bake the ASR model into the image at build time (pre-download via `huggingface-hub` so wake-from-sleep is fast), run `uvicorn carepath.main:app --app-dir apps/api --host 0.0.0.0 --port 7860`. HF Spaces requires port 7860 + a README frontmatter block (`sdk: docker`, `app_port: 7860`) — put that in a dedicated Space README or document exactly what to paste.
- Add `CORSMiddleware` to `main.py`, origins from env `CORS_ORIGINS` (comma-separated; empty ⇒ middleware off, preserving today's same-origin local behavior).
- Call `pipeline.warmup()` on startup (lifespan) so first user request isn't the model-load request.
- Docs: short `docs/deploy.md` — create Space, set secrets (`LLM_PROVIDER=ckey`, `LLM_API_KEY`, `LLM_MODEL=gpt-5.4`, `CORS_ORIGINS`, `TEAM_CODE`, `APP_ENV=prod`), push.

**Acceptance:** `docker build` + `docker run` locally → `curl /api/v1/health` shows `llm_provider: ckey`, `asr_ready: true` without downloading model at runtime; sample audio → full SOAP JSON via curl.

## Goal 2 — Abuse guard: rate limit + team code bypass

**Executor: Codex 5.5 xhigh.** Scope: `apps/api/carepath/main.py` (or small new module), `config.py`, `schemas.py` if needed.

- In-process (single container — no external store needed): per-IP sliding-window limit on `POST /api/v1/soap-notes` (env-tunable, default 3/hour and 10/day per IP) **plus** global daily cap (default 100/day) as CKey-budget backstop.
- Client IP from `X-Forwarded-For` (HF Space sits behind a proxy) with sane fallback.
- `X-Team-Code` request header matching env `TEAM_CODE` ⇒ bypass all limits (teammates run unlimited audios to build SOAP notes for doctor comparison).
- 429 with Vietnamese message + retry-after; no dependency needed — ~30 lines with a dict is fine, but `slowapi` acceptable if it stays simpler.
- Constant-time compare for the code; never log it.

**Acceptance:** scripted curl: 4th request within an hour from same IP → 429; same requests with `X-Team-Code` → all 200; wrong code → limited like anonymous.

## Goal 3 — Next.js app: scaffold + landing page port

**Executor: Claude Opus 4.8 (UI/UX).** Scope: new `apps/web-next/` (Next.js App Router + Tailwind; shadcn only if a component genuinely earns it). Keep `apps/web/` untouched until parity confirmed.

- Port landing page (`apps/web/index.html` + `landing.css` + `landing.js`) to Next.js, pixel-faithful: same copy, sections, light theme, fonts/logo moved into the app's assets. Static-rendered (SSG) — landing must load instantly and stay up even if the Space is asleep.
- Add QR code on landing (pre-generated SVG asset pointing at the production tool URL, no runtime QR lib) with caption "Mở trên điện thoại để ghi âm" so desktop visitors jump to phone.
- `NEXT_PUBLIC_API_BASE` env for the Space URL; empty ⇒ relative paths (local same-origin dev against uvicorn still works).

**Acceptance:** `next build` clean; landing visually matches current page side-by-side; Lighthouse mobile ≥ 90 performance; zero calls to API from landing.

## Goal 4 — Tool page in Next.js: phone recording + mobile-first

**Executor: Claude Opus 4.8 (UI/UX).** Scope: `apps/web-next/` tool route (`/app`). Depends on Goal 3 scaffold; API contract from Goals 1-2 (header name `X-Team-Code`, 429 shape) must be final first.

Port the tool ([apps/web/app.js](apps/web/app.js)) and add:

- **In-browser recording** via native `MediaRecorder` (no deps): record / pause / stop, elapsed timer, mono + `audioBitsPerSecond` ≈ 48k where honored. Name the Blob by actual `mimeType` (`recording.webm` Android / `recording.m4a` iOS Safari) so the server suffix check passes. Preview player + "Ghi lại" (re-record) before submit. Feature-detect: no `MediaRecorder`/`getUserMedia` ⇒ hide button, file upload remains.
- **Mobile-first layout**: thumb-size targets, file picker (`accept="audio/*"`) which on phones already opens voice-memo/file sources, drag-drop kept for desktop.
- Existing flow preserved: context field, 3-step progress (Phiên âm → Hiệu chỉnh → Soạn SOAP), health badge with demo-mode detection, SOAP result rendering incl. `missing_information` + `review_required`.
- **Team code**: small "Mã nội bộ" field (collapsed by default), persisted in `localStorage`, sent as `X-Team-Code` header when set.
- Friendly errors: 429 → Vietnamese "limit reached" message; client-side pre-check of file size vs 25MB; warning for very long recordings (>20 min ⇒ "processing may take several minutes" — free CPU is slow, request stays open).

**Acceptance:** on a real phone (iOS Safari + Android Chrome): record 30s → submit → SOAP renders. Desktop upload path unchanged. 26MB file rejected client-side with clear message.

## Goal 5 — Wire up production: Vercel + CORS + keep-alive

**Executor: Codex 5.5 xhigh.** Scope: Vercel config, `.github/workflows/keepalive.yml`, final env wiring. Runs last, after Goals 3-4 ship.

- Deploy `apps/web-next` to Vercel (Root Directory = `apps/web-next`); set `NEXT_PUBLIC_API_BASE` to the Space URL. Document steps in `docs/deploy.md`.
- Set `CORS_ORIGINS` on the Space to the exact Vercel prod domain (+ `http://localhost:3000` for dev). No wildcard.
- `keepalive.yml`: cron every 12h, `curl -fsS $SPACE_URL/api/v1/health` (URL as repo variable). 48h sleep threshold ⇒ 12h ping = never sleeps, ~0 Actions minutes.
- Update QR asset (Goal 3) to final prod URL. Retire `apps/web/` from the deployment path only after parity sign-off (leave in repo for local dev).

**Acceptance:** public Vercel URL → record on phone → SOAP notes, end-to-end, on the live stack. Cross-origin request succeeds from prod domain, blocked from others. Actions run green.

---

## Judging rubric (Claude, after Codex finishes)

1. **E2E phone flow**: iOS Safari + Android Chrome — record, submit, SOAP renders. The headline feature.
2. **Security sweep**: view-source + built JS bundle grep for CKey key (must be absent); CORS rejects foreign origins; team code not logged; 429s enforce as specced.
3. **Cold/warm behavior**: wake-from-sleep time after forced restart; warmup means first request ≠ model load.
4. **Design fidelity**: landing parity with current `apps/web`, light theme locked, no invented social proof, Vietnamese copy intact.
5. **Perf**: Lighthouse mobile on landing + tool; upload of 20MB file survives on mobile network throttling.
6. **Cost check**: everything on free tiers; only metered spend is CKey per pipeline run, capped by Goal 2 limits.

## Cost summary

$0 hosting (HF Space free + Vercel Hobby + GitHub Actions). Only real spend: CKey gpt-5.4 per run, capped at 100 runs/day globally, bypass only via team code. Vercel Hobby is non-commercial — fine for free demo; revisit when charging.

## Deferred (explicitly not now)

Clerk auth + billing, Convex persistence/history, PWA/share-target, 50MB cap raise, async job queue for long audio, custom domain.
