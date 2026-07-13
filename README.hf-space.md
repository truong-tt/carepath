---
title: CarePath
sdk: docker
app_port: 7860
---

# CarePath Space

This Space runs the unified CarePath product from the root `Dockerfile`, which
builds `scribe/frontend/` and `interpreter/frontend/`:
demo site at `/`, Scribe tool at `/ghi-chep-lam-sang/`, scriber API at
`/api/v1/*`, and Interpreter API at `/api/*` + `/ws/*`. Interpreter browser
paths are disabled for public users while that module remains in development.

Required Space secrets (scriber; the interpreter runs keyless in mock mode):

- `LLM_PROVIDER=ckey`
- `LLM_API_KEY=<your CKey key>`
- `LLM_MODEL=gpt-5.4`
- `TEAM_CODE=<shared internal bypass code>`
- `APP_ENV=prod`
