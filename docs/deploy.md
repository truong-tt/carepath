# CarePath Unified Deploy

One Hugging Face Space runs everything: the demo site at `/`, the Scribe tool
at `/#/scribe`, the interpreter console at `/console/`, the scriber API at
`/api/v1/*`, and the interpreter API at `/api/*` + `/ws/*`. Everything is
same-origin, so no CORS configuration is needed for the deployed frontends.

## Hugging Face Space

1. Create a new Hugging Face Space and choose **Docker** as the SDK.
2. Copy `README.hf-space.md` to the Space as `README.md` so the Space has:

```yaml
---
title: CarePath
sdk: docker
app_port: 7860
---
```

3. Push this repo to the Space. The root `Dockerfile` builds the two Vite
   frontends in a node stage (the site build enforces the Vietnamese
   diacritics gate), installs both API packages, pre-downloads the Gipformer
   int8 ONNX files, and starts Uvicorn on port `7860`.
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
```

The interpreter module runs in mock mode by default and needs no secrets.
When its cloud track lands, it will additionally need `PROVIDER_MODE=cloud`,
`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and a non-default `ADMIN_TOKEN`
(startup refuses `change-me` in cloud mode).

`CORS_ORIGINS` can stay unset for the Space (same-origin). Set it only when a
frontend is hosted elsewhere or for local Vite dev against the deployed API,
e.g. `CORS_ORIGINS=http://localhost:5173`.

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
curl.exe -o NUL -w "%{http_code}`n" http://127.0.0.1:7860/console/
curl.exe -X POST http://127.0.0.1:7860/api/v1/soap-notes `
  -F "audio=@C:\path\to\demo.wav" `
  -F "encounter_context=Phòng khám nội tổng quát"
```

## Optional: keep the existing Vercel URL

The Space alone is a complete deploy. If you also want the site on an existing
Vercel project (e.g. `https://carepath-omega.vercel.app`), the new `site/` is a
static Vite build that works there directly:

1. In the Vercel project settings, change **Root Directory** from the removed
   `apps/web-next` to `site` (framework/build/output come from
   `site/vercel.json`).
2. Set these Vercel environment variables:

```text
VITE_API_BASE=https://<your-hf-space>.hf.space
VITE_CONSOLE_URL=https://<your-hf-space>.hf.space/console/
VITE_LEAD_ENDPOINT=<optional lead endpoint>
VITE_LEAD_EMAIL=<pilot contact email>
```

3. Allow the Vercel origin on the Space (the Scribe tool posts audio directly
   to it):

```text
CORS_ORIGINS=https://carepath-omega.vercel.app
```

The interpreter console itself stays on the Space (`/console/` needs the
WebSocket API); the Vercel landing links out to it via `VITE_CONSOLE_URL`.
The scripted demo and the pilot form are fully client-side and need nothing.

## Keep-Alive

The workflow in `.github/workflows/keepalive.yml` pings the Space every 12
hours. Set the GitHub repository variable:

```text
SPACE_URL=https://<your-hf-space>.hf.space
```

Then run **Actions > Keep HF Space Awake > Run workflow** once and confirm the
job succeeds.

## Final Smoke

1. Open the Space URL: the CarePath landing renders, Vietnamese by default.
2. Run the scripted interpreter simulation on the landing.
3. Open `/#/scribe`, upload a short clip, and verify the SOAP draft renders
   with the review banner.
4. Open `/console/`, accept consent, start a mock session, and send a typed
   turn.
5. Confirm `GET /api/v1/health` reports `llm_provider: ckey` and
   `asr_ready: true`, and `GET /api/health` reports `provider_mode: mock`.
