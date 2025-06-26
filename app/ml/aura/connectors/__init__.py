"""
Connectors del Sistema Aura

Este módulo implementa los conectores para integrar datos externos
y enriquecer la red de relaciones profesionales.
"""

from .linkedin_connector import LinkedInConnector
from .icloud_connector import iCloudConnector
from .contacts_connector import ContactsConnector

__all__ = [
    'LinkedInConnector',
    'iCloudConnector', 
    'ContactsConnector'
] 