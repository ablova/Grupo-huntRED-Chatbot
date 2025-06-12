"""
Módulo de notificaciones para Grupo huntRED®.

Este paquete proporciona un sistema unificado para el envío de notificaciones
a través de múltiples canales (email, WhatsApp, SMS, etc.) con soporte para
plantillas y personalización por unidad de negocio.
"""

# Importaciones principales
from .services.notification_service import NotificationService, notification_service
from .process.manager import ProcessNotificationManager

# Exportar componentes principales
__all__ = [
    'NotificationService',
    'notification_service',
    'ProcessNotificationManager',
]

# Inicialización del logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
