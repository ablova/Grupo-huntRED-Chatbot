
# FIXED: Clase base genérica para handlers - v2025.05.19
import asyncio
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class BaseHandler:
    """Clase base para todos los handlers de canales."""
    
    def __init__(self):
        self.handler_type = "base"
        self.config = {
            "rate_limit": 20,  # mensajes por minuto
            "retry_attempts": 3,
            "timeout": 30  # segundos
        }
    
    async def send_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """Método base para enviar un mensaje."""
        logger.warning(f"[MOCK] BaseHandler.send_message llamado para {user_id}")
        return {"success": False, "error": "Método no implementado en la clase base"}
    
    async def process_incoming(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un mensaje entrante."""
        logger.warning(f"[MOCK] BaseHandler.process_incoming llamado")
        return {"success": False, "error": "Método no implementado en la clase base"}
    
    async def check_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Verifica condiciones específicas del canal."""
        # Por defecto, no hay condiciones específicas al canal
        return True
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Obtiene el perfil de un usuario en el canal."""
        logger.warning(f"[MOCK] BaseHandler.get_user_profile llamado para {user_id}")
        return {"user_id": user_id, "name": "Usuario Genérico", "channel": self.handler_type}
    
    async def validate_user(self, user_id: str) -> bool:
        """Valida que un usuario exista en el canal."""
        logger.warning(f"[MOCK] BaseHandler.validate_user llamado para {user_id}")
        return True
