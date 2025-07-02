# app/ats/integrations/notifications/channels/whatsapp.py
"""
DEPRECATED: Este módulo legacy ya no se utiliza. 

Todas las notificaciones de WhatsApp se envían mediante
`app.ats.integrations.channels.whatsapp.whatsapp.WhatsAppHandler`, que
se comunica directamente con la API oficial de WhatsApp Business.
"""

import logging
from app.ats.security.exceptions import SecurityPolicyViolation

logger = logging.getLogger(__name__)

# Definir constantes de seguridad
SECURITY_MSG = "CANAL DESHABILITADO: Este canal está deshabilitado por políticas de seguridad."
ALTERNATIVE_PATH = "app/ats/integrations/channels/whatsapp/whatsapp.py"

class WhatsAppNotificationChannel:
    """
    DESHABILITADO - Canal de notificación WhatsApp obsoleto.
    
    Este canal ha sido deshabilitado por políticas de seguridad.
    Usar la implementación oficial de WhatsApp Business API en:
    app/ats/integrations/channels/whatsapp/whatsapp.py
    """
    
    def __init__(self, business_unit):
        """Constructor deshabilitado."""
        logger.error(
            f"{SECURITY_MSG} Usar la implementación autorizada en: {ALTERNATIVE_PATH}"
        )
        raise SecurityPolicyViolation(f"{SECURITY_MSG} Ver: {ALTERNATIVE_PATH}")
        
    def send_notification(self, message, options=None, priority=0):
        """Método deshabilitado."""
        logger.error(
            f"{SECURITY_MSG} Usar la implementación autorizada en: {ALTERNATIVE_PATH}"
        )
        raise SecurityPolicyViolation(f"{SECURITY_MSG} Ver: {ALTERNATIVE_PATH}")

# Garantizar que el archivo no pueda ser importado inadvertidamente
if __name__ != "__main__":
    logger.warning(
        f"Intento de importación del canal deshabilitado. "
        f"Usar la implementación autorizada en: {ALTERNATIVE_PATH}"
    )


class SecurityError(Exception):
    """Error de seguridad por intento de uso de integración prohibida."""
    pass