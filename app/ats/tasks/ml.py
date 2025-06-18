# app/ats/tasks/ml.py
"""Compat shim: ``app.ats.tasks.ml``

Historically, ML-related Celery tasks lived in the monolithic
``app/tasks.py`` module.  This shim forwards *any* attribute access to
that legacy module so that legacy imports (e.g. ``from app.ats.tasks.ml
import train_ml_task``) continue to work while we progressively migrate
tasks to standalone files.
"""
from __future__ import annotations

import importlib
from typing import Any

__all__: list[str] = []  # populated dynamically once the real module is loaded


def _real_tasks_module():
    """Return the fully-initialised ``app.tasks`` module.

    We fetch it from ``sys.modules`` if it is *already* imported (to avoid
    circular-import issues).  Otherwise we import it lazily.
    """
    import sys

    if (mod := sys.modules.get("app.tasks")) is not None and getattr(mod, "__spec__", None) is not None:
        return mod  # either fully loaded or still initialising but usable

    return importlib.import_module("app.tasks")


def __getattr__(name: str) -> Any:  # noqa: D401
    """Return attribute from legacy ``app.tasks``.

    If the attribute is not yet present (common during circular imports), we
    create a *lazy proxy* so that import-time references succeed without
    immediately evaluating the real callable.  The proxy will resolve the
    real implementation upon first call.
    """
    tasks_mod = _real_tasks_module()

    if hasattr(tasks_mod, name):
        return getattr(tasks_mod, name)

    # Build a lazy proxy so that `from app.ats.tasks.ml import foo` works even
    # while `app.tasks` is still being initialised.
    def _lazy_proxy(*args: Any, **kwargs: Any):  # type: ignore[override]
        real = getattr(_real_tasks_module(), name)
        globals()[name] = real  # cache for subsequent accesses
        return real(*args, **kwargs)

    _lazy_proxy.__name__ = name
    _lazy_proxy.__qualname__ = f"lazy_proxy<{name}>"
    _lazy_proxy.__doc__ = f"Lazy proxy for app.tasks.{name} (inserted by shim)."

    # Expose via module namespace and __all__
    globals()[name] = _lazy_proxy
    if name not in __all__:
        __all__.append(name)
    return _lazy_proxy
