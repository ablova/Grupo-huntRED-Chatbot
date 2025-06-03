from typing import Dict, Any, Optional, List
from django.db import models
from abc import ABC, abstractmethod

class BaseIntegration(ABC):
    """
    Clase base para todas las integraciones de canales.
    Soporta tanto funcionalidades de publicación como de chatbot.
    """
    def __init__(self):
        self.name = self.__class__.__name__.replace('Integration', '').lower()
        self.supported_features = self._get_supported_features()
        
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
        Maneja webhooks entrantes
        """
        if not self.supported_features.get('webhook'):
            raise NotImplementedError("Esta integración no soporta webhooks")
        return {}

    # Nuevos métodos para soporte de publicación
    async def publish_content(self, content: Dict[str, Any], channel: models.Model) -> Dict[str, Any]:
        """
        Publica contenido en el canal
        """
        if not self.supported_features.get('publish'):
            raise NotImplementedError("Esta integración no soporta publicación")
        return {}

    async def schedule_publication(self, content: Dict[str, Any], channel: models.Model, 
                                 schedule_time: Any) -> Dict[str, Any]:
        """
        Programa una publicación para más tarde
        """
        if not self.supported_features.get('publish'):
            raise NotImplementedError("Esta integración no soporta publicación")
        return {} 