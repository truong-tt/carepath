"""Merge independently gated real GEC and SOAP components into one private bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scribe" / "training"))

from soap.bundle import validate_bundle  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--soap-bundle", type=Path, required=True)
    component = parser.add_mutually_exclusive_group(required=True)
    component.add_argument("--gec-bundle", type=Path)
    component.add_argument("--asr-component", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--confirm-stack", action="store_true")
    args = parser.parse_args()
    if not args.confirm_stack:
        raise SystemExit("Pass --confirm-stack after both components independently pass their gates")
    soap = validate_bundle(args.soap_bundle.resolve())
    if args.output.exists():
        shutil.rmtree(args.output)
    shutil.copytree(args.soap_bundle.resolve(), args.output)
    (args.output / "reports").mkdir()
    if args.gec_bundle:
        _merge_gec(soap, args.gec_bundle.resolve(), args.output)
    else:
        _record_direct_asr(soap, args.asr_component.resolve(), args.output)
    manifest_path = args.output / "scribe_manifest.json"
    manifest_path.unlink(missing_ok=True)
    soap["files"] = {
        str(path.relative_to(args.output)).replace("\\", "/"): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(args.output.rglob("*"))
        if path.is_file()
    }
    manifest_path.write_text(
        json.dumps(soap, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    validate_bundle(args.output)
    print(f"Wrote independently gated Scribe research bundle to {args.output}")


def _merge_gec(soap: dict, gec_path: Path, output: Path) -> None:
    gec = json.loads((gec_path / "serve_manifest.json").read_text(encoding="utf-8"))
    if gec.get("schema") != "carepath.gec.serve/1" or gec.get("gate_accepted") is not True:
        raise SystemExit("GEC bundle lacks an independently accepted safety gate")
    if gec.get("base_model") != soap["base_model"]:
        raise SystemExit("GEC and SOAP adapters do not share the same base model")
    if gec.get("base_revision") and gec["base_revision"] != soap.get("base_revision"):
        raise SystemExit("GEC and SOAP adapters do not share the same base revision")
    adapter, datastore = gec_path / gec["adapter_dir"], gec_path / gec["datastore"]
    if not adapter.is_dir() or not datastore.is_file():
        raise SystemExit("GEC bundle is missing its adapter or retrieval datastore")
    shutil.copytree(adapter, output / "adapters" / "gec")
    (output / "retrieval").mkdir()
    shutil.copy2(datastore, output / "retrieval" / "term_datastore.json")
    shutil.copy2(gec_path / "serve_manifest.json", output / "reports" / "gec_manifest.json")
    soap["adapters"]["gec"] = "adapters/gec"
    soap["correction_mode"] = "adapter"
    soap.setdefault("prompts", {})["gec"] = gec["prompt"]["system"]
    soap.setdefault("max_new_tokens", {})["gec"] = int(gec.get("max_new_tokens", 256))
    soap["retrieval"] = {"datastore": "retrieval/term_datastore.json"}
    soap["transcript_component"] = {"kind": "gec_adapter", "gate": "reports/gec_manifest.json"}
    soap["component_gates"] = {"soap": "evaluation.json", "gec": "reports/gec_manifest.json"}


def _record_direct_asr(soap: dict, component_path: Path, output: Path) -> None:
    if not component_path.is_dir():
        raise SystemExit("--asr-component must be a gated component directory")
    component_manifest = component_path / "asr_component.json"
    component = json.loads(component_manifest.read_text(encoding="utf-8"))
    if component.get("schema") != "carepath.asr.component/1":
        raise SystemExit("unsupported direct-ASR component schema")
    if component.get("gate_accepted") is not True:
        raise SystemExit("direct-ASR component lacks an independently accepted safety gate")
    if component.get("selected_for_serving") is not True:
        raise SystemExit("direct-ASR component did not win final transcript selection")
    if component.get("usage_scope") != "research_only":
        raise SystemExit("direct-ASR component must remain research_only")
    revision = str(component.get("revision", ""))
    if (
        len(revision) != 40
        or set(revision.lower()) - set("0123456789abcdef")
        or component.get("tokenizer_revision") != revision
    ):
        raise SystemExit("direct-ASR component requires exact matching model/tokenizer revisions")
    files = component.get("files")
    if not isinstance(files, dict) or not files:
        raise SystemExit("direct-ASR component must contain hashed model/tokenizer files")
    for relative, expected in files.items():
        path = component_path / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit(f"direct-ASR component file hash mismatch: {relative}")
    for role in ("adapter", "tokenizer", "metrics", "staging_evidence"):
        relative = str(component.get(role, ""))
        if not relative or relative not in files:
            raise SystemExit(f"direct-ASR component manifest must hash its {role} artifact")
    evidence_path = component_path / str(component.get("staging_evidence", ""))
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit("direct-ASR component requires real-GPU staging evidence") from exc
    if evidence.get("status") != "passed" or evidence.get("real_gpu") is not True:
        raise SystemExit("direct-ASR component real-GPU staging evidence has not passed")
    bundled = output / "transcript" / "asr"
    bundled.parent.mkdir()
    shutil.copytree(component_path, bundled)
    soap["correction_mode"] = "identity"
    soap["transcript_component"] = {
        "kind": "direct_asr",
        "model": component.get("model"),
        "revision": component.get("revision"),
        "path": "transcript/asr",
        "manifest": "transcript/asr/asr_component.json",
        "staging_evidence": f"transcript/asr/{component['staging_evidence']}",
    }
    soap["component_gates"] = {"soap": "evaluation.json", "asr": "transcript/asr/asr_component.json"}


if __name__ == "__main__":
    main()
