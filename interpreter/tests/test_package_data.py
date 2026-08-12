"""Every runtime data file must be declared as package data.

The Docker image installs this package for real (`pip install ./interpreter`),
not editable, so a data file that is not declared simply does not exist in
production. Tests run from the source tree and cannot see the difference.

That is not hypothetical: `providers/demo_scenario.json` was undeclared, so
`PROVIDER_MODE=demo` and the public demo's scripted sample both returned 502 on
the deployed Space while every local test passed.
"""

from __future__ import annotations

import fnmatch
import tomllib
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PACKAGE_ROOT / "app"
PYPROJECT = PACKAGE_ROOT / "pyproject.toml"

# Not read at runtime, so not required in the wheel.
IGNORED_SUFFIXES = {".py", ".pyc", ".pyo"}
IGNORED_PARTS = {"__pycache__", ".pytest_cache"}


def _declared_globs() -> list[str]:
    config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return config["tool"]["setuptools"]["package-data"]["app"]


def _runtime_data_files() -> list[str]:
    files = []
    for path in sorted(APP_DIR.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix in IGNORED_SUFFIXES:
            continue
        if IGNORED_PARTS & set(path.relative_to(APP_DIR).parts):
            continue
        files.append(path.relative_to(APP_DIR).as_posix())
    return files


class PackageDataTests(unittest.TestCase):
    def test_every_data_file_is_declared(self) -> None:
        globs = _declared_globs()
        undeclared = [
            name
            for name in _runtime_data_files()
            if not any(fnmatch.fnmatch(name, pattern) for pattern in globs)
        ]
        self.assertEqual(
            undeclared,
            [],
            "these files ship in the source tree but not in the installed "
            f"package; add a glob to [tool.setuptools.package-data] in {PYPROJECT.name}",
        )

    def test_the_demo_scenario_is_declared(self) -> None:
        """Named explicitly: this is the one that broke production."""
        globs = _declared_globs()
        self.assertTrue(
            any(fnmatch.fnmatch("providers/demo_scenario.json", g) for g in globs)
        )

    def test_every_declared_glob_still_matches_something(self) -> None:
        """A glob that matches nothing is a rename waiting to be noticed late."""
        names = _runtime_data_files()
        for pattern in _declared_globs():
            with self.subTest(pattern=pattern):
                self.assertTrue(
                    any(fnmatch.fnmatch(name, pattern) for name in names),
                    f"{pattern} matches no file under app/",
                )


if __name__ == "__main__":
    unittest.main()
