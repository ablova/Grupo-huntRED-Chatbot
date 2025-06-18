# app/ats/tasks/base.py
"""Compatibilidad - `app.ats.tasks.base`

Este módulo existía en versiones anteriores y ofrecía utilidades
compartidas para tareas Celery como el decorador `with_retry`.
Fue movido a `app.ats.chatbot.middleware.message_retry` pero varios
módulos siguen importándolo.  Se reexpone aquí para evitar errores de
importación mientras se completa la refactorización.
"""

from __future__ import annotations

import logging
from celery import shared_task
from typing import Callable

from app.ats.chatbot.middleware.message_retry import MessageRetry

logger = logging.getLogger(__name__)

# Re-exportar el decorador principal

def with_retry(platform_param: str | None = None) -> Callable:
    """Alias de compatibilidad para `MessageRetry.with_retry`."""
    return MessageRetry.with_retry(platform_param)


@shared_task
def add(x: int | float, y: int | float):  # noqa: ANN001
    """Tarea Celery de prueba equivalente a la versión original."""
    return x + y


__all__ = ["with_retry", "add"]
