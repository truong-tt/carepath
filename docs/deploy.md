# CarePath Unified Deploy

Use `https://carepath-omega.vercel.app` as the public Scribe site. One Hugging
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

3. Push this repo to the Space. The root `Dockerfile` builds `scribe/frontend/` and
   `interpreter/frontend/` in a node stage (the site build enforces the Vietnamese
   diacritics gate), installs both API packages, pre-downloads the Gipformer
   int8 ONNX files, and starts Uvicorn on port `7860`.
   Set the Docker build arg `VITE_PUBLIC_SITE_URL=https://carepath-omega.vercel.app`
   so the Interpreter's “Tất cả chức năng” link returns to the public site
   with the selected language.
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
CORS_ORIGINS=https://carepath-omega.vercel.app
```

The interpreter module runs in mock mode by default and needs no secrets.
When its cloud track lands, it will additionally need `PROVIDER_MODE=cloud`,
`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and a non-default `ADMIN_TOKEN`
(startup refuses `change-me` in cloud mode).

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
`https://carepath-omega.vercel.app`:

1. In the Vercel project settings, change **Root Directory** from the removed
   `apps/web-next` to `scribe/frontend` (framework/build/output come from
   `scribe/frontend/vercel.json`).
2. Set these Vercel environment variables:

```text
VITE_API_BASE=https://tranth3truong-carepath-api.hf.space
VITE_CONSOLE_URL=https://tranth3truong-carepath-api.hf.space/phien-dich-y-khoa/
VITE_LEAD_ENDPOINT=<optional lead endpoint>
VITE_LEAD_EMAIL=<pilot contact email>
```

3. Confirm the Space contains the Vercel origin configured above. Do not add
   Vercel API or WebSocket rewrites; the Space owns those routes.

The Vercel build runs `npm run validate:deploy` before compiling. It fails when
either URL is missing or invalid, does not use HTTPS, uses a different origin,
contains a query/fragment, or does not use the exact `/` and `/phien-dich-y-khoa/`
pathnames. Local
and combined-service builds still use same-origin fallbacks because the normal
`npm run build` does not run this deployment-only check.

The Interpreter backend stays on the Space because it needs the WebSocket API,
but its browser frontend is disabled. `VITE_CONSOLE_URL` remains a build-time
compatibility setting until the public-site validation is simplified. The pilot
form remains client-side unless `VITE_LEAD_ENDPOINT` is configured.

## Keep-Alive

The workflow in `.github/workflows/keepalive.yml` pings the Space every 12
hours. Set the GitHub repository variable:

```text
SPACE_URL=https://tranth3truong-carepath-api.hf.space
```

Then run **Actions > Keep HF Space Awake > Run workflow** once and confirm the
job succeeds.

## Final Smoke

1. Open the Space URL: the CarePath landing renders, Vietnamese by default.
2. Run the scripted interpreter simulation on the landing.
3. Open `/ghi-chep-lam-sang/`, upload a short clip, and verify the SOAP draft renders
   with the review banner.
4. Confirm `/phien-dich-y-khoa/` and `/console/` return HTTP 404.
5. Confirm `GET /api/v1/health` reports `llm_provider: ckey` and
   `asr_ready: true`, and `GET /api/health` reports `provider_mode: mock`.
