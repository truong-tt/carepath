---
title: CarePath API
sdk: docker
app_port: 7860
---

# CarePath API Space

This Space runs the CarePath FastAPI backend from the root `Dockerfile`.

Required Space secrets:

- `LLM_PROVIDER=ckey`
- `LLM_API_KEY=<your CKey key>`
- `LLM_MODEL=gpt-5.4`
- `CORS_ORIGINS=<your Vercel URL>`
- `TEAM_CODE=<shared internal bypass code>`
- `APP_ENV=prod`
