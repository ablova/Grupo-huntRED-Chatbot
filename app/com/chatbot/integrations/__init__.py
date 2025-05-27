"""
Módulo de integraciones para Grupo huntRED®.
Contiene los conectores y adaptadores para servicios externos.
"""
from .optimized_connectors import (
    DatabaseConnector,
    APIConnector,
    CacheConnector,
    MessageQueueConnector
)

__all__ = [
    'DatabaseConnector',
    'APIConnector',
    'CacheConnector',
    'MessageQueueConnector',
] 