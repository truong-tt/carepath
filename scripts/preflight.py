"""Demo preflight: warm up ASR and probe the live LLM before going on stage.

Unlike ``smoke_backend.py`` (which forces mock/offline), this uses your real
``.env`` so it validates the actual demo path:

1. Loads settings and prints the active providers.
2. Reports pipeline health.
3. Warms up ASR (downloads + loads Gipformer ONNX so the first real request is fast).
4. Probes the *primary* LLM directly (bypassing the offline fallback) so a broken
   CKey link is surfaced, not silently masked.
5. Runs a full text round-trip to confirm an end-to-end SOAP draft is produced.

Exit code is non-zero only for failures that would break the live demo
(ASR warmup or the end-to-end round-trip). A failed LLM probe is a warning,
because the offline fallback keeps the demo serving notes.

Usage:
    python scripts/preflight.py
    python scripts/preflight.py --skip-asr          # skip the model download
    python scripts/preflight.py --no-llm-probe      # do not call the live LLM
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def _status(ok: bool, warn: bool = False) -> str:
    if ok:
        return "[OK]  "
    return "[WARN]" if warn else "[FAIL]"


def main() -> int:
    parser = argparse.ArgumentParser(description="CarePath demo preflight")
    parser.add_argument("--skip-asr", action="store_true", help="Skip ASR model warmup")
    parser.add_argument(
        "--no-llm-probe", action="store_true", help="Do not call the live LLM"
    )
    args = parser.parse_args()

    # Vietnamese text (and provider error bodies) break the default Windows
    # cp1252 console; force UTF-8 so prints and stderr logs never crash.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001 - older/odd streams have no reconfigure
            pass

    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "scribe"))

    from carepath.config import load_settings
    from carepath.logging_config import configure_logging
    from carepath.services.asr import ASRError
    from carepath.services.pipeline import CarePathPipeline

    configure_logging()
    settings = load_settings()

    print("CarePath preflight")
    print("------------------")
    print(f"  app_env        : {settings.app_env}")
    print(f"  asr_provider   : {settings.asr_provider}")
    print(f"  llm_provider   : {settings.llm_provider}")
    print(f"  llm_model      : {settings.llm_model}")
    print(f"  llm_base_url   : {settings.llm_base_url}")
    print(f"  offline_fallback: {settings.llm_fallback_offline}")
    print()

    pipeline = CarePathPipeline(settings)
    hard_fail = False

    health = pipeline.health()
    print(f"{_status(health['status'] == 'ok')} health: {health['status']}")
    print(f"        asr_ready={health['asr_ready']} llm_ready={health['llm_ready']}")

    if not args.skip_asr:
        start = time.perf_counter()
        try:
            report = pipeline.warmup(probe_llm=not args.no_llm_probe)
            elapsed = time.perf_counter() - start
            print(f"{_status(True)} asr warmup: {report['asr']} ({elapsed:.1f}s)")
            if "llm" in report:
                llm = report["llm"]
                ok = llm.get("probe") == "ok"
                print(f"{_status(ok, warn=not ok)} llm probe: {llm}")
        except ASRError as exc:
            hard_fail = True
            print(f"{_status(False)} asr warmup failed: {exc}")
    elif not args.no_llm_probe:
        # ASR skipped, but still probe the LLM directly (no model download).
        llm = pipeline.probe_llm()
        ok = llm.get("probe") == "ok"
        print(f"{_status(ok, warn=not ok)} llm probe: {llm}")

    # End-to-end text round-trip (uses fallback, so it must always succeed).
    try:
        output = pipeline.process_text(
            "benh nhan dau nguc spo2 98 % huyet ap 120 tren 80 mmhg",
            encounter_context="Phong kham noi tong quat",
        )
        print(
            f"{_status(True)} round-trip: gec_mode={output.metadata.get('gec_mode')} "
            f"soap_mode={output.metadata.get('soap_mode')} "
            f"terms={output.retrieved_terms and [t.term for t in output.retrieved_terms]}"
        )
    except Exception as exc:  # noqa: BLE001 - report any failure, do not crash
        hard_fail = True
        print(f"{_status(False)} round-trip failed: {exc}")

    print()
    if hard_fail:
        print("PREFLIGHT FAILED - fix the items above before the demo.")
        return 1
    print("PREFLIGHT OK - demo path is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
