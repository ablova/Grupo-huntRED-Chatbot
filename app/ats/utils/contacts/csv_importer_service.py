"""Servicio para importar contactos desde un CSV.

Se espera que el archivo contenga cabeceras incluyendo al menos uno de
los siguientes campos:
    - name / first_name & last_name
    - email
    - phone
    - company
Cualquier columna extra se ignora.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .base_service import BaseContactService

logger = logging.getLogger(__name__)


class CSVImporterService(BaseContactService):
    """Lee un archivo CSV y devuelve contactos normalizados."""

    def __init__(self, file_path: str | Path, *, encoding: str = "utf-8-sig", **kwargs):
        super().__init__(**kwargs)
        self._path = Path(file_path)
        self._encoding = encoding
        if not self._path.exists():
            raise FileNotFoundError(self._path)

    async def fetch_contacts(self) -> List[Dict]:
        logger.info("Leyendo contactos desde CSV %s", self._path)
        contacts: List[Dict] = []
        with self._path.open("r", encoding=self._encoding, newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                contact: Dict[str, Optional[str]] = {
                    "name": (row.get("name") or (f"{row.get('first_name', '')} {row.get('last_name', '')}".strip())) or None,
                    "email": row.get("email") or row.get("Email Address"),
                    "phone": row.get("phone"),
                    "company": row.get("company"),
                    "source": "csv",
                }
                if any(contact.values()):
                    contacts.append(contact)  # type: ignore[arg-type]
        logger.info("CSV %s producido %s contactos", self._path, len(contacts))
        return contacts

    async def close(self) -> None:  # noqa: D401 – nothing to do
        pass
