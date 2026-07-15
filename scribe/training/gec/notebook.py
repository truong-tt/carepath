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
from gec.profiles import RunProfile
from gec.run_config import load_pipeline_config

PROFILE_CONFIGS = {
    "smoke": "smoke-v2.json",
    "pilot": "pilot-v1.json",
    "research-full": "research-full-v1.json",
    "replicate": "replicate-v1.json",
    "reproduction": "reproduction-v1.json",
}


@dataclass
class StageContext:
    profile: RunProfile
    paths: ArtifactPaths
    backup: Path | None
    in_colab: bool
    config_path: Path = Path("scribe/training/configs/smoke-v2.json")
    confirm_paid: bool = False
    dataset: str = "local:frozen-gec-fixture"

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
                if src.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
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

    def run_pipeline(self, stage: str) -> None:
        """Run the same manifest- and safety-gated orchestrator as headless CI."""

        args = [
            "scribe/training/scripts/run_pipeline.py",
            "--config",
            str(self.config_path),
            "--stage",
            stage,
        ]
        if self.confirm_paid:
            args.append("--confirm-paid")
        self.run_step(args, env_extra={"CAREPATH_ARTIFACT_ROOT": str(self.paths.root)})

    def run_soap_pipeline(self) -> None:
        """Run the sibling SOAP orchestrator without duplicating its implementation."""

        soap_profile = "replicate" if self.profile.name == "reproduction" else self.profile.name
        config = Path("scribe/training/configs") / f"soap-{soap_profile}-v1.json"
        if not config.exists() and self.profile.name == "smoke":
            config = Path("scribe/training/configs/soap-smoke-v1.json")
        args = [
            "scribe/training/scripts/run_soap_pipeline.py",
            "--config",
            str(config),
            "--stage",
            "all",
        ]
        env_extra = {"CAREPATH_ARTIFACT_ROOT": str(self.paths.root)}
        if self.confirm_paid:
            env_extra["CAREPATH_CONFIRM_PAID"] = "1"
            args.append("--confirm-paid")
        self.run_step(args, env_extra=env_extra)


def init_stage(profile: str = "smoke", confirm_paid: bool = False) -> StageContext:
    """Resolve profile + Drive backup + artifact paths for a stage notebook."""

    if profile not in PROFILE_CONFIGS:
        raise ValueError(f"profile must be one of {sorted(PROFILE_CONFIGS)}")
    config_path = Path("scribe/training/configs") / PROFILE_CONFIGS[profile]
    config = load_pipeline_config(config_path)
    prof = config.profile
    if prof.paid and not confirm_paid:
        raise SystemExit(
            f"Profile '{prof.name}' can consume paid Colab GPU time. Set "
            "CAREPATH_CONFIRM_PAID=1 only after checking the profile and runtime."
        )
    in_colab = env.in_colab()
    backup = env.setup_backup(in_colab)
    artifact_root = backup / config.run_id if backup else config.artifact_root
    paths = ArtifactPaths(root=artifact_root, suffix=config.suffix)
    print(
        f"profile={prof.name} | single_best={prof.n_best == 1} | seeds={prof.seeds} "
        f"| synthetic={prof.enable_synthetic} | artifacts={paths.root}"
    )
    return StageContext(
        profile=prof,
        paths=paths,
        backup=backup,
        in_colab=in_colab,
        config_path=config_path,
        confirm_paid=confirm_paid,
        dataset=config.dataset,
    )
