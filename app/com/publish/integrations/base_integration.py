from typing import Dict, Any, Optional
from django.db import models

class BaseIntegration:
    """
    Integración base para canales de publicación
    """
    def __init__(self):
        self.name = self.__class__.__name__.replace('Integration', '').lower()
        
    def register_channel(self, channel_type: str, identifier: str, name: str) -> models.Model:
        """
        Registra un canal para la integración
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")
        
    def validate_channel(self, channel: models.Model) -> bool:
        """
        Valida las credenciales de un canal
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")
        
    def get_channel_status(self, channel: models.Model) -> Dict[str, Any]:
        """
        Obtiene el estado de un canal
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")
        
    def get_channel_analytics(self, channel: models.Model) -> Dict[str, Any]:
        """
        Obtiene las métricas de un canal
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")
        
    def send_message(self, channel: models.Model, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía un mensaje a través del canal
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")
        
    def register(self):
        """
        Registra la integración
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")
        
    def unregister(self):
        """
        Desregistra la integración
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")
        
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
