# CarePath DARAG notebooks

Four notebooks, grouped by **runtime tier** so one notebook runs on one Colab
runtime and CPU work never burns GPU units. Each is thin — it bootstraps the repo,
installs deps, and calls `scripts/gec/*` steps; all real logic lives in
`apps/api/carepath/gec/`. The notebooks are **generated**: edit
`scripts/gec/build_notebooks.py` and run `python scripts/gec/build_notebooks.py`
to rebuild them (don't hand-edit the `NN_*.ipynb` files).

## Profile

The bootstrap cell sets `PROFILE = 'smoke'`. Change it to `'full'` for the real
ViMedCSS run. The profile (`carepath/gec/profiles.py`) fixes every run-size:
`smoke` = mock ASR, tiny limits, 1 seed (plumbing check); `full` = Gipformer,
N=5 N-best, nsyn=n, 3 seeds, all ablation variants (paper §5).

## Order

Run in order, each on the runtime it names:

| # | Notebook | Runtime | Merges (paper) | What it does |
|---|----------|---------|----------------|--------------|
| 00 | data_prep | CPU | §4.2.1, Table 5 | datastore + labeled pairs (text-only, minutes) |
| 01 | asr_synthesis | GPU (L4) | §3.1/§3.2, §4.1, App. C/Table 6 | real ASR pairs (+N-best, error-signal) → synth transcripts → viXTTS → synth pairs → leakage |
| 02 | train_predict | GPU (A100) | §4.2, §5 | harvest confusions + augment + multi-seed QLoRA + predict |
| 03 | evaluate_export | CPU | Tables 3 & 4, deploy | WER/NE-F1 + gate + serve bundle |

Why ASR pairs sit on the GPU notebook: the full run decodes each clip 6× (best +
5 perturbation N-best) over ~150 h of ViMedCSS audio. On a 2-vCPU Colab CPU
runtime that is weeks of wall time; with the CUDA sherpa-onnx build on an L4
(installed by the notebook, `GIPFORMER_PROVIDER=cuda`, all 6 decodes batched into
one `decode_streams` call) it is hours. If the CUDA wheel install fails,
onnxruntime falls back to CPU with a warning — slower, never broken.

Each step restores its inputs from Drive (Colab) or disk (local) and saves its
outputs, and every step `--resume`s — so a disconnect re-enters the notebook and
skips finished work (resume is per-step, not per-notebook). The runtime plan is
printed at the top of `00_data_prep`.

`02_train_predict` first **harvests real ASR confusions** into the datastore (paper
§4.2, Limitation #1): it aligns every `gold↔raw_asr` pair, learns how Gipformer
actually mangles each term ("reductase" → "REDO TAY"), stores those as aliases, and
refreshes each pair's retrieved NEs — no hand-built phonetic table.

`03_evaluate_export` packages the gated `full` adapter + enriched datastore + frozen
DARAG prompt into a portable `serve_manifest.json` bundle. The FastAPI backend
serves it in-process with `LLM_PROVIDER=gec_local GEC_BUNDLE_PATH=<bundle>`
(`carepath.services.gec_local`), with RAC retrieval and a clinical safety gate that
falls back to the offline corrector on bad output. Qwen3-4B 4-bit needs CUDA at
serve time; on a CPU-only box use the network LLM provider instead.

## One-command alternative

`python scripts/gec/run_pipeline.py --profile {smoke,full} --stage {all,data,synth,train,eval}`
runs the same steps headless (CI / local box).

`legacy/` holds the previous two mega-notebooks, kept for reference.

## Future iterations (deferred, not lost)

Grounded next steps, roughly in value order:

- **Cross-model N-best (biggest paper lever, §3.2-iii).** N-best is currently
  single-model Gipformer acoustic perturbations. Adding a second ASR (PhoWhisper,
  VinAI) gives genuinely diverse errors — the paper's strongest GEC signal. Excluded
  for now by the self-contained choice.
- **VietMed as true cross-corpus OOD.** ViMedCSS "hard" is in-corpus; VietMed
  (LREC-2024 medical ASR) would give real OOD eval + real-data augmentation (paper
  Table 5, "real beats synthetic").
- **Harvest tuning.** On the `full` run, raise `harvest_aliases.py --min-count` to 2+
  to drop one-off confusion noise; if NE recall still stalls, add a phoneme-aware
  retrieval channel (PARCO / PMF-CEC style) on top of the harvested aliases.
- **gold_terms spelling.** Annotations mix `testosteron`/`testosterone`; normalize the
  NE keys so retrieval/F1 are not penalized by a final-`e`.
- **ITN for bedside vitals.** Dropped for ViMedCSS (lecture content, no decimals/%).
  When clinical-vitals data lands, add spoken→written ITN, decimal separator = **comma**
  (Vietnamese convention).
- **Serving scale.** `gec_local` loads Qwen3-4B 4-bit in-process (needs CUDA). Options:
  a `--merge` weights flag in `export_serve.py` for faster cold-load, or a GEC
  microservice (vLLM/TGI) if the serve box has no GPU.
