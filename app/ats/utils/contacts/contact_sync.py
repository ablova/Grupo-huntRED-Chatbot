"""Orquestador de sincronización de contactos.

Uso:
    await ContactSync.run(source="google_contacts", bu="huntred")

Expone además la tarea Celery `sync_contacts_task` y un *management
command* (`manage.py sync_contacts`) para ejecución manual.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Sequence

import phonenumbers
from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone
from rapidfuzz import fuzz, process as fuzz_process

from app.models import Person  # type: ignore[attr-defined]

from . import PROVIDERS
from .base_service import BaseContactService

logger = logging.getLogger(__name__)


class ContactSync:
    """Clase estática que coordina importaciones y persistencia."""

    @staticmethod
    async def run(source: str, *, bu: str, **provider_kwargs: Any) -> None:
        if source not in PROVIDERS:
            raise ValueError(f"Fuente '{source}' no está registrada en PROVIDERS")

        svc_cls = PROVIDERS[source]
        async with svc_cls(**provider_kwargs) as service:  # type: ignore[arg-type]
            contacts = await service.fetch_contacts()

        logger.info("%s contactos obtenidos desde %s", len(contacts), source)

        # Normalizar y guardar
        normalized = [ContactSync._normalize(c) for c in contacts]
        await ContactSync._bulk_upsert(normalized, bu)
        logger.info("Sincronización completada: %s contactos procesados", len(normalized))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize(contact: Dict[str, Any]) -> Dict[str, Any]:
        # Limpieza básica
        contact = contact.copy()
        phone_raw = contact.get("phone")
        if phone_raw:
            try:
                phone_parsed = phonenumbers.parse(phone_raw, None)
                contact["phone"] = phonenumbers.format_number(
                    phone_parsed, phonenumbers.PhoneNumberFormat.E164
                )
            except Exception:
                logger.debug("No se pudo normalizar teléfono '%s'", phone_raw)
        email = (contact.get("email") or "").lower().strip() or None
        contact["email"] = email
        name = (contact.get("name") or "").strip()
        contact["name"] = name
        return contact

    @staticmethod
    async def _bulk_upsert(contacts: Sequence[Dict[str, Any]], bu: str) -> None:
        to_create: List[Person] = []
        to_update: List[Person] = []

        for data in contacts:
            existing = await ContactSync._find_existing(data)
            if existing:
                changed = False
                if data.get("phone") and not existing.phone:
                    existing.phone = data["phone"]
                    changed = True
                if data.get("email") and not existing.email:
                    existing.email = data["email"]
                    changed = True
                if data.get("position"):
                    existing.metadata.setdefault("position", data["position"])
                    changed = True
                if data.get("linkedin_url"):
                    existing.metadata.setdefault("linkedin_url", data["linkedin_url"])
                    changed = True
                if changed:
                    existing.metadata["last_updated"] = timezone.now().isoformat()
                    to_update.append(existing)
            else:
                person = Person(
                    nombre=data.get("name") or "",
                    email=data.get("email"),
                    phone=data.get("phone"),
                    metadata={
                        "company": data.get("company"),
                        "position": data.get("position"),
                        "linkedin_url": data.get("linkedin_url"),
                        "source": data.get("source"),
                    },
                )
                to_create.append(person)

        if to_create:
            await sync_to_async(Person.objects.bulk_create)(to_create, batch_size=1000)
        if to_update:
            fields = ["phone", "email", "metadata"]
            await sync_to_async(Person.objects.bulk_update)(to_update, fields, batch_size=500)

    # ------------------------------------------------------------------
    @staticmethod
    async def _find_existing(data: Dict[str, Any]) -> Optional[Person]:
        email = data.get("email")
        phone = data.get("phone")
        linkedin_url = data.get("linkedin_url")
        query = Person.objects.all()
        if email:
            person = await sync_to_async(query.filter(email__iexact=email).first)()
            if person:
                return person
        if phone:
            person = await sync_to_async(query.filter(phone=phone).first)()
            if person:
                return person
        if linkedin_url:
            person = await sync_to_async(query.filter(metadata__linkedin_url=linkedin_url).first)()
            if person:
                return person
        # Fallback fuzzy match by name + company
        name = data.get("name")
        company = (data.get("company") or "").lower()
        if not name:
            return None
        possibles = await sync_to_async(list)(query.filter(nombre__iexact=name))
        for p in possibles:
            comp = (p.metadata.get("company", "") or "").lower()
            if comp and company and fuzz.ratio(comp, company) > 90:
                return p
        return None


# ----------------------------------------------------------------------
# Celery integration (if Celery is configured)
# ----------------------------------------------------------------------
try:
    from celery import shared_task  # type: ignore

    @shared_task
    def sync_contacts_task(source: str, bu: str, **provider_kwargs: Any):  # noqa: D401
        loop = asyncio.get_event_loop()
        loop.run_until_complete(ContactSync.run(source, bu=bu, **provider_kwargs))

except ImportError:  # pragma: no cover
    logger.warning("Celery no instalado; la tarea sync_contacts_task no estará disponible.")
