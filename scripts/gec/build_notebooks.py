"""Generate the per-stage DARAG notebooks from one spec (run me to (re)build them).

Notebooks are kept thin and *generated* so they never drift: all logic lives in
``carepath.gec`` + ``scripts/gec/*`` and each notebook just bootstraps, installs,
and calls one stage. Edit the spec here, run ``python scripts/gec/build_notebooks.py``,
and the ``notebooks/NN_*.ipynb`` files are rewritten.
"""

from __future__ import annotations

import json
from pathlib import Path

NOTEBOOKS_DIR = Path(__file__).resolve().parents[2] / "notebooks"

# Minimal, self-contained repo bootstrap: can't import carepath until sys.path is
# set, so this cell locates-or-clones the repo before any package import.
BOOTSTRAP = """\
# --- CarePath stage bootstrap (short by design) ---
import importlib.util, os, shutil, subprocess, sys
from pathlib import Path

def _find(start):
    for d in [start, *start.parents]:
        if (d / 'pyproject.toml').exists() and (d / 'apps' / 'api' / 'carepath').exists():
            return d
    return None

def _token():
    # Colab Secrets live in userdata, NOT os.environ - check both.
    for key in ('CAREPATH_GITHUB_TOKEN', 'GITHUB_TOKEN'):
        if os.environ.get(key):
            return os.environ[key]
    try:
        from google.colab import userdata
        for key in ('CAREPATH_GITHUB_TOKEN', 'GITHUB_TOKEN'):
            try:
                val = userdata.get(key)
                if val:
                    return val
            except Exception:
                pass
    except Exception:
        pass
    return None

REPO = _find(Path.cwd().resolve())
if REPO is None and importlib.util.find_spec('google.colab'):
    target = Path('/content/carepath')
    if _find(target):                       # already cloned in this runtime
        REPO = target
    else:
        if target.exists():
            shutil.rmtree(target)           # remove a half-cloned leftover
        url = os.environ.get('CAREPATH_REPO_URL', 'https://github.com/truong-tt/carepath.git')
        tok = _token()
        if tok and url.startswith('https://github.com/'):
            url = url.replace('https://', f'https://x-access-token:{tok}@')
        r = subprocess.run(['git', 'clone', url, str(target)], capture_output=True, text=True)
        if r.returncode != 0:
            err = (r.stderr or r.stdout)
            if tok:
                err = err.replace(tok, '***')
            raise SystemExit(
                'git clone failed. This repo is private — add a Colab Secret named '
                'GITHUB_TOKEN (key icon in the left sidebar, toggle "Notebook access") '
                'holding a GitHub token with read access to the repo, then re-run.\\n\\n' + err)
        REPO = target
assert REPO, 'Open this notebook from inside the CarePath repo.'
os.chdir(REPO); sys.path.insert(0, str(REPO / 'apps' / 'api'))

PROFILE = os.environ.get('CAREPATH_PROFILE', 'full')  # default full; set CAREPATH_PROFILE=smoke for a plumbing-only check
from carepath.gec.notebook import init_stage
CTX = init_stage(PROFILE); P = CTX.paths; PROF = CTX.profile
"""

INSTALL = """\
# Install the GEC training stack (idempotent; needed once per Colab runtime).
import subprocess, sys
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-e', '.[training]'])
"""

INSTALL_TTS = INSTALL + """subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'coqui-tts'])
"""

# GPU notebook: also swap in the CUDA build of sherpa-onnx so the bulk ASR decode
# (6 decodes per clip with N-best) runs on the GPU. Colab GPU runtimes are
# CUDA 12 / cuDNN 9. If the wheel can't be installed, the plain CPU wheel stays
# and onnxruntime falls back to CPU with a warning — slower, never broken.
INSTALL_GPU_ASR = INSTALL_TTS + """\
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q',
                'sherpa-onnx==1.13.3+cuda12.cudnn9',
                '-f', 'https://k2-fsa.github.io/sherpa/onnx/cuda.html'])
"""

# Each stage: (num, slug, gpu, install, title_md, body_code).
STAGES = [
    (0, "setup_and_config", False, INSTALL, """\
# CarePath DARAG — Stage 00: Setup & Config  `[CPU]`
Bootstrap the repo, pick a **profile** (`smoke` plumbing check / `full` ViMedCSS
run), mount Drive on Colab, and print the resolved paths. Every later stage reuses
this `init_stage` so run-sizes and artifact paths have one source of truth.""", """\
from carepath.gec import env
print(env.gpu_report())
print('dataset    ->', CTX.dataset)
print('datastore  ->', P.datastore)
print('real pairs ->', P.real_pairs)
print('adapters   ->', P.adapters)
print('serve dir  ->', P.serve_bundle)

# --- Colab Pro runtime plan (which runtime per notebook) ---
print('''
Run the four notebooks in order, each on the runtime it names:
  00_data_prep        [CPU]        datastore + labeled pairs (free, minutes)
  01_asr_synthesis    [GPU L4]     real ASR pairs (bulk decode) + synthetic
                                   transcripts + TTS + synth pairs + leakage
  02_train_predict    [GPU A100]   harvest + augment + QLoRA train + predict
  03_evaluate_export  [CPU]        WER/NE-F1 tables + gate + serve bundle
Full run ~ 3 seeds x 4 variants; training dominates GPU units; the ASR pair decode
(6 decodes/clip over ~150h of audio) and viXTTS are the other long poles — both
GPU. Every step --resumes, so a disconnect continues, it does not restart.
Set CAREPATH_PROFILE=full for the real ViMedCSS run (smoke = plumbing only).''')
"""),
    (1, "build_datastore", False, INSTALL, """\
# Stage 01: Build the NE / code-switch datastore  `[CPU]`
Paper §4.2 Step 1 — union the curated lexicon, dataset `cs_terms_list`, and mined
code-switch tokens into the retrieval datastore.""", """\
CTX.run_step(['scripts/gec/build_datastore.py', '--dataset', CTX.dataset,
              '--limit-per-split', str(PROF.limit_per_split or 0), '--output', str(P.datastore)])
import json
print('terms:', json.load(open(P.datastore, encoding='utf-8'))['metadata']['term_count'])
CTX.save([str(P.datastore)])  # notebook 01 (GPU) restores this for pair building
"""),
    (2, "asr_pairs", True, INSTALL_GPU_ASR, """\
# Stage 02: Real GEC pairs + N-best + error-signal report  `[GPU]`
Paper §3.1 — run Gipformer (or mock for smoke) over ViMedCSS audio to build
`raw_asr -> gold_text` pairs. `--n-best` adds the perturbation hypotheses (paper
§4.3), so the full run decodes each clip 6x — that is the pipeline's bulk decode
and it needs the CUDA provider (weeks on a 2-vCPU runtime, hours on an L4). The
**error-signal report** warns if the ASR is too accurate on train to teach the
corrector (paper §3.2).""", """\
CTX.restore([str(P.datastore)])  # built in the CPU data-prep notebook
pairs_out = CTX.durable(P.real_pairs)  # write straight to Drive on Colab so --resume survives a disconnect
CTX.run_step(['scripts/gec/make_pairs.py', '--dataset', CTX.dataset, '--output', pairs_out,
              '--asr-provider', PROF.asr_provider, '--datastore', str(P.datastore),
              '--retrieval-backend', PROF.retrieval_backend,
              '--limit-per-split', str(PROF.limit_per_split or 0),
              '--n-best', str(PROF.n_best), '--resume'],
             env_extra={'GIPFORMER_PROVIDER': os.environ.get('GIPFORMER_PROVIDER', 'cuda')})
from carepath.gec.data import read_jsonl
from carepath.gec.evaluate import train_error_signal
print(train_error_signal(read_jsonl(pairs_out)))
"""),
    (3, "synth_transcripts", True, INSTALL, """\
# Stage 03: Synthetic in-domain transcripts  `[GPU-light]`
Paper §4.1 Step 1 — few-shot an open LLM for new in-domain transcripts, with the
n-gram leakage guard rejecting near-copies. `synth_count=None` (full) matches the
real train size (nsyn = n).""", """\
# Pull inputs from Drive: no-op in the same session, lets a fresh runtime
# (or a teammate's Colab) resume mid-notebook.
CTX.restore([str(P.datastore), str(P.real_pairs)])
from carepath.gec.data import read_jsonl
count = PROF.synth_count or (sum(1 for r in read_jsonl(P.real_pairs) if r.get('split') == 'train') or 50)
args = ['scripts/gec/gen_synthetic.py', '--pairs', str(P.real_pairs),
        '--output', CTX.durable(P.synth_clean), '--count', str(count)]  # durable: persist so a later disconnect won't regenerate
if PROF.name != 'smoke':
    args.append('--load-in-4bit')
CTX.run_step(args)
"""),
    (4, "voice_clone_tts", True, INSTALL_TTS, """\
# Stage 04: Voice-cloning TTS  `[GPU]`
Paper §4.1 Step 2 / App. D — synthesize speech with viXTTS conditioned on random
in-domain reference clips (falls back to single-speaker MMS, labeled as such).""", """\
args = ['scripts/gec/voice_clone_tts.py', '--input', CTX.durable(P.synth_clean),
        '--output', CTX.durable(P.tts_manifest), '--provider', PROF.tts_provider,  # durable: viXTTS is long, survive a disconnect
        '--ref-dataset', CTX.dataset, '--ref-count', '20', '--resume']
if PROF.synth_tts_limit:
    args += ['--limit', str(PROF.synth_tts_limit)]
CTX.run_step(args)
"""),
    (5, "synth_pairs", True, INSTALL, """\
# Stage 05: Synthetic GEC pairs (+ N-best)  `[CPU/GPU]`
Paper §4.1 Step 3 — run the ASR over the voice-cloned audio to get synthetic
`raw_asr -> gold_text` pairs, with the same perturbation N-best as the real pairs.""", """\
CTX.run_step(['scripts/gec/make_synth_pairs.py', '--input', CTX.durable(P.tts_manifest),
              '--output', CTX.durable(P.synth_pairs), '--datastore', str(P.datastore),
              '--n-best', str(PROF.n_best), '--resume'],  # durable: survive a disconnect, no re-ASR
             env_extra={'GIPFORMER_PROVIDER': os.environ.get('GIPFORMER_PROVIDER', 'cuda')})
"""),
    (6, "leakage_report", True, INSTALL, """\
# Stage 06: Leakage report — in-domain but not memorized  `[GPU-light]`
Paper App. C / Table 6 — SentenceBERT cosine + BLEU of synthetic vs real. High
cosine + low BLEU means the synthetic data is on-domain without copying.""", """\
CTX.run_step(['scripts/gec/check_leakage.py', '--synthetic', CTX.durable(P.synth_clean),
              '--real', str(P.real_pairs), '--output', str(P.leakage)])
import json
print(json.load(open(P.leakage, encoding='utf-8')))
"""),
    (7, "augment_and_train", True, INSTALL, """\
# Stage 07: Augment + QLoRA fine-tune (multi-seed)  `[GPU]`
Paper §5 — merge real ViMedCSS pairs with synthetic (nsyn = n), then train
the DARAG variants over the profile's seeds (full averages 3). Auto-resumes from
checkpoints.""", """\
# Continue-in-a-teammate's-Colab: pull this stage's inputs from Drive first.
CTX.restore([str(P.datastore), str(P.real_pairs)])
CTX.restore_optional([str(P.synth_pairs)])
# Learn real ASR confusions into the datastore (paper Limitation #1), then refresh
# every pair's retrieved NEs so the RAC prompt carries the right term.
harvest = [str(P.real_pairs)]
if Path(P.synth_pairs).exists():
    harvest.append(str(P.synth_pairs))
CTX.run_step(['scripts/gec/harvest_aliases.py', '--datastore', str(P.datastore),
              '--pairs', *harvest, '--refresh', '--backend', PROF.retrieval_backend])
CTX.save([str(P.datastore)])  # enriched datastore feeds eval + the serve bundle
real = [str(P.real_pairs)]
CTX.run_step(['scripts/gec/augment.py', '--real', *real, '--synthetic', str(P.synth_pairs),
              '--output', str(P.augmented), '--nsyn-factor', str(PROF.nsyn_factor)])
CTX.save([str(P.augmented)])  # persist training data to Drive so a teammate can resume
train = ['scripts/gec/train.py', '--pairs', str(P.augmented), '--output-dir', str(P.adapters),
         '--max-steps', str(PROF.max_steps), '--seeds', *[str(s) for s in PROF.seeds]]
train.append('--all-variants' if PROF.all_variants else '--variant')
if not PROF.all_variants:
    train.append('full')
CTX.run_step(train)
"""),
    (8, "predict", True, INSTALL, """\
# Stage 08: LLM/RAG baseline + trained predictions  `[GPU]`
Run the LLM/RAG baseline and the trained `full` adapter so one file carries every
column the tables compare (`raw_asr`, `corrected_text`, `gec_pred`).""", """\
import os
os.environ.setdefault('LLM_PROVIDER', 'offline')
adir = str(P.adapters)
if PROF.all_variants:
    adir = f'{adir}/full'
if len(PROF.seeds) > 1:
    adir = f'{adir}/seed-{PROF.seeds[0]}'
CTX.run_step(['scripts/gec/llm_rag_baseline.py', '--input', str(P.real_pairs), '--output', str(P.llm_rag)])
CTX.run_step(['scripts/gec/predict.py', '--pairs', str(P.llm_rag), '--adapter-dir', adir,
              '--output', str(P.darag_preds), '--column', 'gec_pred'])
CTX.save([str(P.darag_preds)])  # hand predictions to the CPU evaluate/export notebook
"""),
    (9, "evaluate_and_gate", False, INSTALL, """\
# Stage 09: WER + NE-F1 tables + acceptance gate  `[CPU]`
Paper Tables 3 & 4 — WER (syllable + word) and NE micro-F1, then the gate: ship the
adapter only if it matches/beats every baseline on val + hard. For `full`, repeat
predict/evaluate per seed and pass the reports to `evaluate.aggregate_reports` for
mean±std.""", """\
CTX.restore([str(P.darag_preds)])  # predictions from the train+predict notebook
CTX.run_step(['scripts/gec/evaluate.py', '--input', str(P.darag_preds), '--prediction-columns',
              'raw_asr', 'corrected_text', 'gec_pred', '--wer-output', str(P.darag_wer),
              '--ne-f1-output', str(P.darag_ne_f1)])
CTX.run_step(['scripts/gec/gate.py', '--report', str(P.darag_wer)])
import json
from carepath.gec.evaluate import render_ne_f1_table
print(render_ne_f1_table(json.load(open(P.darag_ne_f1, encoding='utf-8'))))
CTX.save([str(P.darag_wer), str(P.darag_ne_f1), str(P.leakage)])
"""),
    (10, "export_and_serve", False, INSTALL, """\
# Stage 10: Export the gated adapter into a serve bundle  `[CPU]`
Package the accepted `full` adapter + the enriched datastore + the frozen DARAG
prompt into a portable `serve_manifest.json` bundle. The FastAPI backend serves it
with `LLM_PROVIDER=gec_local` `GEC_BUNDLE_PATH=<bundle>` — RAC retrieval and a
clinical safety gate (fallback to offline) are wired in `carepath.services.gec_local`.
Run this only after Stage 09's gate accepts the adapter.""", """\
from pathlib import Path
CTX.restore([str(P.datastore)])
adir = str(P.adapters)
if PROF.all_variants:
    adir = f'{adir}/full'
if len(PROF.seeds) > 1:
    adir = f'{adir}/seed-{PROF.seeds[0]}'
CTX.run_step(['scripts/gec/export_serve.py', '--adapter-dir', adir,
              '--datastore', str(P.datastore), '--output', str(P.serve_bundle),
              '--gate-report', str(P.darag_wer)])
CTX.save([str(P.serve_bundle)])
print('Serve with: LLM_PROVIDER=gec_local GEC_BUNDLE_PATH=' + str(P.serve_bundle))
"""),
]


# Group the 11 thin stages into 4 notebooks by RUNTIME tier — one notebook runs
# on one Colab runtime, so cheap text work stays on free CPU runtimes and every
# bulk decode/training step gets a GPU (the full-profile ASR decode is ~6x ~150h
# of audio: weeks on 2 vCPUs, hours with the CUDA provider on an L4). Resume is
# preserved by each step's --resume / restore / save, not by notebook boundaries,
# so a disconnect re-enters the notebook and skips finished steps.
GROUPS = [
    (0, "data_prep", INSTALL, [0, 1], """\
# CarePath DARAG — 00 Data prep  `[CPU runtime]`
Setup + NE datastore. Text-only — minutes on a free Colab CPU runtime. The bulk
ASR decode lives in notebook 01's GPU. Each step resumes, so re-running after a
disconnect skips finished work."""),
    (1, "asr_synthesis", INSTALL_GPU_ASR, [2, 3, 4, 5, 6], """\
# 01 ASR pairs + synthesis  `[GPU — L4 is enough]`
Real ASR pairs first (the pipeline's bulk decode: 6 decodes per clip with N-best,
CUDA sherpa-onnx), then synthetic transcripts → voice-cloned TTS → synthetic pairs
→ leakage report. Long poles: pair decode + viXTTS, both
resume per item."""),
    (2, "train_predict", INSTALL, [7, 8], """\
# 02 Train + predict  `[GPU — A100 advised]`
Harvest real ASR confusions, augment, QLoRA fine-tune the DARAG variants
(multi-seed), then run predictions. Training auto-resumes
from the latest checkpoint."""),
    (3, "evaluate_export", INSTALL, [9, 10], """\
# 03 Evaluate + export  `[CPU runtime]`
WER + NE-F1 tables, acceptance gate, then bundle the gated adapter for serving
CPU — run on a free runtime."""),
]


def _src(text: str) -> list[str]:
    return list(text.splitlines(keepends=True))


def code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": _src(text)}


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _src(text)}


def build() -> None:
    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    for stale in NOTEBOOKS_DIR.glob("[0-9][0-9]_*.ipynb"):
        stale.unlink()  # drop the previous numbering before regenerating
    stage_by_num = {num: (title, body) for num, _slug, _gpu, _inst, title, body in STAGES}
    for gnum, gslug, install, stage_nums, intro in GROUPS:
        cells = [md(intro), code(BOOTSTRAP), code(install)]
        for snum in stage_nums:
            title, body = stage_by_num[snum]
            cells += [md(title), code(body)]
        notebook = {
            "cells": cells,
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                "language_info": {"name": "python"},
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        path = NOTEBOOKS_DIR / f"{gnum:02d}_{gslug}.ipynb"
        path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {path.name}  (stages {stage_nums})")


if __name__ == "__main__":
    build()
