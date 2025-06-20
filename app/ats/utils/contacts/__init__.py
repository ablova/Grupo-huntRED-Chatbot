"""Sub‐package for contacto sync utilities (iCloud & LinkedIn).

Exporta las clases principales para que puedan importarse de forma
compacta:

    from app.ats.utils.contacts import ContactSync
"""
from typing import Dict, Type

from .base_service import BaseContactService  # noqa: F401
from .icloud_service import ICloudService  # noqa: F401
from .linkedin_service import LinkedInService  # noqa: F401
from .csv_importer_service import CSVImporterService  # noqa: F401
from .google_contacts_service import GoogleContactsService  # noqa: F401

# Registro de proveedores disponibles.  "source" -> clase de servicio
PROVIDERS: Dict[str, Type[BaseContactService]] = {
    "icloud": ICloudService,
    "linkedin": LinkedInService,
    "csv": CSVImporterService,
    "google_contacts": GoogleContactsService,
}

# Exportar orquestador (se define más abajo para evitar import circular)
from .contact_sync import ContactSync  # noqa: E402,F401
