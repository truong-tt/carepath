"""Tiny CLI helpers shared by the ``scripts/gec/*`` entrypoints."""

from __future__ import annotations

import sys


def configure_stdout() -> None:
    """Force UTF-8 stdout/stderr so Vietnamese output never crashes on cp1252.

    Windows consoles default to a legacy code page; printing Vietnamese JSON would
    raise ``UnicodeEncodeError``. Colab/Linux are already UTF-8, so this is a no-op
    there. Best-effort: silently skipped on stream types without ``reconfigure``.
    """

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
