"""
Servicio de Background Check para el sistema huntRED.
"""

import logging
import requests
from typing import Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class BackgroundCheckService:
    """
    Servicio para integración con Background Check API.
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'BACKGROUND_CHECK_API_KEY', '')
        self.base_url = getattr(settings, 'BACKGROUND_CHECK_BASE_URL', 'https://api.backgroundcheck.com')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
    
    def create_check(self, person_data: Dict[str, Any], package_type: str = 'basic') -> Dict[str, Any]:
        """
        Crear una nueva verificación de antecedentes.
        """
        try:
            payload = {
                "package": package_type,
                "candidate": {
                    "first_name": person_data.get('first_name'),
                    "last_name": person_data.get('last_name'),
                    "email": person_data.get('email'),
                    "phone": person_data.get('phone'),
                    "ssn": person_data.get('ssn'),
                    "date_of_birth": person_data.get('date_of_birth')
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/checks",
                json=payload
            )
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Error creando Background Check: {e}")
            return {"error": str(e)}
    
    def get_check_status(self, check_id: str) -> Dict[str, Any]:
        """
        Obtener estado de una verificación.
        """
        try:
            response = self.session.get(
                f"{self.base_url}/checks/{check_id}"
            )
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo estado de Background Check: {e}")
            return {"error": str(e)}
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesar webhook de Background Check.
        """
        try:
            check_id = webhook_data.get('check_id')
            status = webhook_data.get('status')
            
            # Actualizar estado en cache
            cache_key = f"background_check_{check_id}"
            cache.set(cache_key, status, timeout=3600)
            
            return {
                "check_id": check_id,
                "status": status,
                "processed": True
            }
        except Exception as e:
            logger.error(f"Error procesando webhook Background Check: {e}")
            return {"error": str(e)}
    
    def get_check_result(self, check_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener resultados de una verificación.
        """
        try:
            response = self.session.get(
                f"{self.base_url}/checks/{check_id}/report"
            )
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo resultados de Background Check: {e}")
            return None 