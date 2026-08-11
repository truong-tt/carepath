---
title: CarePath
sdk: docker
app_port: 7860
---

# CarePath Space

This Space runs the unified CarePath product from the root `Dockerfile`, which
builds one frontend (`scribe/frontend/`) and serves:

- `/` — the public landing page
- `/kham-song-ngu/` — the bilingual visit: two-way interpretation, document
  reading, and the clinician confirmation gate
- `/ghi-chep-lam-sang/` — the Scribe tool
- `/api/v1/*` — Scribe API, including the visit bridge, document reading and
  Vietnamese speech
- `/api/*` and `/ws/*` — Interpreter API

`/phien-dich-y-khoa/` and `/console/` are explicit 404s: the separate
interpreter console was removed once `/kham-song-ngu/` replaced it.

## Required Space secrets

Scribe:

- `LLM_PROVIDER=ckey`
- `LLM_API_KEY=<your CKey key>`
- `LLM_MODEL=gpt-5.4`
- `TEAM_CODE=<shared internal bypass code>`
- `APP_ENV=prod`

Interpreter — one variable, **required for `/kham-song-ngu/` to translate**.
Without it the module stays in mock mode and returns `[vi->en] …` echoes, which
look like a broken product to a visitor. It reuses the `LLM_*` secrets above,
so nothing else is needed:

- `PROVIDER_MODE=ckey`

Measured ckey latency across 50 turns: median 15s, p90 54s, max 206s. That is
a gateway limit, not an architectural one, but it is what a live visitor will
experience.

Vietnamese text-to-speech is optional. The model is not baked into the image,
so `/api/v1/speech` returns 503 and the browser voice is used instead.
