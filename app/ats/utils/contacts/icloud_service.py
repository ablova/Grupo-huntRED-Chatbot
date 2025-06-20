"""Servicio de integración con iCloud para extracción de contactos.

Depende de *pyicloud-ipd* para la conexión.  Maneja 2FA de forma
asíncrona pidiendo el código mediante ConfigAPI (o falla con un error
claramente identificable).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional

try:
    from pyicloud_ipd import PyiCloudService  # type: ignore
except ImportError:  # pragma: no cover – la lib puede no estar instalada aún
    PyiCloudService = None  # type: ignore[misc,assignment]

from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class ICloudService:
    """Cliente asíncrono *wrapper* alrededor de **pyicloud-ipd**."""

    def __init__(self, email: str, password: str, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        if PyiCloudService is None:
            raise ImproperlyConfigured("pyicloud-ipd not installed. Add it to your requirements.txt")
        self._loop = loop or asyncio.get_event_loop()
        self._client = PyiCloudService(email, password, verify=True)

    # ------------------------------------------------------------------
    # 2FA helpers
    # ------------------------------------------------------------------
    async def ensure_authenticated(self) -> None:
        if not self._client.requires_2fa:
            return
        logger.info("iCloud requires 2FA code – waiting for user input via ConfigAPI")
        from app.models import ConfigAPI  # local import to avoid early Django setup issues

        code: Optional[str] = None
        for _ in range(10):
            await asyncio.sleep(6)
            code = ConfigAPI.get_optional("ICLOUD_2FA_CODE")  # type: ignore[attr-defined]
            if code:
                break
        if not code:
            raise RuntimeError("No 2FA code available in ConfigAPI – aborting iCloud login")
        self._client.validate_2fa_code(code)
        if not self._client.is_trusted_session:
            raise RuntimeError("2FA validation failed for iCloud")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def fetch_contacts(self) -> List[Dict]:
        await self.ensure_authenticated()
        contacts: List[Dict] = []
        for raw in self._client.contacts.all():
            contacts.append(
                {
                    "name": f"{raw.get('firstName', '')} {raw.get('lastName', '')}".strip(),
                    "email": (raw.get("emails") or [{}])[0].get("value", ""),
                    "phone": (raw.get("phones") or [{}])[0].get("value", ""),
                    "company": raw.get("companyName", ""),
                    "source": "icloud",
                }
            )
        return contacts

    async def close(self) -> None:
        # pyicloud-ipd no necesita explícito close, placeholder para simetría
        pass
