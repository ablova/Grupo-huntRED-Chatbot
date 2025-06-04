"""
Clase base para handlers de integración

Esta clase proporciona una interfaz común para la implementación de handlers
en diferentes plataformas de integración.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
import logging
import json
from datetime import datetime
from django.core.cache import cache

from app.ats.integrations.base.webhooks import BaseWebhook
from app.ats.integrations.utils import log_integration_event

logger = logging.getLogger(__name__)

class BaseHandler(BaseWebhook):
    """
    Clase base para handlers de integración.
    Hereda de BaseWebhook para manejar webhooks y proporciona funcionalidad
    adicional para procesamiento de mensajes.
    """
    
    def __init__(self, business_unit: Any, secret_key: Optional[str] = None):
        """
        Inicializa el handler
        
        Args:
            business_unit: Unidad de negocio asociada
            secret_key: Clave secreta para validar firmas
        """
        super().__init__(secret_key)
        self.business_unit = business_unit
        self.cache_timeout = 600  # 10 minutos por defecto
        
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja un mensaje entrante
        
        Args:
            message: Mensaje a procesar
            
        Returns:
            Dict con la respuesta
        """
        try:
            # Extraer datos del mensaje
            message_type = message.get('type', 'text')
            content = message.get('content', {})
            
            # Procesar según el tipo
            if message_type == 'text':
                return await self.handle_text_message(content)
            elif message_type == 'image':
                return await self.handle_image_message(content)
            elif message_type == 'document':
                return await self.handle_document_message(content)
            elif message_type == 'location':
                return await self.handle_location_message(content)
            elif message_type == 'contact':
                return await self.handle_contact_message(content)
            else:
                return await self.handle_unknown_message(message)
                
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }
            
    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja un webhook entrante
        
        Args:
            payload: Datos del webhook
            
        Returns:
            Dict con la respuesta
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
        
        Args:
            payload: Payload del webhook
            
        Returns:
            Dict con el mensaje extraído
        """
        return payload
        
    def _get_cache_key(self, key: str) -> str:
        """
        Genera una clave de caché única para el handler
        
        Args:
            key: Clave base
            
        Returns:
            str: Clave de caché única
        """
        return f"{self.__class__.__name__}:{key}"
        
    def cache_get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del caché
        
        Args:
            key: Clave del valor
            
        Returns:
            Optional[Any]: Valor en caché o None
        """
        return cache.get(self._get_cache_key(key))
        
    def cache_set(self, key: str, value: Any, timeout: Optional[int] = None):
        """
        Guarda un valor en el caché
        
        Args:
            key: Clave del valor
            value: Valor a guardar
            timeout: Tiempo de expiración
        """
        cache.set(
            self._get_cache_key(key),
            value,
            timeout or self.cache_timeout
        )
        
    def cache_delete(self, key: str):
        """
        Elimina un valor del caché
        
        Args:
            key: Clave del valor
        """
        cache.delete(self._get_cache_key(key))
        
    @abstractmethod
    async def handle_text_message(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja un mensaje de texto
        
        Args:
            content: Contenido del mensaje
            
        Returns:
            Dict con la respuesta
        """
        pass
        
    @abstractmethod
    async def handle_image_message(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja un mensaje con imagen
        
        Args:
            content: Contenido del mensaje
            
        Returns:
            Dict con la respuesta
        """
        pass
        
    @abstractmethod
    async def handle_document_message(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja un mensaje con documento
        
        Args:
            content: Contenido del mensaje
            
        Returns:
            Dict con la respuesta
        """
        pass
        
    @abstractmethod
    async def handle_location_message(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja un mensaje con ubicación
        
        Args:
            content: Contenido del mensaje
            
        Returns:
            Dict con la respuesta
        """
        pass
        
    @abstractmethod
    async def handle_contact_message(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja un mensaje con contacto
        
        Args:
            content: Contenido del mensaje
            
        Returns:
            Dict con la respuesta
        """
        pass
        
    @abstractmethod
    async def handle_unknown_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja un mensaje de tipo desconocido
        
        Args:
            message: Mensaje completo
            
        Returns:
            Dict con la respuesta
        """
        pass 