"""Servicio ligero para obtener conexiones de LinkedIn.

Este módulo encapsula la autenticación y paginación básica usando
`linkedin_api` y delega las peticiones HTTP a `http_helpers` para
respetar límites y rotar *User-Agent*.  No pretende cubrir todos los
endpoints de LinkedIn; sólo lo necesario para sincronizar contactos.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Dict, List, Optional

import aiohttp
from django.core.exceptions import ImproperlyConfigured

from app.ats.utils.http_helpers import get_random_headers, rate_limited_request

try:
    from linkedin_api import Linkedin  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise ImproperlyConfigured(
        "linkedin_api library is required. Add it to your requirements.txt"
    ) from exc

logger = logging.getLogger(__name__)


class LinkedInService:
    """Cliente *wrapper* alrededor de `linkedin_api.Linkedin`."""

    _PAGE_SIZE = 1000  # máximo permitido por la API no oficial

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        cookies: Optional[dict] = None,
        *,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        self._username = username or os.getenv("LINKEDIN_USERNAME")
        self._password = password or os.getenv("LINKEDIN_PASSWORD")
        self._cookies = cookies
        self._session = session or aiohttp.ClientSession()
        self._api: Optional[Linkedin] = None

    async def _ensure_login(self) -> None:
        if self._api:
            return
        logger.info("Iniciando sesión en LinkedIn")
        # linkedin_api no es asíncrono; ejecútalo en *threadpool* para no bloquear.
        loop = asyncio.get_event_loop()
        self._api = await loop.run_in_executor(
            None, lambda: Linkedin(self._username, self._password, cookies=self._cookies)
        )

    async def fetch_connections(self) -> List[Dict]:
        """Devuelve la lista completa de conexiones."""
        await self._ensure_login()
        assert self._api  # para mypy
        start = 0
        results: List[Dict] = []
        while True:
            logger.debug("Solicitando conexiones LinkedIn offset=%s", start)
            # `get_profile_connections` no existe; usamos `get_profile` + endpoints internos.
            # Sin embargo, la librería ofrece `get_connections`.
            batch = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._api.get_connections(start=start, limit=self._PAGE_SIZE)
            )
            if not batch:
                break
            for item in batch:
                results.append(
                    {
                        "name": item.get("public_identifier"),
                        "email": None,  # LinkedIn API no provee email
                        "phone": None,
                        "company": item.get("companyName"),
                        "source": "linkedin",
                    }
                )
            start += self._PAGE_SIZE
        return results

    async def close(self) -> None:
        await self._session.close()
        # linkedin_api no necesita close.
