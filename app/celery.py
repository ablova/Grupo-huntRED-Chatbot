# app/celery.py
"""Compatibility shim for legacy imports of `app.celery`.

Historically some parts of the codebase imported the Celery application
from `app.celery`.  The canonical Celery application lives in
`ai_huntred.celery_app` (see global rules).  This module simply imports
and re-exports that `app` instance so legacy imports keep working
without changes.

Do NOT add new logic here.  New code should import the Celery instance
from `ai_huntred.celery_app` directly.
"""
from __future__ import annotations

import importlib
import logging
from types import ModuleType
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

_app = None  # Cached Celery app instance

# Try to load the canonical Celery app from ai_huntred.celery_app
try:
    _celery_mod: ModuleType = importlib.import_module("ai_huntred.celery_app")
    _app = getattr(_celery_mod, "app", None)
    if _app is None:
        raise AttributeError("'ai_huntred.celery_app' does not define 'app'")
except Exception as exc:  # Broad except on purpose to fall back gracefully
    logger.warning(
        "Falling back to creating a new Celery app because canonical one could not be imported: %s",
        exc,
    )
    # Create a minimal Celery instance so that import does not fail, but log that this is undesirable.
    from celery import Celery

    _app = Celery("app")

# Re-export for `from app.celery import app`
app = _app

# Clean up namespace to avoid leaking private vars
if not TYPE_CHECKING:
    del _app
    del importlib
    del ModuleType
    del TYPE_CHECKING
    del logger
