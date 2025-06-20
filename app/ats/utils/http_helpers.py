# app/ats/utils/http_helpers.py
"""HTTP helper utilities for the whole project.

Centraliza el manejo de User-Agents y de peticiones con control de
rate-limit/back-off para reutilizar en scraping, LinkedIn, iCloud, etc.

Reglas clave:
1. No duplica la lista USER_AGENTS: se reutiliza la definida en
   ``app.models`` siguiendo las reglas globales.
2. Provee funciones simples para obtener headers aleatorios y para
   ejecutar peticiones asíncronas con límite de concurrencia y
   back-off exponencial.
3. Está diseñado para ser *import safe* en contextos síncronos y
   asíncronos.  Si se llama desde código síncrono, se delegará la
   ejecución a un hilo mediante ``sync_to_async`` de Django.
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any, Dict, Optional

import aiohttp
from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings

# Importar la lista canónica de agentes desde app.models
try:
    from app.models import USER_AGENTS as _USER_AGENTS
except Exception:  # pragma: no cover – evita errores de import circular en migraciones
    _USER_AGENTS: list[str] = [
        "Mozilla/5.0",
    ]

__all__ = [
    "get_random_user_agent",
    "get_random_headers",
    "rate_limited_request",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1.  User-Agent helpers
# ---------------------------------------------------------------------------

def get_random_user_agent() -> str:
    """Return a random user-agent string from the canonical list."""
    return random.choice(_USER_AGENTS)


def get_random_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Return headers with a random *User-Agent*.

    Args:
        extra: Headers to merge/override.
    """
    headers: Dict[str, str] = {
        "User-Agent": get_random_user_agent(),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }
    if extra:
        headers.update(extra)
    return headers

# ---------------------------------------------------------------------------
# 2.  Rate-limited request helper
# ---------------------------------------------------------------------------

# Límite global de concurrencia.  Ajustable via settings.HTTP_CONCURRENCY.
_MAX_CONCURRENCY: int = getattr(settings, "HTTP_CONCURRENCY", 8)
_semaphore = asyncio.Semaphore(_MAX_CONCURRENCY)

# Factor de back-off exponencial
_BACKOFF_FACTOR: float = getattr(settings, "HTTP_BACKOFF_FACTOR", 1.6)
_MAX_RETRIES: int = getattr(settings, "HTTP_MAX_RETRIES", 3)
_TIMEOUT: int = getattr(settings, "HTTP_TIMEOUT", 30)


async def _async_request(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    retries: int = _MAX_RETRIES,
    backoff_factor: float = _BACKOFF_FACTOR,
    **kwargs: Any,
) -> aiohttp.ClientResponse:
    """Internal helper that performs a single HTTP request with retries."""
    attempt = 0
    while True:
        try:
            async with _semaphore:
                async with session.request(method.upper(), url, timeout=_TIMEOUT, **kwargs) as resp:
                    if resp.status in {429, 500, 502, 503, 504} and attempt < retries:
                        raise aiohttp.ClientResponseError(
                            resp.request_info, resp.history, status=resp.status, message="retryable", headers=resp.headers
                        )
                    resp.raise_for_status()
                    return resp
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            attempt += 1
            if attempt > retries:
                logger.error("HTTP %s %s failed after %s attempts: %s", method, url, attempt, exc)
                raise
            sleep_for = backoff_factor ** attempt + random.random()
            logger.warning("HTTP %s %s failed (%s). Retrying in %.2fs (attempt %s/%s)", method, url, exc, sleep_for, attempt, retries)
            await asyncio.sleep(sleep_for)


async def rate_limited_request(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    retries: int = _MAX_RETRIES,
    **kwargs: Any,
) -> aiohttp.ClientResponse:
    """Perform an HTTP request (GET/POST/etc.) with global concurrency
    control and exponential back-off retries.

    Si se llama desde un contexto *sync* se utiliza `async_to_sync`.
    """
    if asyncio.get_event_loop().is_running():
        return await _async_request(session, method, url, retries=retries, **kwargs)
    # Fallback para ámbitos síncronos (p.ej. tests)
    return async_to_sync(_async_request)(session, method, url, retries=retries, **kwargs)
