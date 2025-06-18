# app/ats/tasks/notifications.py
"""Compat module: app.ats.tasks.notifications

Este módulo reexporta funciones de notificación que permanecen en
`app.tasks`, para mantener compatibilidad con importaciones antiguas
(`from app.ats.tasks.notifications import ...`).
"""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any

# Lista pública de símbolos compatibles
__all__: list[str] = [
    "send_ntfy_notification",
    "send_linkedin_login_link",
    "send_whatsapp_message_task",
    "send_telegram_message_task",
    "send_messenger_message_task",
]

_tasks_module: ModuleType | None = None


def _load_tasks() -> ModuleType:
    """Carga perezosamente `app.tasks` para evitar import circular."""
    global _tasks_module  # noqa: PLW0603
    if _tasks_module is None:
        _tasks_module = importlib.import_module("app.tasks")
    return _tasks_module


# ---------------------------------------------------------------------------
# Wrappers que delegan en las implementaciones reales una vez que app.tasks
# se haya inicializado. De esta forma, app.tasks puede importarnos sin caer
# en un ciclo irrompible.
# ---------------------------------------------------------------------------

def _delegate(fname: str):  # type: ignore
    def _wrapper(*args: Any, **kwargs: Any):  # noqa: ANN401
        func = getattr(_load_tasks(), fname)
        return func(*args, **kwargs)

    _wrapper.__name__ = fname
    _wrapper.__doc__ = f"Compat wrapper for {fname} from app.tasks"
    return _wrapper


# Creamos las funciones públicas
send_ntfy_notification = _delegate("send_ntfy_notification")
send_linkedin_login_link = _delegate("send_linkedin_login_link")
send_whatsapp_message_task = _delegate("send_whatsapp_message_task")
send_telegram_message_task = _delegate("send_telegram_message_task")
send_messenger_message_task = _delegate("send_messenger_message_task")
