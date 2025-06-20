"""Definición de la interfaz común para los servicios de contactos.

Cada servicio (iCloud, LinkedIn, CSV, Google, etc.) debe heredar de
`BaseContactService` para garantizar un contrato uniforme.
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List


class BaseContactService(ABC):
    """API mínima que todos los *providers* de contactos deben exponer."""

    def __init__(self, **kwargs):  # noqa: D401 – keep kwargs flexible
        self._closed = False
        super().__init__()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):  # noqa: D401
        await self.close()

    # ------------------------------------------------------------------
    # Métodos obligatorios
    # ------------------------------------------------------------------
    @abstractmethod
    async def fetch_contacts(self) -> List[Dict]:
        """Devuelve una lista de dicts con llaves: name, email, phone, company, source."""

    @abstractmethod
    async def close(self) -> None:  # noqa: D401
        """Libera recursos (conexiones HTTP, archivos, etc.)."""

    # ------------------------------------------------------------------
    # Utilidad opcional
    # ------------------------------------------------------------------
    async def _gather(self, *aws):
        """Ejecuta *awaitables* en paralelo con manejo de cancelación uniforme."""
        return await asyncio.gather(*aws, return_exceptions=False)
