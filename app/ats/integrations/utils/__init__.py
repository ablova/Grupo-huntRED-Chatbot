# app/ats/integrations/utils/__init__.py
"""
Utilidades para integraciones.
"""

# Importaciones necesarias
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def log_integration_event(integration, event_type, payload=None, error=None):
    """
    Registra un evento de integración en el log
    """
    try:
        from app.ats.integrations.models import IntegrationLog
        
        IntegrationLog.objects.create(
            integration=integration,
            event_type=event_type,
            payload=json.dumps(payload) if payload else None,
            error=str(error) if error else None
        )
    except Exception as e:
        logger.error(f"Error al registrar evento de integración: {str(e)}")

# Exportar otras utilidades que podrían ser necesarias
# Nota: Estas funciones deben estar definidas en otros módulos del paquete
# y ser importadas explícitamente aquí si son necesarias

# Importar utilidades de webhook
from .webhook_utils import format_webhook_payload, parse_webhook_payload
# Importar utilidades de configuración
from .config_utils import get_integration_config, set_integration_config, delete_integration_config

# Asegurar que todas las funciones estén disponibles para importación
__all__ = [
    'log_integration_event',
    'format_webhook_payload',
    'parse_webhook_payload',
    'get_integration_config',
    'set_integration_config',
    'delete_integration_config'
]