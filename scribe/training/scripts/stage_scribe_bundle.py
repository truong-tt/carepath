"""Reload an accepted real Scribe bundle and exercise it through FastAPI in Colab."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scribe" / "training"))
sys.path.insert(0, str(ROOT / "scribe"))
sys.path.insert(0, str(ROOT / "shared"))

from soap.bundle import validate_bundle  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = validate_bundle(args.bundle.resolve())
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    retrieval = manifest.get("retrieval", {}).get("datastore")
    lexicon = args.bundle.resolve() / retrieval if retrieval else ROOT / "data" / "medical_lexicon.json"
    os.environ.update(
        {
            "CAREPATH_ENV_FILE": "__colab_stage_no_env__",
            "APP_ENV": "stage",
            "ASR_PROVIDER": "mock",
            "ALLOW_MOCK_ASR": "true",
            "LLM_PROVIDER": "scribe_local",
            "SCRIBE_BUNDLE_PATH": str(args.bundle.resolve()),
            "LLM_FALLBACK_OFFLINE": "false",
            "MEDICAL_LEXICON_PATH": str(lexicon),
        }
    )
    from fastapi.testclient import TestClient

    from carepath.main import app, get_pipeline, get_settings

    get_settings.cache_clear()
    get_pipeline.cache_clear()
    if get_settings().medical_lexicon_path.resolve() != lexicon.resolve():
        raise SystemExit("staging did not select the bundled retrieval datastore")
    text = (
        "Bệnh nhân đau họng, không khó thở. "
        "Bác sĩ chẩn đoán viêm họng và kê paracetamol 500 mg khi đau."
    )
    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        health.raise_for_status()
        details = health.json()["details"]["llm"]
        if details.get("adapters") != sorted(manifest["adapters"]):
            raise SystemExit("staging health did not report the selected adapter set")
        if details.get("fallback") != "disabled":
            raise SystemExit("staging must disable the offline fallback")
        response = client.post("/api/v1/corrections", json={"raw_transcript": text})
        response.raise_for_status()
        if response.json()["metadata"].get("soap_mode") != "scribe_local":
            raise SystemExit("staging API did not use the Scribe SOAP adapter")
    output = get_pipeline().process_text(text)
    if not output.soap.review_required or output.metadata.get("soap_mode") != "scribe_local":
        raise SystemExit("staging pipeline did not return a review-required Scribe SOAP note")
    if getattr(get_pipeline().llm, "provider_name", None) != "scribe_local":
        raise SystemExit("staging provider identity is not scribe_local")
    transcript_component = manifest.get("transcript_component", {})
    if transcript_component.get("kind") == "direct_asr":
        evidence_path = args.bundle.resolve() / str(
            transcript_component.get("staging_evidence", "")
        )
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            evidence = {}
        direct_asr_status = (
            "prior_real_gpu_evidence_validated; current_mock_asr_did_not_exercise_direct_asr"
            if evidence.get("status") == "passed" and evidence.get("real_gpu") is True
            else "pending; current_mock_asr_did_not_exercise_direct_asr"
        )
    else:
        direct_asr_status = "not_selected"
    print(
        "PASS: accepted real bundle reloaded with no fallback and passed API/SOAP staging; "
        f"retrieval={lexicon}; direct_asr={direct_asr_status}"
    )


if __name__ == "__main__":
    main()
