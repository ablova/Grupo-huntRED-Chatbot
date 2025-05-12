"""
Módulo de notificaciones para el sistema de huntRED.

Este módulo gestiona todas las notificaciones para los diferentes roles
del sistema, asegurando la comunicación efectiva entre los usuarios
en diferentes puntos del proceso de reclutamiento y ventas.
"""

from .handlers import NotificationHandler, EmailNotificationHandler, WhatsAppNotificationHandler
from .managers import NotificationManager
from .core import send_notification, schedule_notification
from .templates import get_notification_template
# Correcting imports to reference models from app/models.py or correct module
# from .models import Notification, NotificationStatus, NotificationPreference
# Import from the correct location
from app.models import Notification, NotificationStatus, NotificationPreference

__all__ = [
    'NotificationHandler',
    'EmailNotificationHandler',
    'WhatsAppNotificationHandler',
    'NotificationManager',
    'send_notification',
    'schedule_notification',
    'get_notification_template',
    'Notification',
    'NotificationStatus',
    'NotificationPreference',
]
