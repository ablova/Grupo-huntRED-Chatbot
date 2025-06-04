"""
Submódulo de referencias para el chatbot de Grupo huntRED®.
Maneja la captura, solicitud, procesamiento y conversión de referencias.
"""

from .references import ReferenceManager
from .notifications import ReferenceNotificationManager
from .utils import ReferenceUtils

__all__ = ['ReferenceManager', 'ReferenceNotificationManager', 'ReferenceUtils'] 