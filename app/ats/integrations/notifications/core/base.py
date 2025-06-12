"""
Sistema base de notificaciones para Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from django.utils import timezone

from app.models import BusinessUnit, Notification, NotificationLog

logger = logging.getLogger('notifications')

class BaseNotificationChannel(ABC):
    """Canal base para notificaciones."""
    
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el canal de notificación.
        
        Args:
            business_unit: Unidad de negocio asociada
        """
        self.business_unit = business_unit
    
    @abstractmethod
    async def send_notification(
        self,
        message: str,
        options: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Envía una notificación a través del canal.
        
        Args:
            message: Mensaje a enviar
            options: Opciones adicionales
            priority: Prioridad de la notificación
        
        Returns:
            Dict con el resultado de la operación
        """
        pass
    
    async def log_notification(
        self,
        message: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra una notificación en el sistema.
        
        Args:
            message: Mensaje enviado
            status: Estado de la notificación
            details: Detalles adicionales
        """
        try:
            await NotificationLog.objects.acreate(
                business_unit=self.business_unit,
                channel=self.__class__.__name__,
                message=message,
                status=status,
                details=details or {},
                timestamp=timezone.now()
            )
        except Exception as e:
            logger.error(f"Error registrando notificación: {str(e)}")
            
    def _format_message(self, message: str, priority: int) -> str:
        """
        Formatea el mensaje según la prioridad.
        
        Args:
            message: Mensaje original
            priority: Nivel de prioridad (0-5)
            
        Returns:
            Mensaje formateado
        """
        if priority >= 4:
            return f"🚨 URGENTE: {message}"
        elif priority >= 2:
            return f"⚠️ IMPORTANTE: {message}"
        return message
    
    def is_enabled(self) -> bool:
        """
        Verifica si el canal está habilitado.
        
        Returns:
            True si el canal está habilitado, False en caso contrario
        """
        return getattr(self.business_unit, f"{self.__class__.__name__.lower()}_notifications_enabled", False)
    
    def get_channel_name(self) -> str:
        """
        Obtiene el nombre del canal.
        
        Returns:
            Nombre del canal
        """
        return self.__class__.__name__.replace('NotificationChannel', '').lower() 