from typing import Dict, Any, Optional, List, Union
from django.db import models
from abc import ABC, abstractmethod
import logging
from django.core.cache import cache
from django.conf import settings
import time
from datetime import datetime

from .services import BaseService
from .metrics import ChannelMetrics

logger = logging.getLogger(__name__)

class BaseIntegration(ABC):
    """
    Clase base para todas las integraciones de canales.
    Soporta tanto funcionalidades de publicación como de chatbot.
    """
    def __init__(self, channel_name: str, fallback_channels: List[str] = None):
        """
        Inicializa la integración base
        
        Args:
            channel_name: Nombre del canal
            fallback_channels: Lista de canales de respaldo
        """
        self.name = self.__class__.__name__.replace('Integration', '').lower()
        self.supported_features = self._get_supported_features()
        self.channel_name = channel_name
        self.fallback_channels = fallback_channels or []
        self.metrics = ChannelMetrics(channel_name)
        self.retry_config = {
            'max_retries': 3,
            'retry_delay': 1,  # segundos
            'backoff_factor': 2
        }
        
    def _get_supported_features(self) -> Dict[str, bool]:
        """
        Define las características soportadas por la integración
        """
        return {
            'publish': True,
            'chatbot': True,
            'analytics': True,
            'webhook': True
        }
        
    @abstractmethod
    def register_channel(self, channel_type: str, identifier: str, name: str) -> models.Model:
        """
        Registra un canal para la integración
        """
        pass
        
    @abstractmethod
    def validate_channel(self, channel: models.Model) -> bool:
        """
        Valida las credenciales de un canal
        """
        pass
        
    @abstractmethod
    def get_channel_status(self, channel: models.Model) -> Dict[str, Any]:
        """
        Obtiene el estado de un canal
        """
        pass
        
    @abstractmethod
    def get_channel_analytics(self, channel: models.Model) -> Dict[str, Any]:
        """
        Obtiene las métricas de un canal
        """
        pass
        
    @abstractmethod
    def send_message(self, channel: models.Model, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía un mensaje a través del canal
        """
        pass
        
    def register(self):
        """
        Registra la integración
        """
        pass
        
    def unregister(self):
        """
        Desregistra la integración
        """
        pass
        
    def get_settings(self) -> Dict[str, Any]:
        """
        Obtiene las configuraciones de la integración
        """
        return {}
        
    def set_settings(self, settings: Dict[str, Any]):
        """
        Establece las configuraciones de la integración
        """
        pass
        
    def get_channel_types(self) -> Dict[str, str]:
        """
        Obtiene los tipos de canales disponibles para la integración
        """
        return {}
        
    def validate_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Valida las configuraciones de la integración
        """
        return True
        
    def get_channel_metadata(self, channel: models.Model) -> Dict[str, Any]:
        """
        Obtiene los metadatos de un canal
        """
        return {}
        
    def update_channel_metadata(self, channel: models.Model, metadata: Dict[str, Any]):
        """
        Actualiza los metadatos de un canal
        """
        pass

    # Nuevos métodos para soporte de chatbot
    async def handle_incoming_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja mensajes entrantes (para chatbot)
        """
        if not self.supported_features.get('chatbot'):
            raise NotImplementedError("Esta integración no soporta chatbot")
        return {}

    async def handle_outgoing_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja mensajes salientes (para chatbot)
        """
        if not self.supported_features.get('chatbot'):
            raise NotImplementedError("Esta integración no soporta chatbot")
        return {}

    # Nuevos métodos para soporte de webhook
    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja un webhook entrante
        
        Args:
            payload: Datos del webhook
            
        Returns:
            Dict con la respuesta al webhook
        """
        start_time = time.time()
        
        try:
            # Validar la firma del webhook
            if not self._validate_webhook_signature(payload):
                raise ValueError("Firma de webhook inválida")
                
            # Procesar el webhook
            result = await self._process_webhook(payload)
            
            # Registrar métricas de éxito
            self.metrics.record_webhook_success(
                duration=time.time() - start_time,
                payload_size=len(str(payload))
            )
            
            return result
            
        except Exception as e:
            # Registrar métricas de error
            self.metrics.record_webhook_error(
                error_type=type(e).__name__,
                duration=time.time() - start_time
            )
            raise
            
    def _validate_webhook_signature(self, payload: Dict[str, Any]) -> bool:
        """
        Valida la firma del webhook
        
        Args:
            payload: Datos del webhook
            
        Returns:
            bool: True si la firma es válida
        """
        # Implementación específica de validación de firma
        return True
        
    @abstractmethod
    async def _process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un webhook entrante
        
        Args:
            payload: Datos del webhook
            
        Returns:
            Dict con la respuesta al webhook
        """
        pass
        
    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtiene las métricas del canal
        
        Returns:
            Dict con las métricas del canal
        """
        return self.metrics.get_metrics()

    async def publish(self, message: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Publica un mensaje en el canal
        
        Args:
            message: Mensaje a publicar
            **kwargs: Argumentos adicionales
            
        Returns:
            Dict con el resultado de la publicación
        """
        start_time = time.time()
        result = None
        retry_count = 0
        
        while retry_count < self.retry_config['max_retries']:
            try:
                # Intentar publicar en el canal principal
                result = await self._publish_to_channel(message, **kwargs)
                
                # Registrar métricas de éxito
                self.metrics.record_success(
                    duration=time.time() - start_time,
                    message_size=len(str(message))
                )
                
                return result
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Error publicando en {self.channel_name}: {str(e)}")
                
                # Registrar métricas de error
                self.metrics.record_error(
                    error_type=type(e).__name__,
                    duration=time.time() - start_time
                )
                
                if retry_count < self.retry_config['max_retries']:
                    # Esperar antes de reintentar
                    delay = self.retry_config['retry_delay'] * (self.retry_config['backoff_factor'] ** (retry_count - 1))
                    await asyncio.sleep(delay)
                    
                    # Intentar canal de respaldo
                    if self.fallback_channels:
                        for fallback_channel in self.fallback_channels:
                            try:
                                result = await self._publish_to_fallback(fallback_channel, message, **kwargs)
                                if result:
                                    logger.info(f"Mensaje enviado exitosamente a través del canal de respaldo {fallback_channel}")
                                    return result
                            except Exception as fallback_error:
                                logger.error(f"Error en canal de respaldo {fallback_channel}: {str(fallback_error)}")
                                
                # Si llegamos aquí, todos los intentos fallaron
                raise
                
    async def _publish_to_channel(self, message: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Publica un mensaje en el canal principal
        
        Args:
            message: Mensaje a publicar
            **kwargs: Argumentos adicionales
            
        Returns:
            Dict con el resultado de la publicación
        """
        # Implementación específica del canal
        return await self._do_publish(message, **kwargs)
        
    async def _publish_to_fallback(self, channel: str, message: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Publica un mensaje en un canal de respaldo
        
        Args:
            channel: Nombre del canal de respaldo
            message: Mensaje a publicar
            **kwargs: Argumentos adicionales
            
        Returns:
            Dict con el resultado de la publicación
        """
        # Obtener la instancia del canal de respaldo
        fallback = self._get_fallback_channel(channel)
        if fallback:
            return await fallback._do_publish(message, **kwargs)
        return None
        
    def _get_fallback_channel(self, channel: str) -> Optional['BaseIntegration']:
        """
        Obtiene una instancia del canal de respaldo
        
        Args:
            channel: Nombre del canal
            
        Returns:
            Instancia del canal de respaldo o None
        """
        # Implementación específica para obtener el canal de respaldo
        pass
        
    @abstractmethod
    async def _do_publish(self, message: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Implementación específica de la publicación
        
        Args:
            message: Mensaje a publicar
            **kwargs: Argumentos adicionales
            
        Returns:
            Dict con el resultado de la publicación
        """
        pass

    async def schedule_publication(self, content: Dict[str, Any], channel: models.Model, 
                                 schedule_time: Any) -> Dict[str, Any]:
        """
        Programa una publicación para más tarde
        """
        if not self.supported_features.get('publish'):
            raise NotImplementedError("Esta integración no soporta publicación")
        return {} 