# HopeGait

HopeGait is a backend-first MVP for Vietnamese medical staff:

1. Upload an audio clip.
2. Transcribe it with Gipformer ONNX ASR.
3. Correct ASR/code-switching errors with retrieval-assisted GEC.
4. Generate a draft Vietnamese SOAP note for clinician review.

The MVP is intentionally designed so demo success does not depend on a trained GEC model. Training is a gated upgrade path: the trained model must beat raw Gipformer and the LLM/RAG baseline before it is used in the app.

## Project Shape

- `apps/api/hopegait`: FastAPI runtime backend.
- `data/medical_lexicon.json`: editable Vietnamese/English medical lexicon seed.
- `scripts/create_gec_pairs.py`: Colab-friendly ViMedCSS to `raw_asr -> gold_text` data creation.
- `scripts/evaluate_corrections.py`: baseline metric reporting.
- `notebooks/HopeGait_GEC_Colab.ipynb`: training/evaluation notebook skeleton.
- `tests`: dependency-light unit tests.

## Python Version

Use Python 3.11, 3.12, or 3.13. Gipformer declares Python 3.9-3.13 support; this project blocks Python 3.14 in `pyproject.toml` to avoid unsupported ML wheels.

## Local API Setup

Recommended first run:

```powershell
.\scripts\setup_local.ps1
.\scripts\run_api.ps1
```

The setup script requires Python 3.11-3.13 and defaults to `py -3.12`.
If Python 3.12 is installed at a custom path:

```powershell
.\scripts\setup_local.ps1 -Python "C:\Path\To\python.exe"
```

Manual equivalent:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.local.example .env
python scripts/smoke_backend.py
uvicorn hopegait.main:app --app-dir apps/api --reload --host 127.0.0.1 --port 8000
```

If your machine only has the Windows Store `python.exe`, install Python 3.12 first.

## First Backend Smoke Test

Run this before testing real audio:

```powershell
python scripts/smoke_backend.py
```

The smoke test forces `ASR_PROVIDER=mock`, `ALLOW_MOCK_ASR=true`, and
`LLM_PROVIDER=offline` for that process. It validates:

1. `GET /api/v1/health`
2. `POST /api/v1/corrections`
3. `POST /api/v1/soap-notes` with a generated WAV file

Do not debug Gipformer until this smoke test passes.

## Enabling Real Gipformer ASR

After the mock/offline backend passes:

```powershell
Copy-Item .env.example .env -Force
.\scripts\run_api.ps1
```

The first real ASR request downloads Gipformer ONNX artifacts from Hugging Face.

Verify the running API with a generated WAV:

```powershell
python scripts/smoke_real_asr.py --timeout 300
```

To test a real demo clip:

```powershell
python scripts/smoke_real_asr.py --audio C:\path\to\demo.wav --timeout 300
```

## Demo API

Health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

Audio to SOAP:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/soap-notes `
  -F "audio=@C:\path\to\demo.wav" `
  -F "encounter_context=Phòng khám nội tổng quát"
```

Correction-only debugging:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/corrections `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"raw_transcript":"bệnh nhân đau ngực spo2 chín mươi tám phần trăm"}'
```

## Runtime Modes

- `ASR_PROVIDER=gipformer`: real Gipformer ONNX inference.
- `ASR_PROVIDER=mock` and `ALLOW_MOCK_ASR=true`: frontend/debug fallback only.
- `LLM_PROVIDER=offline`: deterministic local fallback for development.
- `LLM_PROVIDER=ckey`: CKey OpenAI-compatible `/v1/chat/completions` provider.
- `LLM_PROVIDER=openai_compatible`: calls `/chat/completions` at `LLM_BASE_URL`.

The API always sets `review_required: true` because the SOAP note is a draft clinical document.

## Enabling CKey LLM

CKey's setup guide uses the OpenAI-compatible API with:

- Base URL: `https://api.xah.io/v1`
- Route: `/chat/completions`
- API key format: `sk-...`
- Example model: `gpt-5.4`

Configure local `.env`:

```powershell
Copy-Item .env.ckey.example .env -Force
notepad .env
```

Set `LLM_API_KEY` to your CKey key, then restart the API:

```powershell
.\scripts\run_api.ps1
```

Verify CKey through the running backend:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_llm.py --timeout 120
```

Keep `LLM_PROVIDER=ckey`, `LLM_BASE_URL=https://api.xah.io/v1`, and
`LLM_MODEL=gpt-5.4` unless the CKey pricing page shows a different active model
you want to test.

## Long Audio Clips

Gipformer is run in chunks to avoid ONNX memory spikes on long WAV files.
The default chunk size is:

```text
GIPFORMER_CHUNK_SECONDS=20
```

Lower this value if a machine still runs out of memory; raise it only after
testing with the real demo clip.

## GEC Methodology

Do not train directly on clean ViMedCSS text. First create GEC pairs:

```text
Gipformer ASR hypothesis -> ViMedCSS gold segment_text
```

Then compare:

1. Raw Gipformer.
2. LLM/RAG correction.
3. Trained QLoRA GEC model.

The trained GEC model is accepted only if validation and hard split metrics improve, especially code-switched term recall/F1 and number/unit preservation.

## DARAG Pipeline

CKey is reserved for runtime correction, SOAP generation, and optional high-quality
baseline calls. Synthetic transcript generation for DARAG uses open-weight HF
models in Colab, defaulting to `Qwen/Qwen3-4B-Instruct-2507`.

Small-goal sequence:

```powershell
python scripts/build_term_datastore.py `
  --dataset tensorxt/ViMedCSS `
  --limit-per-split 20 `
  --output artifacts/retrieval/term_datastore_smoke.json

python scripts/create_gec_pairs.py `
  --output artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl `
  --limit-per-split 20 `
  --lexicon artifacts/retrieval/term_datastore_smoke.json `
  --resume

python scripts/evaluate_corrections.py `
  --input artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl `
  --prediction-column raw_asr

python scripts/run_llm_rag_baseline.py `
  --input artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl `
  --output artifacts/evaluations/ckey_rag_smoke.jsonl `
  --limit 20

python scripts/evaluate_gec_runs.py `
  --input artifacts/evaluations/ckey_rag_smoke.jsonl `
  --prediction-columns raw_asr corrected_text
```

Colab synthetic data sequence:

```bash
PYTHONPATH=apps/api python scripts/generate_synthetic_transcripts.py \
  --pairs artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl \
  --output artifacts/synthetic/synthetic_clean_smoke.jsonl \
  --model Qwen/Qwen3-4B-Instruct-2507 \
  --count 50 \
  --load-in-4bit

PYTHONPATH=apps/api python scripts/synthesize_speech.py \
  --input artifacts/synthetic/synthetic_clean_smoke.jsonl \
  --output artifacts/synthetic/synthetic_audio_manifest_smoke.jsonl \
  --limit 10 \
  --resume

PYTHONPATH=apps/api python scripts/create_synthetic_gec_pairs.py \
  --input artifacts/synthetic/synthetic_audio_manifest_smoke.jsonl \
  --output artifacts/gec_pairs/darag_synthetic_pairs_smoke.jsonl \
  --limit 10 \
  --resume
```

If TTS fails, use `scripts/create_text_noise_ablation.py` only as a labeled
ablation. It mines substitutions from real Gipformer pairs and must not be
reported as full DARAG.

## Colab Training

Open `notebooks/CarePath_DARAG_Colab.ipynb` in Google Colab. It defaults to:

- Model: `Qwen/Qwen3-4B-Instruct-2507`
- OOM fallback: `Qwen/Qwen2.5-3B-Instruct`
- Quantization: 4-bit QLoRA
- Dataset: `tensorxt/ViMedCSS`

The notebook is structured to produce metrics before training and to keep train/validation/test/hard splits frozen.

Colab must be able to see this repository before running the pipeline cells.
The setup cell supports three options:

1. Upload `carepath.zip` to `/content/carepath.zip` with the Colab Files sidebar,
   then rerun the setup cell.
2. Set `CAREPATH_REPO_ZIP` to a zip path in `/content` or Google Drive.
3. Set `CAREPATH_REPO_URL` to a Git URL and let the setup cell clone it.

On Windows, create the zip with:

```powershell
Compress-Archive -Path C:\Users\ADMIN\carepath\* -DestinationPath C:\Users\ADMIN\Downloads\carepath.zip -Force
```
