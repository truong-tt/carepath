"""Generate or verify the five thin Colab orchestration notebooks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

NOTEBOOKS_DIR = Path(__file__).resolve().parents[1] / "notebooks"

BOOTSTRAP = r'''# CarePath bootstrap: local checkout first, otherwise a private GitHub clone.
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def _find(start):
    for directory in [start, *start.parents]:
        if (directory / 'pyproject.toml').exists() and (directory / 'scribe' / 'carepath').exists():
            return directory
    return None

def _secret():
    for key in ('CAREPATH_GITHUB_TOKEN', 'GITHUB_TOKEN'):
        if os.environ.get(key):
            return os.environ[key]
    try:
        from google.colab import userdata
        for key in ('CAREPATH_GITHUB_TOKEN', 'GITHUB_TOKEN'):
            try:
                value = userdata.get(key)
                if value:
                    return value
            except Exception:
                pass
    except Exception:
        pass
    return None

def _inject_runtime_secrets():
    """Copy only approved named Colab secrets into memory for child processes."""
    try:
        from google.colab import userdata
    except Exception:
        return
    for key in ('LLM_API_KEY', 'HF_TOKEN'):
        if os.environ.get(key):
            continue
        try:
            value = userdata.get(key)
        except Exception:
            value = None
        if value:
            os.environ[key] = value

REPO = _find(Path.cwd().resolve())
if REPO is None and importlib.util.find_spec('google.colab'):
    target = Path('/content/carepath')
    REPO = _find(target)
    if REPO is None:
        if target.exists():
            shutil.rmtree(target)
        url = os.environ.get('CAREPATH_REPO_URL', 'https://github.com/truong-tt/carepath.git')
        if '://' in url and '@' in url.split('://', 1)[1].split('/', 1)[0]:
            raise SystemExit('CAREPATH_REPO_URL must not contain credentials; use a Colab Secret.')
        token = _secret()
        clone_env = dict(os.environ)
        clone_env['GIT_TERMINAL_PROMPT'] = '0'
        with tempfile.TemporaryDirectory(prefix='carepath_git_') as temp:
            if token:
                askpass = Path(temp) / 'askpass.sh'
                askpass.write_text(
                    '#!/bin/sh\ncase "$1" in *Username*) echo x-access-token ;; *) echo "$GITHUB_TOKEN" ;; esac\n',
                    encoding='utf-8',
                )
                askpass.chmod(0o700)
                clone_env['GIT_ASKPASS'] = str(askpass)
                clone_env['GITHUB_TOKEN'] = token
            result = subprocess.run(
                ['git', 'clone', url, str(target)],
                env=clone_env,
                capture_output=True,
                text=True,
            )
        if result.returncode:
            error = result.stderr or result.stdout
            if token:
                error = error.replace(token, '***')
            raise SystemExit(
                'Clone failed. Add a Colab Secret named GITHUB_TOKEN with repository read access, '
                'enable Notebook access, then rerun.\n' + error
            )
        REPO = target

assert REPO, 'Run the notebook inside CarePath or from Google Colab.'
os.chdir(REPO)
sys.path[:0] = [str(REPO / 'scribe' / 'training'), str(REPO / 'scribe')]
_inject_runtime_secrets()

PROFILE = os.environ.get('CAREPATH_PROFILE', 'smoke')
CONFIRM_PAID = os.environ.get('CAREPATH_CONFIRM_PAID') == '1'
from gec.notebook import init_stage
CTX = init_stage(PROFILE, confirm_paid=CONFIRM_PAID)
P, PROF = CTX.paths, CTX.profile
'''

INSTALL_BASE = r"""# Pin the repository's tested training and combined-app environment.
extras = ['dev', 'training']
if PROFILE == 'reproduction':
    extras.append('training-tts')
"""

INSTALL_NORMAL = INSTALL_BASE + r"""extra = '.[' + ','.join(extras) + ']'
subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '-q', '-e', extra, '-e', './shared', '-e', './interpreter'],
    check=True,
)
"""

INSTALL_FAST = INSTALL_BASE + r"""if PROF.paid:
    extras.append('training-fast')
extra = '.[' + ','.join(extras) + ']'
subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '-q', '-e', extra, '-e', './shared', '-e', './interpreter'],
    check=True,
)
"""

NOTEBOOK_SPECS = (
    (
        "00_data_prep.ipynb",
        INSTALL_NORMAL,
        "# CarePath — 00 Data preparation `[CPU]`\n\n"
        "Validate the selected profile and build the term datastore. Smoke is the default; paid "
        "profiles require `CAREPATH_CONFIRM_PAID=1` and an approved dataset manifest.",
        "CTX.run_pipeline('data')\n"
        "if PROF.paid:\n"
        "    CTX.run_step([\n"
        "        'scribe/training/scripts/prepare_public_sources.py',\n"
        "        '--manifest', 'scribe/training/manifests/soap-public-v1.json',\n"
        "        '--canonical', 'shared/carepath_shared/terms/medical_terms.json',\n"
        "        '--output-root', '/content/carepath_data',\n"
        "    ])\n"
        "print('datastore ->', P.datastore)\n",
    ),
    (
        "01_asr_benchmark.ipynb",
        INSTALL_NORMAL,
        "# CarePath — 01 ASR benchmark `[L4 for real data]`\n\n"
        "Build production-compatible **single-best** Gipformer pairs and a duration-derived "
        "benchmark. Paid profiles train/evaluate plain PhoWhisper-small LoRA on ViMedCSS train only; "
        "the reproduction profile fails closed if the plain-LoRA gate makes the still-unimplemented "
        "contrastive near-miss stage mandatory.",
        "CTX.run_pipeline('asr')\nprint(P.asr_benchmark.read_text(encoding='utf-8'))\n",
    ),
    (
        "02_train_gec.ipynb",
        INSTALL_FAST,
        "# CarePath — 02 Transcript correction `[L4/A100]`\n\n"
        "Run optional synthetic/TTS work only for the explicit reproduction profile, then train "
        "the configured candidate and seed through the consent-gated orchestrator.",
        "if PROF.enable_synthetic:\n    CTX.run_pipeline('synth')\n"
        "CTX.run_pipeline('train')\nprint('candidate adapter ->', P.candidate_adapter(\n"
        "    PROF.candidate_variant, PROF.candidate_seed, all_variants=PROF.all_variants, "
        "multi_seed=len(PROF.seeds) > 1))\n",
    ),
    (
        "03_train_soap.ipynb",
        INSTALL_FAST,
        "# CarePath — 03 Grounded SOAP training `[L4/A100]`\n\n"
        "Call the sibling SOAP orchestrator. Its data, factual filters, and export gates remain "
        "owned by the SOAP training package.",
        "CTX.run_soap_pipeline()\n",
    ),
    (
        "04_evaluate_export_stage.ipynb",
        INSTALL_NORMAL,
        "# CarePath — 04 Evaluate, gate, export, and stage `[CPU, then GPU smoke]`\n\n"
        "Run normal and frozen safety evaluation through the same orchestrator as CI. Export occurs "
        "only when the selected trained candidate clears both gates; mock bundles are deliberately refused.",
        "import json\n"
        "CTX.run_pipeline('eval')\n"
        "selection = json.loads(P.candidate_selection.read_text(encoding='utf-8'))\n"
        "print(json.dumps(selection, ensure_ascii=False, indent=2))\n"
        "asr_component = P.asr_lora_root / f'seed-{PROF.candidate_seed}'\n"
        "asr_manifest = asr_component / 'asr_component.json'\n"
        "if asr_manifest.exists():\n"
        "    asr_meta = json.loads(asr_manifest.read_text(encoding='utf-8'))\n"
        "    if asr_meta.get('gate_accepted') and asr_meta.get('selected_for_serving'):\n"
        "        CTX.run_step([\n"
        "            'scribe/training/scripts/stage_asr_component.py',\n"
        "            '--component', str(asr_component), '--manifest', str(CTX.config_path.parent.parent / 'manifests' / 'vimedcss-v1.json'),\n"
        "            '--predictions', str(P.evaluations / 'asr_staging_predictions.jsonl'),\n"
        "            '--report', str(P.evaluations / 'asr_staging_report.json'), '--confirm-paid'])\n"
        "    else:\n"
        "        print('Direct-ASR staging deliberately skipped: component did not pass and win selection.')\n"
        "from soap.bundle import validate_bundle\n"
        "from soap.config import load_config as load_soap_config\n"
        "soap_profile = 'replicate' if PROFILE == 'reproduction' else PROFILE\n"
        "soap_cfg_path = Path('scribe/training/configs') / f'soap-{soap_profile}-v1.json'\n"
        "if not soap_cfg_path.exists() and PROFILE == 'smoke':\n"
        "    soap_cfg_path = Path('scribe/training/configs/soap-smoke-v1.json')\n"
        "soap_cfg = load_soap_config(soap_cfg_path)\n"
        "soap_bundle = P.root / soap_cfg.run_id / 'bundle'\n"
        "assembled = P.root / 'accepted_scribe_bundle'\n"
        "try:\n"
        "    validate_bundle(soap_bundle)\n"
        "except ValueError as exc:\n"
        "    print('Staging deliberately refused:', exc)\n"
        "else:\n"
        "    component_args = None\n"
        "    if selection['selected'] == 'gec_pred' and P.serve_bundle.exists():\n"
        "        component_args = ['--gec-bundle', str(P.serve_bundle)]\n"
        "    elif selection['selected'] == 'phowhisper_pred' and asr_manifest.exists():\n"
        "        component_args = ['--asr-component', str(asr_component)]\n"
        "    if component_args:\n"
        "        CTX.run_step(['scribe/training/scripts/assemble_scribe_bundle.py', '--soap-bundle', str(soap_bundle), *component_args, '--output', str(assembled), '--confirm-stack'])\n"
        "        CTX.run_step(['scribe/training/scripts/stage_scribe_bundle.py', '--bundle', str(assembled)])\n"
        "    else:\n"
        "        print('No assembled bundle staged: raw Gipformer baseline or no accepted transcript component.')\n"
        "print('Private publishing remains a separate explicit --confirm-private-upload command.')\n",
    ),
)


def _source(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def _notebook(install: str, title: str, body: str) -> str:
    payload = {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": _source(title)},
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": _source(BOOTSTRAP),
            },
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": _source(install),
            },
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": _source(body),
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return json.dumps(payload, ensure_ascii=False, indent=1) + "\n"


def build(*, check: bool = False) -> None:
    expected = {
        name: _notebook(install, title, body)
        for name, install, title, body in NOTEBOOK_SPECS
    }
    actual_names = {path.name for path in NOTEBOOKS_DIR.glob("[0-9][0-9]_*.ipynb")}
    drift = sorted(actual_names ^ expected.keys())
    drift += [
        name
        for name, content in expected.items()
        if not (NOTEBOOKS_DIR / name).exists()
        or (NOTEBOOKS_DIR / name).read_text(encoding="utf-8") != content
    ]
    if check:
        if drift:
            raise SystemExit(
                "generated notebooks drifted: " + ", ".join(sorted(set(drift)))
            )
        print("Generated notebooks are current.")
        return
    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    for stale in NOTEBOOKS_DIR.glob("[0-9][0-9]_*.ipynb"):
        if stale.name not in expected:
            stale.unlink()
    for name, content in expected.items():
        (NOTEBOOKS_DIR / name).write_text(content, encoding="utf-8")
        print("wrote", name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if generated notebooks drift"
    )
    args = parser.parse_args()
    build(check=args.check)


if __name__ == "__main__":
    main()
