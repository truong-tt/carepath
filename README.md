# CarePath

CarePath is a backend-first MVP for Vietnamese medical staff:

1. Upload an audio clip.
2. Transcribe it with Gipformer ONNX ASR.
3. Correct ASR/code-switching errors with retrieval-assisted GEC.
4. Generate a draft Vietnamese SOAP note for clinician review.

The MVP is intentionally designed so demo success does not depend on a trained GEC model. Training is a gated upgrade path: the trained model must beat raw Gipformer and the LLM/RAG baseline before it is used in the app.

## Project Shape

- `apps/api/carepath`: FastAPI runtime backend (ASR + retrieval + LLM serving).
- `apps/api/carepath/gec`: standalone, paper-faithful DARAG post-ASR correction
  package (training/data/eval only — never imported by the serving path).
- `data/medical_lexicon.json`: editable Vietnamese/English medical lexicon seed.
- `scripts/gec/`: thin CLI entrypoints over `carepath.gec` (datastore, pairs,
  synthetic, voice-cloning TTS, leakage, train, predict, evaluate, gate).
- `apps/web`: vanilla static frontend (landing + SOAP-note tool), served by the API.
- `notebooks/CarePath_DARAG_dataprep_cpu.ipynb` + `CarePath_DARAG_train_gpu.ipynb`:
  the rebuilt two-stage Colab pipeline.
- `tests`: dependency-light unit tests (`tests/test_gec.py` covers the GEC package).

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
uvicorn carepath.main:app --app-dir apps/api --reload --host 127.0.0.1 --port 8000
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

## Demo Preflight

Run this once **before** a live demo. Unlike the smoke test, it uses your real
`.env`, so it validates the actual demo path: it warms up Gipformer (downloads
and loads the ONNX model so the first real request is not slow), probes the live
LLM connection, and runs a full end-to-end round-trip.

```powershell
.\.venv\Scripts\python.exe scripts\preflight.py
```

Options:

- `--skip-asr` skips the model download/warmup.
- `--no-llm-probe` skips the live LLM call.

A failed LLM probe is only a warning because the offline fallback keeps the demo
serving notes; ASR warmup or round-trip failures exit non-zero.

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

Uploads must be an audio file (`wav`, `mp3`, `m4a`, `aac`, `flac`, `ogg`, `oga`,
`opus`, `webm`) and at most 25 MB; otherwise the API returns `400` immediately.

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

- `LLM_FALLBACK_OFFLINE=true` (default): if a network LLM provider (ckey /
  openai_compatible) fails or times out, the request is served by the offline
  generator instead of erroring. The response metadata reports `gec_mode` and
  `soap_mode` as `offline_fallback` so the degraded path stays visible. Set to
  `false` to fail hard instead.

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

Gipformer is run in segments to avoid ONNX memory spikes on long WAV files.
`GIPFORMER_SEGMENTATION` controls how the audio is split:

- `overlap` (default): overlapping windows of `GIPFORMER_CHUNK_SECONDS` with a
  `GIPFORMER_OVERLAP_SECONDS` (default 2 s) overlap. Adjacent transcripts are
  merged with seam de-duplication, so a word cut at one boundary is recovered
  whole in the neighbor instead of being split (e.g. `dihydro` + `testosterone`).
  No extra model.
- `vad`: split on silence using a silero VAD so cuts land in pauses, never
  mid-word. Set `GIPFORMER_VAD_MODEL` to `repo_id:filename` (a `silero_vad.onnx`)
  or a local path. If the VAD model/deps are unavailable it degrades to `overlap`.
- `fixed`: legacy non-overlapping windows.

```text
GIPFORMER_CHUNK_SECONDS=20
GIPFORMER_SEGMENTATION=overlap
GIPFORMER_OVERLAP_SECONDS=2
```

Lower `GIPFORMER_CHUNK_SECONDS` if a machine still runs out of memory; raise it
only after testing with the real demo clip. ASR metadata reports the
`segmentation` mode used and the `segment_count`.

## Post-ASR Correction (DARAG)

The post-ASR corrector is a standalone, paper-faithful re-implementation of
**DARAG** (Ghosh et al., *Failing Forward: Improving Generative Error Correction
for ASR with Synthetic Data and Retrieval Augmentation*, Findings of ACL 2025),
adapted to Vietnamese code-switched medical speech. It lives in
`apps/api/carepath/gec` with thin CLIs in `scripts/gec/`. It is the **offline
training/data/eval layer** and never imports the FastAPI serving path, so deleting
or retraining it cannot break the live app.

What the paper contributes, and where it lives here:

- **Synthetic data augmentation** (paper §4.1): few-shot LLM transcript generation
  (`gec/synthetic.py`) → **voice-cloning TTS** conditioned on in-domain reference
  speech (`gec/tts.py`, paper §4.1 Step 2 / Appendix D) → Gipformer over the cloned
  audio (`gec/data.py`).
- **Retrieval-Augmented Correction** (paper §4.2, Eq. 1): an NE / code-switch
  datastore (`gec/datastore.py`) + bi-encoder cosine top-k retrieval
  (`gec/retrieval.py`).
- **Leakage audit** (paper App. C / Table 6): SentenceBERT cosine + BLEU of
  synthetic vs nearest real transcript (`gec/leakage.py`).
- **QLoRA fine-tune with ablation variants** (paper §5): `full`, `wo_rac`,
  `wo_aug`, `only_synth` (`gec/train.py`).
- **WER + NE-F1 tables and the acceptance gate** (paper Tables 3 & 4):
  `gec/evaluate.py`, `gec/gate.py`.

Do not train directly on clean ViMedCSS text — first create GEC pairs
(`Gipformer ASR hypothesis -> ViMedCSS gold segment_text`), then compare:

1. Raw Gipformer (`raw_asr`).
2. LLM/RAG correction (`corrected_text`, from `scripts/gec/llm_rag_baseline.py`).
3. Trained QLoRA DARAG adapter (`gec_pred`, from `scripts/gec/predict.py`).

```powershell
# Run the trained adapter over the LLM/RAG output so one file has every column
python scripts/gec/predict.py `
  --pairs artifacts/evaluations/llm_rag.jsonl `
  --adapter-dir artifacts/gec_lora/qwen3/full `
  --output artifacts/evaluations/darag_all_preds.jsonl

# Score raw vs LLM/RAG vs trained (WER table + NE-F1 ablation table), then gate
python scripts/gec/evaluate.py `
  --input artifacts/evaluations/darag_all_preds.jsonl `
  --prediction-columns raw_asr corrected_text gec_pred `
  --wer-output artifacts/evaluations/darag_wer.json `
  --ne-f1-output artifacts/evaluations/darag_ne_f1.json

python scripts/gec/gate.py --report artifacts/evaluations/darag_wer.json
```

The trained adapter is accepted only when `scripts/gec/gate.py` exits `ACCEPT` — on
the frozen `validation` and `hard` splits it matches or beats raw Gipformer and the
LLM/RAG baseline on WER and code-switched term F1 without regressing number/unit
preservation.

### Retrieval backend (code-switch terms)

Retrieval defaults to the lexical/fuzzy matcher. The runtime serving path selects
its retriever with `RETRIEVAL_BACKEND` (`lexical` / `semantic` / `hybrid`); the
`semantic` / `hybrid` modes use the Vietnamese bi-encoder
(`bkai-foundation-models/vietnamese-bi-encoder`) and need the optional
`sentence-transformers` + `pyvi` deps.

The offline DARAG pair builders take a matching `--retrieval-backend` flag so the
NEs stored in training pairs use the same retriever you plan to serve with:

```powershell
python scripts/gec/make_pairs.py --asr-provider mock --limit-per-split 20 `
  --datastore artifacts/retrieval/term_datastore_smoke.json `
  --retrieval-backend hybrid `
  --output artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl
```

## DARAG Pipeline (CLIs)

CKey is reserved for runtime correction, SOAP generation, and optional high-quality
baseline calls. Synthetic transcript generation uses open-weight HF models,
defaulting to `Qwen/Qwen3-4B-Instruct-2507`. Run with `PYTHONPATH=apps/api` (the
CLIs also set it themselves).

Data prep (CPU — real Gipformer pairs are the long step):

```powershell
python scripts/gec/build_datastore.py `
  --dataset tensorxt/ViMedCSS --limit-per-split 20 `
  --output artifacts/retrieval/term_datastore_smoke.json

python scripts/gec/make_pairs.py `
  --output artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl `
  --limit-per-split 20 `
  --datastore artifacts/retrieval/term_datastore_smoke.json --resume

# Baseline WER + LLM/RAG baseline (+GEC column)
python scripts/gec/evaluate.py `
  --input artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl `
  --prediction-columns raw_asr

python scripts/gec/llm_rag_baseline.py `
  --input artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl `
  --output artifacts/evaluations/llm_rag_smoke.jsonl --limit 20
```

Synthetic augmentation (GPU for generation/TTS/train):

```bash
python scripts/gec/gen_synthetic.py \
  --pairs artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl \
  --output artifacts/synthetic/synthetic_clean_smoke.jsonl --count 50 --load-in-4bit

# Voice-cloning TTS (paper §4.1 Step 2). --provider mms is the no-clone fallback.
python scripts/gec/voice_clone_tts.py \
  --input artifacts/synthetic/synthetic_clean_smoke.jsonl \
  --output artifacts/synthetic/synthetic_audio_manifest_smoke.jsonl \
  --provider xtts --ref-dataset tensorxt/ViMedCSS --ref-count 20 --limit 10 --resume

python scripts/gec/make_synth_pairs.py \
  --input artifacts/synthetic/synthetic_audio_manifest_smoke.jsonl \
  --output artifacts/gec_pairs/darag_synthetic_pairs_smoke.jsonl \
  --datastore artifacts/retrieval/term_datastore_smoke.json --limit 10 --resume

# Leakage audit (paper Table 6): synthetic must be in-domain but not memorized.
python scripts/gec/check_leakage.py \
  --synthetic artifacts/synthetic/synthetic_clean_smoke.jsonl \
  --real artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl \
  --output artifacts/evaluations/leakage_smoke.json
```

Augment + train (full run plus the paper's ablations) + gate:

```bash
python scripts/gec/augment.py \
  --real artifacts/gec_pairs/vimedcss_gipformer_pairs_smoke.jsonl \
  --synthetic artifacts/gec_pairs/darag_synthetic_pairs_smoke.jsonl \
  --output artifacts/gec_pairs/darag_augmented_smoke.jsonl

# --all-variants trains full / wo_rac / wo_aug / only_synth into <dir>/<variant>.
python scripts/gec/train.py \
  --pairs artifacts/gec_pairs/darag_augmented_smoke.jsonl \
  --output-dir artifacts/gec_lora/qwen3 --all-variants --max-steps 60
```

## Colab Training

Two notebooks split the work to save GPU units — the slow Gipformer ASR data prep
is CPU-only, so running it on an L4 wastes units:

- `notebooks/CarePath_DARAG_dataprep_cpu.ipynb` — **CPU runtime**: builds the NE
  datastore + real Gipformer GEC pairs (the long step) and saves artifacts to
  Google Drive (`MyDrive/carepath_artifacts`).
- `notebooks/CarePath_DARAG_train_gpu.ipynb` — **L4/GPU runtime**: restores the
  artifacts from Drive, then runs the GPU work — synthetic generation,
  voice-cloning TTS, QLoRA fine-tune (full + ablations), prediction — plus the
  leakage report, WER/NE-F1 tables, and acceptance gate.

Each notebook's run-size cell (`LIMIT_PER_SPLIT`, `SYNTH_COUNT`, `SYNTH_TTS_LIMIT`,
`NSYN_FACTOR`, `MAX_STEPS`) keeps smoke defaults; raise them for a real run.
Defaults:

- GEC model: `Qwen/Qwen3-4B-Instruct-2507` (OOM fallback `Qwen/Qwen2.5-3B-Instruct`)
- Quantization: 4-bit QLoRA, LoRA adapters only (paper §4.3)
- TTS: `capleaf/viXTTS` voice cloning (fallback `facebook/mms-tts-vie`, no clone)
- Dataset: `tensorxt/ViMedCSS`, with frozen train/validation/test/hard splits

> The paper fine-tunes LLaMA-2-7B (English); CarePath defaults to multilingual
> Qwen3 for Vietnamese and uses `hard` as the in-corpus OOD split. These are
> deliberate, documented ports — see `apps/api/carepath/gec/config.py`.

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
