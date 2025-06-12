"""
Servicio base para el sistema de notificaciones de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from functools import wraps
import asyncio

from app.models import BusinessUnit, Notification, NotificationLog
from app.ats.integrations.notifications.core.config import (
    NotificationType,
    NotificationSeverity,
    NOTIFICATION_CHANNELS,
    NOTIFICATION_EMOJIS,
    NOTIFICATION_SEVERITY,
    NOTIFICATION_TEMPLATES,
    NOTIFICATION_RETRIES,
    NOTIFICATION_TIMEOUTS
)

logger = logging.getLogger('notifications')

def notification_retry(max_attempts: int = 3):
    """
    Decorador para reintentar el envío de notificaciones.
    
    Args:
        max_attempts: Número máximo de intentos
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logger.error(f"Error después de {max_attempts} intentos: {str(e)}")
                        raise
                    await asyncio.sleep(1 * attempts)  # Backoff exponencial
            return None
        return wrapper
    return decorator

class BaseNotificationService:
    """Servicio base para notificaciones."""
    
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el servicio de notificaciones.
        
        Args:
            business_unit: Unidad de negocio
        """
        self.business_unit = business_unit
        self.logger = logger
    
    async def _get_channels(self, notification_type: str) -> List[str]:
        """
        Obtiene los canales configurados para el tipo de notificación.
        
        Args:
            notification_type: Tipo de notificación
            
        Returns:
            Lista de canales configurados
        """
        return NOTIFICATION_CHANNELS.get(notification_type, ["telegram"])
    
    def _get_emoji(self, notification_type: str) -> str:
        """
        Obtiene el emoji para el tipo de notificación.
        
        Args:
            notification_type: Tipo de notificación
            
        Returns:
            Emoji correspondiente
        """
        return NOTIFICATION_EMOJIS.get(notification_type, "📢")
    
    def _get_severity(self, notification_type: str) -> str:
        """
        Obtiene la severidad para el tipo de notificación.
        
        Args:
            notification_type: Tipo de notificación
            
        Returns:
            Severidad correspondiente
        """
        return NOTIFICATION_SEVERITY.get(notification_type, NotificationSeverity.INFO.value)
    
    def _get_template(self, notification_type: str) -> str:
        """
        Obtiene la plantilla para el tipo de notificación.
        
        Args:
            notification_type: Tipo de notificación
            
        Returns:
            Plantilla correspondiente
        """
        return NOTIFICATION_TEMPLATES.get(notification_type, "{emoji} *Notificación*\n\n{message}")
    
    def _get_retries(self, notification_type: str) -> int:
        """
        Obtiene el número de reintentos para el tipo de notificación.
        
        Args:
            notification_type: Tipo de notificación
            
        Returns:
            Número de reintentos
        """
        return NOTIFICATION_RETRIES.get(notification_type, 1)
    
    def _get_timeout(self, notification_type: str) -> int:
        """
        Obtiene el timeout para el tipo de notificación.
        
        Args:
            notification_type: Tipo de notificación
            
        Returns:
            Timeout en segundos
        """
        return NOTIFICATION_TIMEOUTS.get(notification_type, 10)
    
    @notification_retry()
    async def send_notification(
        self,
        notification_type: str,
        message: str,
        channels: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Envía una notificación.
        
        Args:
            notification_type: Tipo de notificación
            message: Mensaje a enviar
            channels: Canales a usar (None para usar los configurados)
            context: Contexto para la plantilla
            additional_data: Datos adicionales
            
        Returns:
            Dict con el resultado por canal
        """
        try:
            # Obtener configuración
            channels = channels or await self._get_channels(notification_type)
            emoji = self._get_emoji(notification_type)
            severity = self._get_severity(notification_type)
            template = self._get_template(notification_type)
            
            # Preparar contexto
            context = context or {}
            context.update({
                "emoji": emoji,
                "severity": severity,
                "timestamp": datetime.now().isoformat()
            })
            
            # Formatear mensaje
            formatted_message = template.format(**context)
            
            # Crear notificación
            notification = await Notification.objects.acreate(
                business_unit=self.business_unit,
                notification_type=notification_type,
                message=formatted_message,
                severity=severity,
                channels=channels,
                additional_data=additional_data or {}
            )
            
            # Enviar por cada canal
            results = {}
            for channel in channels:
                try:
                    # Aquí iría la lógica específica de cada canal
                    # Por ahora solo registramos
                    results[channel] = True
                except Exception as e:
                    self.logger.error(f"Error enviando por {channel}: {str(e)}")
                    results[channel] = False
            
            # Registrar resultado
            await NotificationLog.objects.acreate(
                notification=notification,
                status="sent" if all(results.values()) else "partial",
                details=results
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error en send_notification: {str(e)}")
            return {channel: False for channel in channels}
    
    async def log_notification(
        self,
        notification_type: str,
        message: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra una notificación.
        
        Args:
            notification_type: Tipo de notificación
            message: Mensaje
            status: Estado
            details: Detalles adicionales
        """
        try:
            await NotificationLog.objects.acreate(
                business_unit=self.business_unit,
                notification_type=notification_type,
                message=message,
                status=status,
                details=details or {},
                timestamp=datetime.now()
            )
        except Exception as e:
            self.logger.error(f"Error registrando notificación: {str(e)}") 