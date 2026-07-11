# CarePath public site

Static, Vietnamese-first buyer site for the two CarePath products. The embedded
Interpreter experience is a scripted client-only simulation. The Scribe route
at `/#/scribe` uploads a user-selected audio file to `VITE_API_BASE`; its
Interpreter link uses `VITE_CONSOLE_URL`; it includes the selected `lang` when
that URL crosses origins.

```powershell
npm.cmd install
npm.cmd run dev
npm.cmd run lint
npm.cmd test
npm.cmd run build
npm.cmd run e2e
npm.cmd run lighthouse
```

Normal builds allow same-origin API fallbacks for the combined FastAPI service.
The Vercel build validates that both Space URLs are configured and use one
HTTPS origin.

The generated identity board is stored in `brand/`; production identity assets
live in `src/assets/`.
