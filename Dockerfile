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
RUN python -m pip install --upgrade pip \
    && python -m pip install .

ARG GIPFORMER_QUANTIZE=int8
ENV GIPFORMER_QUANTIZE=${GIPFORMER_QUANTIZE}
RUN python -c "from carepath.services.asr import GipformerASR; from huggingface_hub import hf_hub_download; files = GipformerASR.onnx_files['${GIPFORMER_QUANTIZE}']; [hf_hub_download(repo_id=GipformerASR.repo_id, filename=name) for name in (*files.values(), 'tokens.txt')]"

COPY data ./data

EXPOSE 7860

CMD ["uvicorn", "carepath.main:app", "--app-dir", "apps/api", "--host", "0.0.0.0", "--port", "7860"]
