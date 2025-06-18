# app/ats/tasks/utils.py
"""Compat shim: ``app.ats.tasks.utils``

Provides backward-compatibility for historical imports such as::

    from app.ats.tasks.utils import get_business_unit

The real implementation still lives in the legacy monolith
``app/tasks.py``.  Once we extract it to a modern module we can update
imports and delete this shim.
"""
from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any

__all__: list[str] = []

# ----------------------------------------------------------------------------
# Shim estático para evitar ciclo de importación
# ----------------------------------------------------------------------------
# Cuando ``app.tasks`` importa este módulo para obtener ``get_business_unit`` se
# produce un ciclo (tasks -> utils -> tasks). Para romperlo, exponemos un
# wrapper ligero aquí mismo sin depender de la carga completa de ``app.tasks``
# en tiempo de importación. El wrapper delega la llamada real sólo cuando se
# ejecuta.

def get_business_unit(*args: Any, **kwargs: Any):  # type: ignore[override]
    """Delegación perezosa a ``app.tasks.get_business_unit``.

    Se resuelve en tiempo de ejecución para evitar ciclos de importación.
    """
    from importlib import import_module

    module = import_module("app.tasks")
    real = getattr(module, "get_business_unit", None)
    if real is None:
        raise ImportError("get_business_unit no se encontró en app.tasks")
    # Sobrescribimos en globals para futuras llamadas rápidas.
    globals()["get_business_unit"] = real
    return real(*args, **kwargs)

if "get_business_unit" not in __all__:
    __all__.append("get_business_unit")


def _modern_module() -> ModuleType | None:
    try:
        return importlib.import_module("app.ats.utils.tasks")
    except ModuleNotFoundError:
        return None


def _legacy_module() -> ModuleType:
    return importlib.import_module("app.tasks")


def _resolve_module() -> ModuleType:
    return _modern_module() or _legacy_module()


def __getattr__(name: str) -> Any:  # noqa: D401
    tgt = _resolve_module()
    if hasattr(tgt, name):
        return getattr(tgt, name)

    def _lazy_proxy(*args: Any, **kwargs: Any):  # type: ignore[override]
        real = getattr(_resolve_module(), name)
        globals()[name] = real
        return real(*args, **kwargs)

    _lazy_proxy.__name__ = name
    globals()[name] = _lazy_proxy
    if name not in __all__:
        __all__.append(name)
    return _lazy_proxy
