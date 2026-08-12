# CarePath Unified Deploy

Use `https://carepath-medicaltranslation.vercel.app` as the public Scribe site. One Hugging
Face Space runs the Scribe tool at `/ghi-chep-lam-sang/`, the Scribe API at
`/api/v1/*`, and the retained Interpreter API at `/api/*` + `/ws/*`.
`/phien-dich-y-khoa/*` and `/console/*` are intentionally public 404s while
the Interpreter remains in development.

## Hugging Face Space

Reuse the existing Docker Space
[`tranth3truong/carepath-api`](https://huggingface.co/spaces/tranth3truong/carepath-api),
served at `https://tranth3truong-carepath-api.hf.space`. Deploy this unified
repository there; it retains the Interpreter API but does not serve the
unfinished Interpreter browser workflow.

1. Rebuild the existing `tranth3truong/carepath-api` Space with **Docker** as
   the SDK. Create a replacement only if that Space is no longer available.
2. Copy `README.hf-space.md` to the Space as `README.md` so the Space has:

```yaml
---
title: CarePath
sdk: docker
app_port: 7860
---
```

3. Push this repo to the Space. The root `Dockerfile` builds `scribe/frontend/`
   in a node stage (that build enforces the Vietnamese diacritics gate),
   installs both API packages, pre-downloads the Gipformer int8 ONNX files, and
   starts Uvicorn on port `7860`.
4. Set these Space secrets:

```text
LLM_PROVIDER=ckey
LLM_API_KEY=<your CKey key>
LLM_MODEL=gpt-5.4
TEAM_CODE=<shared internal demo code>
SOAP_RATE_LIMIT_PER_IP_HOUR=3
SOAP_RATE_LIMIT_PER_IP_DAY=10
SOAP_RATE_LIMIT_GLOBAL_DAY=100
APP_ENV=prod
CORS_ORIGINS=https://carepath-medicaltranslation.vercel.app
```

The interpreter defaults to mock mode, which returns `[vi->en] …` echoes. For
`/kham-song-ngu/` and `/dich-giay-to/` to actually translate on the deployed
Space, add **two** more secrets:

```text
PROVIDER_MODE=ckey
ADMIN_TOKEN=<anything except change-me>
```

`ADMIN_TOKEN` is not optional here and its absence is not a degraded mode: it is
a **hard boot failure**. `validate_runtime_settings()`
(`interpreter/app/main.py:19`) runs first inside `interpreter_lifespan`, which
`scribe/carepath/main.py:98` wraps, so it gates the whole combined app — and it
raises `RuntimeError` when `PROVIDER_MODE` is `ckey` **or** `cloud` while
`ADMIN_TOKEN` is still its `change-me` default. Setting `PROVIDER_MODE=ckey`
alone takes the Space down with *"Your space is in error"*, which reads like an
infrastructure problem rather than a missing variable. Check the Space's build
log: the message names the fix.

Both must be Space **secrets**, not variables. A Hugging Face variable is
visible to anyone who can see the Space; `ADMIN_TOKEN` guards `/api/admin/review`
and `LLM_API_KEY` bills real tokens.

It reuses `LLM_BASE_URL`, `LLM_API_KEY` and `LLM_MODEL` above — one CKey
account configures both modules. Measured latency across 50 turns: median 15s,
p90 54s, max 206s, so a live visitor waits. `PROVIDER_MODE=demo` is the
offline scripted scenario for the pitch laptop, not for a public URL, because
anything off-script falls back to a visible placeholder.

The public demo hub at `/thu-nghiem/` is built for both cases and reads
`GET /api/health` to decide what it may honestly offer:

| `provider_mode` | What the hub shows |
| --- | --- |
| `ckey` | Everything: the scripted sample, own-document upload, and the two-way conversation. |
| `demo` | The scripted sample only. Own-upload and the conversation panel are hidden, because in this mode `read_document` ignores the uploaded bytes and the canned map covers nothing a visitor would actually type. This is what makes `demo` safe on a public URL. |
| `mock` or unreachable | Nothing runnable, and a notice saying so. It never invents output. |

The sample path sends `X-CarePath-Sample: 1`, which forces scripted mode for
that one request, so samples stay instant and free even on `ckey`. Own-uploads
and conversation turns on `ckey` bill real tokens, capped at five runs per IP
per day by the `/api/demo/*` functions.

The `cloud` mode (Anthropic/OpenAI direct) additionally needs
`ANTHROPIC_API_KEY` and `OPENAI_API_KEY`. It needs a non-default `ADMIN_TOKEN`
too, but so does `ckey` — this paragraph used to claim the requirement was
cloud-only, and the code has always refused `change-me` in both
(`interpreter/app/main.py:21`). That wording is what took the Space down the
first time `PROVIDER_MODE=ckey` was set.

The Vercel site uploads Scribe audio directly to the Space, so its exact origin
must be present in `CORS_ORIGINS`. Add local Vite origins as comma-separated
values only when testing local frontends against the deployed API.

Requests with header `X-Team-Code: <TEAM_CODE>` bypass the SOAP rate limits
for internal doctor-comparison runs. Limited requests return HTTP `429`,
`Retry-After`, and JSON body
`{"detail":{"message":"...","retry_after_seconds":3600}}` — the Scribe tool
surfaces that message to the user.

## Local Docker Check

```powershell
docker build -t carepath .
docker run --rm -p 7860:7860 `
  -e LLM_PROVIDER=ckey `
  -e "LLM_API_KEY=$env:LLM_API_KEY" `
  -e LLM_MODEL=gpt-5.4 `
  -e APP_ENV=prod `
  carepath
```

Keyless variant (mock ASR + offline LLM + mock interpreter — must also work):

```powershell
docker run --rm -p 7860:7860 `
  -e ASR_PROVIDER=mock -e ALLOW_MOCK_ASR=true -e LLM_PROVIDER=offline `
  carepath
```

In another terminal:

```powershell
curl.exe http://127.0.0.1:7860/api/v1/health
curl.exe http://127.0.0.1:7860/api/health
curl.exe -o NUL -w "%{http_code}`n" http://127.0.0.1:7860/
curl.exe -o NUL -w "%{http_code}`n" http://127.0.0.1:7860/ghi-chep-lam-sang/
curl.exe -o NUL -w "%{http_code}`n" http://127.0.0.1:7860/phien-dich-y-khoa/
curl.exe -X POST http://127.0.0.1:7860/api/v1/soap-notes `
  -F "audio=@C:\path\to\demo.wav" `
  -F "encounter_context=Phòng khám nội tổng quát"
```

## Canonical Vercel site

The `scribe/frontend/` directory is the static marketing deployment at
`https://carepath-medicaltranslation.vercel.app`:

1. In the Vercel project settings, change **Root Directory** from the removed
   `apps/web-next` to `scribe/frontend` (framework/build/output come from
   `scribe/frontend/vercel.json`).
2. Set these Vercel environment variables:

```text
VITE_API_BASE=
VITE_WS_BASE=https://tranth3truong-carepath-api.hf.space
DEMO_API_BASE=https://tranth3truong-carepath-api.hf.space
VITE_LEAD_ENDPOINT=<optional lead endpoint>
VITE_LEAD_EMAIL=<pilot contact email>
```

`VITE_API_BASE` is **empty on purpose** (DEC-0021). `vercel.json` rewrites
`/api/*` to the Space, so the browser calls its own origin and no
`CORS_ORIGINS` entry stands between the site and the backend. Setting it to an
absolute origin restores the cross-origin coupling that took both tool routes
down when the domain moved to `carepath-medicaltranslation.vercel.app` while
the Space still allowed only `carepath-omega.vercel.app`.

`VITE_WS_BASE` is required whenever `VITE_API_BASE` is empty: a Vercel rewrite
will not carry a websocket upgrade to an external host, so `/ws/*` still goes
direct. That is safe — the origin check in `scribe/carepath/main.py` is HTTP
middleware and never runs for a websocket scope.

`DEMO_API_BASE` is read server-side by the `/api/demo/*` functions, so the API
host no longer appears in the client bundle.

3. Earlier guidance here said not to add Vercel API rewrites because the Space
   owns those routes. That is superseded: the `/api/*` rewrite is what makes the
   API same-origin. It excludes `/api/demo/*`, which are Vercel functions.

The Vercel build runs `npm run validate:deploy` before compiling. It fails when
`VITE_API_BASE` is set but invalid, does not use HTTPS, contains a
query/fragment, or is not the bare `/` pathname; when both `VITE_API_BASE` and
`VITE_WS_BASE` are empty; or when an SPA route
in `src/App.tsx` has no matching rewrite in `vercel.json` — without one, a direct
visit to that route is a hard 404. Local and combined-service builds still use
same-origin fallbacks because the normal `npm run build` skips this
deployment-only check.

The interpreter console was deleted once `/kham-song-ngu/` replaced it; its
backend stays on the Space for the WebSocket API, and `/phien-dich-y-khoa/` and
`/console/` return an explicit 404. The pilot form remains client-side unless
`VITE_LEAD_ENDPOINT` is configured.

## Keep-Alive

The workflow in `.github/workflows/keepalive.yml` pings the Space every 12
hours. Set the GitHub repository variable:

```text
SPACE_URL=https://tranth3truong-carepath-api.hf.space
```

Then run **Actions > Keep HF Space Awake > Run workflow** once and confirm the
job succeeds.

## Final Smoke

1. Open the Space URL: the landing renders, Vietnamese by default, and the
   English resolves under each prescription line within about two seconds.
2. Open `/kham-song-ngu/`, consent, start a visit, and type a Vietnamese dose.
   Confirm the turn is gated and the patient pane shows nothing until you
   confirm it.
3. Open `/ghi-chep-lam-sang/`, upload a short clip, and verify the SOAP draft renders
   with the review banner.
4. Confirm `/phien-dich-y-khoa/` and `/console/` return HTTP 404.
5. Confirm `GET /api/v1/health` reports `llm_provider: ckey` and
   `asr_ready: true`, and `GET /api/health` reports `provider_mode: ckey`.

Note the deploy commit shape: the Space's `README.md` carries the
`sdk: docker` frontmatter, so a plain branch push would overwrite it with the
repository README and break the Space's build configuration. Deploy by
building a commit that copies `README.hf-space.md` over `README.md` first.
