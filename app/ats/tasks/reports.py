# app/ats/tasks/reports.py
"""Compat shim: ``app.ats.tasks.reports``

Historically, reporting Celery tasks continue to live in the legacy
``app/tasks.py`` monolith.  This thin wrapper delegates every attribute
access to that module (or to a modern specialised module once it exists)
so that import paths such as::

    from app.ats.tasks.reports import generate_weekly_report_task

keep working while we refactor.
"""
from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any

__all__: list[str] = []


def _modern_module() -> ModuleType | None:
    """Return new implementation module if available."""
    try:
        return importlib.import_module("app.ats.reports.tasks")
    except ModuleNotFoundError:
        return None


def _legacy_module() -> ModuleType:
    return importlib.import_module("app.tasks")


def _resolve_module() -> ModuleType:
    return _modern_module() or _legacy_module()


def __getattr__(name: str) -> Any:  # noqa: D401
    target = _resolve_module()
    if hasattr(target, name):
        return getattr(target, name)

    # lazy proxy to break circular import
    def _lazy_proxy(*args: Any, **kwargs: Any):
        real = getattr(_resolve_module(), name)
        globals()[name] = real
        return real(*args, **kwargs)

    _lazy_proxy.__name__ = name
    globals()[name] = _lazy_proxy
    if name not in __all__:
        __all__.append(name)
    return _lazy_proxy
