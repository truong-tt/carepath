from __future__ import annotations

import argparse
import json

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the running CarePath API is using a real LLM provider."
    )
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=120.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_url = args.url.rstrip("/")

    with httpx.Client(timeout=args.timeout) as client:
        health = client.get(f"{base_url}/api/v1/health")
        health.raise_for_status()
        health_json = health.json()
        if health_json.get("llm_provider") not in {"ckey", "openai_compatible", "openai"}:
            raise SystemExit(
                "API is not using a real LLM provider. Set LLM_PROVIDER=ckey and restart."
            )
        if not health_json.get("llm_ready"):
            raise SystemExit(f"LLM is not ready: {json.dumps(health_json, indent=2)}")

        correction = client.post(
            f"{base_url}/api/v1/corrections",
            json={
                "raw_transcript": (
                    "benh nhan dau nguc, spo2 98 phan tram, "
                    "huyet ap 120 tren 80 mmhg"
                ),
                "encounter_context": "Phong kham noi tong quat",
            },
        )
        if correction.status_code >= 400:
            raise SystemExit(
                f"Correction request failed: HTTP {correction.status_code} {correction.text}"
            )

        payload = correction.json()
        print(
            json.dumps(
                {
                    "llm_provider": health_json["llm_provider"],
                    "llm_details": health_json["details"]["llm"],
                    "corrected_transcript": payload["corrected_transcript"],
                    "retrieved_terms": payload["retrieved_terms"],
                    "metadata": payload["metadata"],
                },
                ensure_ascii=True,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
