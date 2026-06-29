"""Environment + storage helpers so the DARAG notebooks run on Colab *or* a local GPU.

The two Colab notebooks call these to stay portable:

* ``in_colab`` / ``gpu_report`` — detect the runtime and give a beginner a clear
  read on whether a usable GPU is present (and which base model will fit).
* ``setup_backup`` — mount Google Drive on Colab and return a backup root; on a
  local machine it returns ``None`` because the repo's ``artifacts/`` already
  persists on disk.
* ``restore_artifacts`` / ``save_artifacts`` — copy to/from that backup on Colab,
  and degrade to a presence check / no-op locally.
* ``latest_checkpoint`` — find a resumable Trainer checkpoint so an interrupted
  run (a Colab disconnect or a student closing the lid) continues instead of
  starting over.

Heavy imports (torch, google.colab) are local so this module imports anywhere.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

DEFAULT_DRIVE_SUBDIR = "carepath_artifacts"


def in_colab() -> bool:
    """True when running inside Google Colab.

    ``find_spec`` raises (not returns None) when the parent ``google`` package is
    absent, so guard it — off-Colab that just means "not Colab".
    """

    try:
        return importlib.util.find_spec("google.colab") is not None
    except ModuleNotFoundError:
        return False


def gpu_report() -> str:
    """Human-readable GPU status + which base model fits, for the notebook header."""

    try:
        import torch  # type: ignore
    except Exception:
        return (
            "PyTorch not importable yet - run the install cell first. "
            "Training needs a CUDA GPU."
        )
    if not torch.cuda.is_available():
        return (
            "No CUDA GPU detected - training would be far too slow on CPU.\n"
            "  Colab: Runtime > Change runtime type > GPU (T4 or L4).\n"
            "  Local: you need an NVIDIA GPU with a CUDA-enabled PyTorch build "
            "(on Windows, WSL2 is the reliable path)."
        )
    idx = torch.cuda.current_device()
    name = torch.cuda.get_device_name(idx)
    vram_gb = torch.cuda.get_device_properties(idx).total_memory / 1e9
    if vram_gb < 8:
        hint = (
            "\n  VRAM < 8 GB: use the smaller base model - add "
            '--base-model "Qwen/Qwen2.5-3B-Instruct" to the train step.'
        )
    elif vram_gb < 12:
        hint = "\n  VRAM 8-12 GB: Qwen3-4B in 4-bit fits at batch size 1 (the default)."
    else:
        hint = "\n  VRAM >= 12 GB: comfortable for Qwen3-4B 4-bit QLoRA."
    return f"GPU OK: {name}, {vram_gb:.1f} GB VRAM.{hint}"


def setup_backup(is_colab: bool | None = None, drive_subdir: str = DEFAULT_DRIVE_SUBDIR) -> Path | None:
    """Mount Drive and return the backup root on Colab; return ``None`` locally.

    On Colab the returned directory is where Part 1 artifacts live and where
    Part 2 adapters/metrics are persisted, so progress survives a disconnect.
    """

    if is_colab is None:
        is_colab = in_colab()
    if not is_colab:
        print("Local run: artifacts persist in the repo's artifacts/ folder (no Drive needed).")
        return None
    from google.colab import drive  # type: ignore

    drive.mount("/content/drive")
    backup = Path("/content/drive/MyDrive") / drive_subdir
    backup.mkdir(parents=True, exist_ok=True)
    print("Colab run: artifacts back up to", backup)
    return backup


def restore_artifacts(backup: Path | None, rel_paths: list[str]) -> None:
    """Bring Part 1 outputs into the working tree.

    Colab: copy ``<backup>/<basename>`` to the repo-relative path. Local: just
    confirm the file already exists (Part 1 wrote it to disk), with a clear error
    pointing back to Part 1 if it does not.
    """

    import shutil

    for rel in rel_paths:
        dst = Path(rel)
        if backup is None:
            if not dst.exists():
                raise SystemExit(f"Missing {dst}. Run Part 1 (data prep) first to create it.")
            print("found", dst)
            continue
        src = backup / dst.name
        if not src.exists():
            raise SystemExit(f"Missing {src} on Drive. Run Part 1 (data prep) first.")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
        print("restored", dst, "from", src)


def save_artifacts(backup: Path | None, rel_paths: list[str]) -> None:
    """Persist result files. Colab: copy to Drive. Local: no-op (already on disk)."""

    import shutil

    for rel in rel_paths:
        src = Path(rel)
        if not src.exists():
            continue
        if backup is None:
            print("on disk:", src.resolve())
            continue
        dst = backup / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
        print("saved", dst)


def bundle_adapter(
    adapter_dir: str | Path,
    dest_root: str | Path,
    name: str | None = None,
    make_zip: bool = True,
) -> tuple[Path, Path | None]:
    """Copy the *final* adapter into a small, student-ready bundle (+ optional zip).

    The trained ``output_dir`` also holds bulky ``checkpoint-*`` folders (optimizer
    state, only needed to *resume* training). Those are skipped here so the shared
    bundle is just what inference needs: ``adapter_config.json``,
    ``adapter_model.safetensors``, the tokenizer files, and ``darag_variant.json``
    (~tens of MB). Returns ``(bundle_dir, zip_path or None)``.

    To use the bundle the recipient needs a GPU and the matching base model
    (downloaded automatically) — no dataset and no training.
    """

    import shutil

    adapter_dir = Path(adapter_dir)
    if not (adapter_dir / "adapter_config.json").exists():
        raise SystemExit(
            f"No adapter at {adapter_dir} (expected adapter_config.json). "
            "Train the 'full' variant first."
        )
    bundle = Path(dest_root) / (name or adapter_dir.name)
    if bundle.exists():
        shutil.rmtree(bundle)
    bundle.mkdir(parents=True, exist_ok=True)
    for item in adapter_dir.iterdir():
        if item.is_dir() and item.name.startswith("checkpoint-"):
            continue  # resumable optimizer state, not needed for inference
        if item.is_dir():
            shutil.copytree(item, bundle / item.name)
        else:
            shutil.copy(item, bundle / item.name)
    zip_path = (
        Path(shutil.make_archive(str(bundle), "zip", root_dir=str(bundle)))
        if make_zip
        else None
    )
    return bundle, zip_path


def latest_checkpoint(output_dir: str | Path) -> str | None:
    """Return the newest ``checkpoint-<step>`` dir under ``output_dir``, or ``None``.

    Used to resume training: a higher step number is newer. Non-numeric or empty
    dirs are ignored so a malformed folder never blocks a fresh run.
    """

    output_dir = Path(output_dir)
    if not output_dir.exists():
        return None

    def step_of(path: Path) -> int:
        suffix = path.name.split("-")[-1]
        return int(suffix) if suffix.isdigit() else -1

    checkpoints = [
        p for p in output_dir.glob("checkpoint-*")
        if p.is_dir() and step_of(p) >= 0
    ]
    if not checkpoints:
        return None
    return str(max(checkpoints, key=step_of))
