import json
import logging
from datetime import datetime
from .models import IntegrationLog
from .constants import EVENT_TYPES

logger = logging.getLogger(__name__)

def log_integration_event(integration, event_type, payload=None, error=None):
    """
    Registra un evento de integración en el log
    """
    try:
        IntegrationLog.objects.create(
            integration=integration,
            event_type=event_type,
            payload=json.dumps(payload) if payload else None,
            error=str(error) if error else None
        )
    except Exception as e:
        logger.error(f"Error al registrar evento de integración: {str(e)}")

def format_webhook_payload(payload):
    """
    Formatea el payload del webhook para su almacenamiento
    """
    if isinstance(payload, dict):
        return json.dumps(payload)
    return payload

def parse_webhook_payload(payload):
    """
    Parsea el payload del webhook desde su formato almacenado
    """
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return payload
    return payload

def get_integration_config(integration, key, default=None):
    """
    Obtiene el valor de una configuración de integración
    """
    try:
        config = integration.configs.get(key=key)
        return config.value
    except IntegrationConfig.DoesNotExist:
        return default

def set_integration_config(integration, key, value, is_secret=False):
    """
    Establece el valor de una configuración de integración
    """
    config, created = integration.configs.get_or_create(
        key=key,
        defaults={
            'value': value,
            'is_secret': is_secret
        }
    )
    if not created:
        config.value = value
        config.is_secret = is_secret
        config.save()
    return config 