# CarePath DARAG notebooks

One stage per notebook. Each is thin — it bootstraps the repo, installs deps, and
calls one `scripts/gec/*` step. All real logic lives in `apps/api/carepath/gec/`.
The notebooks are **generated**: edit `scripts/gec/build_notebooks.py` and run
`python scripts/gec/build_notebooks.py` to rebuild them (don't hand-edit the
`NN_*.ipynb` files).

## Profile

The bootstrap cell sets `PROFILE = 'smoke'`. Change it to `'full'` for the real
ViMedCSS run. The profile (`carepath/gec/profiles.py`) fixes every run-size:
`smoke` = mock ASR, tiny limits, 1 seed (plumbing check); `full` = Gipformer,
N=5 N-best, nsyn=n, 3 seeds, all ablation variants (paper §5).

## Order

| # | Notebook | Runtime | Paper |
|---|----------|---------|-------|
| 00 | setup_and_config | CPU | — |
| 01 | build_datastore | CPU | §4.2 Step 1 |
| 02 | asr_pairs (+ N-best + error-signal) | CPU | §3.1 / §3.2 |
| 03 | labeled_pairs (supplementary real) | CPU | Table 5 |
| 04 | synth_transcripts | GPU-light | §4.1 Step 1 |
| 05 | voice_clone_tts | GPU | §4.1 Step 2 |
| 06 | synth_pairs (+ N-best) | CPU/GPU | §4.1 Step 3 |
| 07 | leakage_report | GPU-light | App. C / Table 6 |
| 08 | augment_and_train (multi-seed) | GPU | §5 |
| 09 | predict | GPU | — |
| 10 | evaluate_and_gate | CPU | Tables 3 & 4 |

Each stage restores its inputs from Drive (Colab) or disk (local) and saves its
outputs, so stages run independently and resume after a disconnect. CPU stages
(00–03, 10) run on a Colab **CPU** runtime to save GPU units. The trained adapter
stays on Drive (`carepath_artifacts/gec_lora/...`); a second trainer picks it up
via the shared Drive folder (see the handoff below) — there is no separate
inference/bundle notebook because every consumer is a trainer with the repo.

## One-command alternative

`python scripts/gec/run_pipeline.py --profile {smoke,full} --stage {all,data,synth,train,eval}`
runs the same steps headless (CI / local box).

`legacy/` holds the previous two mega-notebooks, kept for reference.
