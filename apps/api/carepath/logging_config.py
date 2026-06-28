from __future__ import annotations

import logging
import os
import sys

_CONFIGURED = False


def configure_logging() -> logging.Logger:
    """Attach a single stderr handler to the ``carepath`` logger.

    Idempotent so importing the app under tests or reload does not stack
    duplicate handlers. Level is controlled by ``LOG_LEVEL`` (default INFO).
    """

    global _CONFIGURED
    logger = logging.getLogger("carepath")
    if _CONFIGURED or logger.handlers:
        _CONFIGURED = True
        return logger

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level, logging.INFO))
    logger.propagate = False
    _CONFIGURED = True
    return logger
