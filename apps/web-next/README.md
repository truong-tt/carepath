# CarePath web (Next.js)

Next.js port of `apps/web/` (landing `/` + tool `/app`) for the free-demo deployment
(Vercel frontend + Hugging Face Space API). Plan: `docs/demo-deploy-plan.md`.

## Dev

```bash
npm install
npm run dev        # http://localhost:3000
```

`NEXT_PUBLIC_API_BASE` — base URL of the CarePath API (the HF Space).
Empty/unset ⇒ relative paths, so local dev against same-origin uvicorn still works.
For split local dev create `.env.local`:

```
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

(then the API needs `CORS_ORIGINS=http://localhost:3000`.)

## Build

```bash
npm run build && npm run start
```

## Production

Vercel project settings:

- Root Directory: `apps/web-next`
- Framework Preset: Next.js
- Build Command: `npm run build`
- Environment Variables:
  - `NEXT_PUBLIC_API_BASE=https://<your-hf-space>.hf.space`
  - `NEXT_PUBLIC_SITE_URL=https://<your-vercel-app>.vercel.app`

The HF Space must set `CORS_ORIGINS` to the exact Vercel production origin
plus local dev if needed, for example:

```text
https://<your-vercel-app>.vercel.app,http://localhost:3000
```

## QR asset

`public/qr-app.svg` points desktop visitors at the tool page on their phone.
Regenerate it after the final Vercel domain is known:

```bash
npx qrcode -t svg -o public/qr-app.svg "https://<prod-domain>/app"
```

## Notes

- CSS is copied verbatim from `apps/web/` (`app/css/styles.css`, `app/css/landing.css`)
  for pixel parity; web-next-only additions live in clearly marked blocks at the end of
  `landing.css` and in `app/app/tool.css`. No Tailwind — the existing hand-written CSS
  is the design system, rewriting it would only risk fidelity.
- Fonts + logo live in `public/assets/` (copied from `apps/web/assets/`).
- Recording uses native `MediaRecorder`; blobs are named by real mimeType
  (`recording.webm` Android / `recording.m4a` iOS) so the server suffix check passes.
