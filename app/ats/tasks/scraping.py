# app/ats/tasks/scraping.py
"""Compat module: app.ats.tasks.scraping

Shims that proxy scraping-related Celery tasks to their real
implementations in ``app.tasks``.  This keeps legacy imports working
while we migrate away from the monolithic ``app/tasks.py`` file.
"""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any, Callable, List

__all__: List[str] = [
    "ejecutar_scraping",
    "retrain_ml_scraper",
    "verificar_dominios_scraping",
    "procesar_scraping_dominio",
    "procesar_sublinks_task",
    "execute_ml_and_scraping",
    "execute_email_scraper",
    "process_cv_emails_task",
]

_tasks_mod: ModuleType | None = None


def _load_tasks() -> ModuleType:
    """Lazy-import ``app.tasks`` to avoid circular deps."""
    global _tasks_mod  # noqa: PLW0603
    if _tasks_mod is None:
        _tasks_mod = importlib.import_module("app.tasks")
    return _tasks_mod


def _delegate(func_name: str) -> Callable[..., Any]:  # type: ignore[name-defined]
    def _wrapper(*args: Any, **kwargs: Any):  # noqa: ANN401
        real_func = getattr(_load_tasks(), func_name)
        return real_func(*args, **kwargs)

    _wrapper.__name__ = func_name
    _wrapper.__doc__ = f"Compat wrapper for {func_name} from app.tasks"
    return _wrapper

# Generate wrappers
for _fname in __all__:
    globals()[_fname] = _delegate(_fname)  # type: ignore[index]
