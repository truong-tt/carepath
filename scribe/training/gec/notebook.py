"""Thin glue the stage notebooks call so each one is ~5 cells.

``init_stage(profile)`` resolves the run profile, mounts Drive (Colab), and builds
the shared ``ArtifactPaths`` — returning a ``StageContext`` whose ``run_step`` runs
a pipeline CLI with ``PYTHONPATH`` set and ``restore``/``save`` move artifacts
to/from Drive. On Colab the first notebook cell does a minimal locate-or-clone
before importing this module (it can't import the package until ``scribe`` is
on ``sys.path``).
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from gec import env
from gec.paths import ArtifactPaths
from gec.profiles import RunProfile, get_profile


@dataclass
class StageContext:
    profile: RunProfile
    paths: ArtifactPaths
    backup: Path | None
    in_colab: bool
    dataset: str = "tensorxt/ViMedCSS"

    def run_step(self, args: list[str], env_extra: dict | None = None) -> None:
        """Run a ``scribe/training/scripts/*`` CLI with PYTHONPATH set, raising on failure."""

        run_env = dict(os.environ)
        run_env["PYTHONPATH"] = os.pathsep.join(("scribe/training", "scribe"))
        run_env["PYTHONIOENCODING"] = "utf-8"
        if env_extra:
            run_env.update(env_extra)
        printable = " ".join(str(a) for a in args)
        print(">>>", printable, flush=True)
        proc = subprocess.run([sys.executable, *map(str, args)], env=run_env)
        if proc.returncode != 0:
            raise RuntimeError(f"step failed ({proc.returncode}): {printable}")

    def restore(self, rel_paths: list[str]) -> None:
        env.restore_artifacts(self.backup, rel_paths)

    def restore_optional(self, rel_paths: list[str]) -> None:
        """Copy artifacts from Drive *if present*, without failing when they aren't.

        Used for inputs that may legitimately be absent (no synthetic pairs, no
        labeled export) so a teammate continuing a run on a fresh Colab still pulls
        whatever exists on Drive.
        """

        if self.backup is None:
            return  # local: files already on disk (or intentionally absent)
        import shutil

        for rel in rel_paths:
            dst = Path(rel)
            src = self.backup / dst.name
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(src, dst)
                print("restored", dst, "from", src)
            else:
                print("(optional, not on Drive):", dst)

    def save(self, rel_paths: list[str]) -> None:
        env.save_artifacts(self.backup, rel_paths)

    def durable(self, path: str | Path) -> str:
        """Output path that survives a Colab runtime recycle.

        Long, resumable stages (ASR pairs, TTS) write here so ``--resume`` can pick
        up after a disconnect: on Colab that's the Drive backup, where every flushed
        row already persists; locally it's the normal ``artifacts/`` path. Uses the
        same basename as ``save``/``restore`` so a downstream stage's ``restore``
        finds it unchanged.
        """

        p = Path(path)
        if self.backup is None:
            return str(p)
        dst = self.backup / p.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        return str(dst)


def init_stage(profile: str = "smoke", dataset: str = "tensorxt/ViMedCSS") -> StageContext:
    """Resolve profile + Drive backup + artifact paths for a stage notebook."""

    prof = get_profile(profile)
    in_colab = env.in_colab()
    backup = env.setup_backup(in_colab)
    suffix = "" if prof.name == "full" else f"_{prof.name}"
    adapters_root = (backup / "gec_lora" / "qwen3") if backup else None
    paths = ArtifactPaths(root=Path("artifacts"), suffix=suffix, adapters_root=adapters_root)
    print(f"profile={prof.name} | n_best={prof.n_best} | seeds={prof.seeds} | adapters={paths.adapters}")
    return StageContext(profile=prof, paths=paths, backup=backup, in_colab=in_colab, dataset=dataset)
