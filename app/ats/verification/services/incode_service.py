"""
Servicio de integración con INCODE para verificación de identidad.
"""

import logging
import requests
from typing import Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class INCODEService:
    """
    Servicio para integración con INCODE API.
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'INCODE_API_KEY', '')
        self.base_url = getattr(settings, 'INCODE_BASE_URL', 'https://api.incode.com')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
    
    def create_session(self, flow_id: str, user_id: str) -> Dict[str, Any]:
        """
        Crear una nueva sesión de verificación.
        """
        try:
            payload = {
                "flowId": flow_id,
                "configurationId": "default",
                "userTrackingCode": user_id,
                "metadata": {
                    "userId": user_id
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/omni/start",
                json=payload
            )
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Error creando sesión INCODE: {e}")
            return {"error": str(e)}
    
    def verify_identity(self, session_id: str) -> Dict[str, Any]:
        """
        Verificar identidad usando la sesión existente.
        """
        try:
            response = self.session.get(
                f"{self.base_url}/omni/get/score/{session_id}"
            )
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Error verificando identidad: {e}")
            return {"error": str(e)}
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar webhook de INCODE.
        """
        try:
            session_id = webhook_data.get('sessionId')
            status = webhook_data.get('status')
            
            # Actualizar estado en cache
            cache_key = f"incode_session_{session_id}"
            cache.set(cache_key, status, timeout=3600)
            
            return {
                "session_id": session_id,
                "status": status,
                "processed": True
            }
        except Exception as e:
            logger.error(f"Error procesando webhook INCODE: {e}")
            return {"error": str(e)}
    
    def get_session_status(self, session_id: str) -> Optional[str]:
        """
        Obtener estado de una sesión.
        """
        cache_key = f"incode_session_{session_id}"
        return cache.get(cache_key) 