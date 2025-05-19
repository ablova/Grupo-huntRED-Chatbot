import logging
from typing import Dict, Any
from django.conf import settings
from django.db import models
from app.com.publish.utils.content_adapters import ContentAdapter

class BaseProcessor:
    """
    Procesador base para publicación en diferentes canales
    """
    def __init__(self, channel: Dict[str, Any]):
        self.channel = channel
        self.business_unit = self._get_business_unit()
        self.logger = logging.getLogger('publish')
        
    def _get_business_unit(self) -> models.Model:
        """
        Obtiene la unidad de negocio asociada al canal
        """
        from app.models import BusinessUnit
        try:
            return BusinessUnit.objects.get(id=self.channel['business_unit'])
        except BusinessUnit.DoesNotExist:
            self.logger.error(f"No se encontró unidad de negocio para el canal {self.channel['id']}")
            raise
            
    async def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publica contenido en el canal
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")
        
    async def get_analytics(self) -> Dict[str, Any]:
        """
        Obtiene métricas del canal
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")
        
    def validate_content(self, content: Dict[str, Any]) -> bool:
        """
        Valida el contenido antes de la publicación
        """
        if not content.get('text') and not content.get('media'):
            self.logger.error("El contenido debe tener texto o medios")
            return False
            
        if self.channel['type'] == 'WHATSAPP_GROUP' and len(content.get('text', '')) > 1000:
            self.logger.error("El texto excede el límite de WhatsApp")
            return False
            
        return True
        
    def log_publication(self, result: Dict[str, Any]):
        """
        Registra la publicación
        """
        self.logger.info(f"Publicación exitosa en {self.channel['type']}")
        self.logger.debug(f"Detalles de la publicación: {result}")
        
    def handle_error(self, error: Exception):
        """
        Maneja errores de publicación
        """
        self.logger.error(f"Error en publicación: {str(error)}")
        raise error
