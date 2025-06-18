# app/ats/tasks/onboarding.py
"""Compat shim: ``app.ats.tasks.onboarding``

This module exists solely to keep historic import paths working while we
finish extracting Celery tasks out of the legacy monolith ``app/tasks.py``.

It lazily delegates attribute access to:
1. A modern dedicated module if one is eventually created (e.g.
   ``app.ats.onboarding.tasks``), otherwise
2. The legacy ``app.tasks`` module.

No new business logic should be added here.
"""
from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Any

__all__: list[str] = []  # filled dynamically


def _modern_module() -> ModuleType | None:
    """Return modern onboarding tasks module if it exists."""
    try:
        return importlib.import_module("app.ats.onboarding.tasks")
    except ModuleNotFoundError:
        return None


def _legacy_module() -> ModuleType:
    """Always available fallback: the historical ``app.tasks`` module."""
    return importlib.import_module("app.tasks")


def _resolve_module() -> ModuleType:
    """Prefer modern module, else legacy."""
    return _modern_module() or _legacy_module()


def __getattr__(name: str) -> Any:  # noqa: D401
    """Delegate attribute access.

    Like in the ML shim, if the attribute isn't yet present (typical during
    import cycles), we create a lazy proxy that resolves upon first call.
    """
    target_mod = _resolve_module()

    if hasattr(target_mod, name):
        return getattr(target_mod, name)

    # Build lazy proxy
    def _lazy_proxy(*args: Any, **kwargs: Any):  # type: ignore[override]
        real = getattr(_resolve_module(), name)
        globals()[name] = real  # cache
        return real(*args, **kwargs)

    _lazy_proxy.__name__ = name
    _lazy_proxy.__qualname__ = f"lazy_proxy<{name}>"
    _lazy_proxy.__doc__ = f"Lazy proxy for {target_mod.__name__}.{name} (inserted by shim)."

    globals()[name] = _lazy_proxy
    if name not in __all__:
        __all__.append(name)

    return _lazy_proxy
