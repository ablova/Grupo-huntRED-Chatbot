from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging
from django.core.cache import cache
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger('integrations')

class BaseHandler(ABC):
    """
    Clase base para todos los handlers de mensajes.
    Proporciona funcionalidad común para el manejo de mensajes en diferentes canales.
    """
    
    def __init__(self):
        self.rate_limit = self._get_rate_limit()
        self.cache_timeout = 600  # 10 minutos por defecto
        
    def _get_rate_limit(self) -> float:
        """
        Obtiene el límite de tasa para el canal
        """
        return 1.0  # 1 segundo por defecto
        
    @abstractmethod
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un mensaje entrante
        """
        pass
        
    @abstractmethod
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Envía un mensaje
        """
        pass
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja un mensaje con reintentos automáticos
        """
        try:
            # Procesar el mensaje
            response = await self.process_message(message)
            
            # Enviar respuesta si es necesario
            if response.get('should_send', True):
                await self.send_message(response)
                
            return response
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }
            
    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja un webhook entrante
        """
        try:
            # Extraer mensaje del payload
            message = self._extract_message_from_payload(payload)
            
            # Procesar mensaje
            return await self.handle_message(message)
            
        except Exception as e:
            logger.error(f"Error procesando webhook: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }
            
    def _extract_message_from_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae el mensaje del payload del webhook
        """
        return payload
        
    def _get_cache_key(self, key: str) -> str:
        """
        Genera una clave de caché única para el handler
        """
        return f"{self.__class__.__name__}:{key}"
        
    def cache_get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del caché
        """
        return cache.get(self._get_cache_key(key))
        
    def cache_set(self, key: str, value: Any, timeout: Optional[int] = None):
        """
        Guarda un valor en el caché
        """
        cache.set(
            self._get_cache_key(key),
            value,
            timeout or self.cache_timeout
        )
        
    def cache_delete(self, key: str):
        """
        Elimina un valor del caché
        """
        cache.delete(self._get_cache_key(key)) 