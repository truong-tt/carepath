# CarePath Free Demo Deploy

## Backend: Hugging Face Space

1. Create a new Hugging Face Space.
2. Choose **Docker** as the SDK.
3. Copy `README.hf-space.md` to the Space as `README.md` so the Space has:

```yaml
---
title: CarePath API
sdk: docker
app_port: 7860
---
```

4. Push this repo to the Space. The root `Dockerfile` installs only runtime
   Python dependencies from `pyproject.toml`, pre-downloads the Gipformer int8
   ONNX files, and starts Uvicorn on port `7860`.
5. Set these Space secrets:

```text
LLM_PROVIDER=ckey
LLM_API_KEY=<your CKey key>
LLM_MODEL=gpt-5.4
CORS_ORIGINS=https://<your-vercel-app>.vercel.app
TEAM_CODE=<shared internal demo code>
SOAP_RATE_LIMIT_PER_IP_HOUR=3
SOAP_RATE_LIMIT_PER_IP_DAY=10
SOAP_RATE_LIMIT_GLOBAL_DAY=100
APP_ENV=prod
```

Use a comma-separated `CORS_ORIGINS` value when adding local dev later, for
example `https://<your-vercel-app>.vercel.app,http://localhost:3000`.
Requests with header `X-Team-Code: <TEAM_CODE>` bypass the limits for internal
doctor-comparison runs.
Limited requests return HTTP `429`, `Retry-After`, and JSON body:
`{"detail":{"message":"...","retry_after_seconds":3600}}`.

## Local Docker Check

```powershell
docker build -t carepath-api .
docker run --rm -p 7860:7860 `
  -e LLM_PROVIDER=ckey `
  -e "LLM_API_KEY=$env:LLM_API_KEY" `
  -e LLM_MODEL=gpt-5.4 `
  -e APP_ENV=prod `
  carepath-api
```

In another terminal:

```powershell
curl.exe http://127.0.0.1:7860/api/v1/health
curl.exe -X POST http://127.0.0.1:7860/api/v1/soap-notes `
  -F "audio=@C:\path\to\demo.wav" `
  -F "encounter_context=Phòng khám nội tổng quát"
```

Expected health signal after startup: `llm_provider` is `ckey` and `asr_ready`
is `true`. The model should already be in the Docker image cache, so startup
warms it without downloading the ONNX files at request time.

## Frontend: Vercel

Import the GitHub repo into Vercel and use these project settings:

```text
Root Directory: apps/web-next
Framework Preset: Next.js
Build Command: npm run build
```

Set these Vercel environment variables:

```text
NEXT_PUBLIC_API_BASE=https://<your-hf-space>.hf.space
NEXT_PUBLIC_SITE_URL=https://<your-vercel-app>.vercel.app
```

`NEXT_PUBLIC_API_BASE` must be the Hugging Face Space origin only, without a
trailing `/api/v1`.

`apps/web-next` is the production frontend. Keep `apps/web/` in the repo for
the legacy same-origin local demo until parity sign-off; do not point Vercel at
`apps/web/`.

## Production Wiring

After Vercel gives the production domain, update the Space secret:

```text
CORS_ORIGINS=https://<your-vercel-app>.vercel.app,http://localhost:3000
```

Do not use `*`; the frontend sends uploads directly to the Space and should be
accepted only from the production Vercel origin and local dev.

Regenerate the landing QR code to point phones at the production tool URL:

```powershell
cd apps\web-next
npx qrcode -t svg -o public\qr-app.svg "https://<your-vercel-app>.vercel.app/app"
```

Commit the regenerated `public/qr-app.svg` after replacing the placeholder
domain with the real Vercel URL.

## Keep-Alive

The workflow in `.github/workflows/keepalive.yml` pings the Space every 12 hours.
Set this GitHub repository variable:

```text
SPACE_URL=https://<your-hf-space>.hf.space
```

Then run **Actions > Keep HF Space Awake > Run workflow** once and confirm the
job succeeds. The scheduled run uses:

```bash
curl -fsS "${SPACE_URL%/}/api/v1/health"
```

## Automated Checks

After both public URLs are live, run:

```powershell
.\scripts\check_goal5_deploy.ps1 `
  -SpaceUrl "https://<your-hf-space>.hf.space" `
  -VercelUrl "https://<your-vercel-app>.vercel.app"
```

It verifies the Vercel landing page, Vercel tool page, Space health, allowed
CORS from the exact Vercel origin, and rejected CORS from a foreign origin.

## Final Smoke

1. Open the public Vercel URL on a phone.
2. Record a short clip on `/app`.
3. Submit it and verify the SOAP note renders.
4. Confirm the browser request goes directly to the Space URL from
   `NEXT_PUBLIC_API_BASE`.
5. Confirm a request from the Vercel origin succeeds and a random foreign origin
   is rejected by CORS.
