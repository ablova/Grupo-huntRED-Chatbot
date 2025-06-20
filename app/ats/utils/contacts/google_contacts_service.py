"""Servicio Google Contacts basado en la API People v1.

Requiere `google-api-python-client` y `google-auth` instalados.
Se asume que el token OAuth2 (access+refresh) se almacena en el modelo
`ConfigAPI` bajo la clave `GOOGLE_CONTACTS_TOKEN` o se pasa como dict al
constructor.

Cada item devuelto cumple el contrato estándar:
    name, email, phone, company, position, linkedin_url, source
Otros campos se incluyen en `metadata`.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, List, Optional

import aiohttp
from django.core.exceptions import ImproperlyConfigured

from app.models import ConfigAPI  # type: ignore[attr-defined]

from .base_service import BaseContactService

logger = logging.getLogger(__name__)

try:
    from google.oauth2.credentials import Credentials  # type: ignore
    from googleapiclient.discovery import build  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise ImproperlyConfigured(
        "google-api-python-client and google-auth are required for GoogleContactsService"
    ) from exc

SCOPES = [
    "https://www.googleapis.com/auth/contacts.readonly",
]


class GoogleContactsService(BaseContactService):
    """Obtiene contactos del People API usando credenciales OAuth."""

    _PAGE_SIZE = 1000

    def __init__(self, token_key: str | None = None, *, session: Optional[aiohttp.ClientSession] = None, **kwargs):
        super().__init__(**kwargs)
        self._session = session or aiohttp.ClientSession()
        self._token_data: Optional[dict] = None

        # Intentar recuperar token JSON del modelo ConfigAPI si no se pasa.
        token_key = token_key or "GOOGLE_CONTACTS_TOKEN"
        self._token_data = ConfigAPI.get_optional(token_key)  # type: ignore[attr-defined]
        if not self._token_data:
            raise ImproperlyConfigured(
                f"No OAuth token data found for Google Contacts under ConfigAPI key '{token_key}'"
            )

        self._creds = Credentials.from_authorized_user_info(json.loads(self._token_data), SCOPES)
        self._service = None

    async def _ensure_service(self) -> None:
        if self._service:
            return
        loop = asyncio.get_event_loop()
        self._service = await loop.run_in_executor(None, lambda: build("people", "v1", credentials=self._creds))

    async def fetch_contacts(self) -> List[Dict]:
        await self._ensure_service()
        assert self._service is not None
        people: List[Dict] = []

        def _call_api(page_token: Optional[str] = None):
            kwargs = {
                "pageSize": self._PAGE_SIZE,
                "personFields": "names,emailAddresses,phoneNumbers,organizations,photos,birthdays",
            }
            if page_token:
                kwargs["pageToken"] = page_token
            return (
                self._service.people()
                .connections()
                .list(resourceName="people/me", **kwargs)  # type: ignore[arg-type]
                .execute()
            )

        loop = asyncio.get_event_loop()
        page_token: Optional[str] = None
        while True:
            resp = await loop.run_in_executor(None, _call_api, page_token)
            for person in resp.get("connections", []):
                names = person.get("names", [{}])
                orgs = person.get("organizations", [{}])
                emails = person.get("emailAddresses", [{}])
                phones = person.get("phoneNumbers", [{}])

                contact: Dict = {
                    "name": names[0].get("displayName"),
                    "email": emails[0].get("value"),
                    "phone": phones[0].get("value"),
                    "company": orgs[0].get("name"),
                    "position": orgs[0].get("title"),
                    "linkedin_url": None,
                    "source": "google_contacts",
                    "metadata": {
                        "photo": (person.get("photos", [{}])[0].get("url")),
                        "birthday": (person.get("birthdays", [{}])[0].get("text")),
                    },
                }
                people.append(contact)

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        logger.info("Google Contacts: %s contactos recuperados", len(people))
        return people

    async def close(self) -> None:  # noqa: D401
        await self._session.close()
