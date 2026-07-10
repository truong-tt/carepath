# --- Stage 1: build the static frontends (demo site + interpreter console) ---
FROM node:22-slim AS frontends

WORKDIR /build

COPY site/package.json site/package-lock.json site/
RUN cd site && npm ci
COPY site site
# site build also runs the Vietnamese diacritics gate.
RUN cd site && npm run build

COPY frontend/package.json frontend/package-lock.json frontend/
RUN cd frontend && npm ci
COPY frontend frontend
# Production build uses base /console/ (see frontend/vite.config.ts).
RUN cd frontend && npm run build

# --- Stage 2: Python runtime serving both APIs and the built frontends ---
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf-cache

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates libgomp1 libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY apps/api ./apps/api
COPY backend ./backend
RUN python -m pip install --upgrade pip \
    && python -m pip install . ./backend

ARG GIPFORMER_QUANTIZE=int8
ENV GIPFORMER_QUANTIZE=${GIPFORMER_QUANTIZE}
RUN python -c "from carepath.services.asr import GipformerASR; from huggingface_hub import hf_hub_download; files = GipformerASR.onnx_files['${GIPFORMER_QUANTIZE}']; [hf_hub_download(repo_id=GipformerASR.repo_id, filename=name) for name in (*files.values(), 'tokens.txt')]"

COPY data ./data
COPY --from=frontends /build/site/dist ./site/dist
COPY --from=frontends /build/frontend/dist ./frontend/dist
ENV SITE_DIST_DIR=/app/site/dist \
    CONSOLE_DIST_DIR=/app/frontend/dist

EXPOSE 7860

CMD ["uvicorn", "carepath.main:app", "--app-dir", "apps/api", "--host", "0.0.0.0", "--port", "7860"]
