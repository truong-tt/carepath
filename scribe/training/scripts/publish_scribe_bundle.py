"""Publish an accepted real research bundle to a confirmed private Hugging Face repo."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scribe" / "training"))

from soap.bundle import validate_bundle  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--confirm-private-upload", action="store_true")
    args = parser.parse_args()
    if not args.confirm_private_upload:
        raise SystemExit("Pass --confirm-private-upload to authorize the private bundle upload")
    try:
        validate_bundle(args.bundle.resolve())
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise SystemExit("HF_TOKEN is required from an environment variable or Colab Secret")
    from huggingface_hub import HfApi  # type: ignore

    api = HfApi(token=token)
    api.create_repo(args.repo_id, repo_type="model", private=True, exist_ok=True)
    info = api.repo_info(args.repo_id, repo_type="model")
    if not info.private:
        raise SystemExit("refusing upload because the Hugging Face repository is not private")
    api.upload_folder(
        repo_id=args.repo_id,
        repo_type="model",
        folder_path=str(args.bundle.resolve()),
        commit_message="Upload accepted CarePath research-only Scribe bundle",
    )
    print(f"Uploaded accepted research bundle to private model repository {args.repo_id}")


if __name__ == "__main__":
    main()
