# /home/pablo/app/com/notifications/core.py
"""
Core functionality for notifications.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from functools import wraps

from django.conf import settings
from asgiref.sync import sync_to_async
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models import BusinessUnit, Notification, NotificationLog
from app.ats.integrations.notifications.channels.telegram import TelegramNotificationChannel
from app.ats.integrations.notifications.channels.whatsapp import WhatsAppNotificationChannel
from app.ats.integrations.notifications.channels.slack import SlackNotificationChannel
from app.ats.integrations.notifications.channels.messenger import MessengerNotificationChannel
from app.ats.integrations.notifications.channels.instagram import InstagramNotificationChannel
from app.ats.integrations.notifications.channels.x import XNotificationChannel

logger = logging.getLogger('chatbot')

def notification_retry(max_attempts=3):
    """Decorador para reintentar operaciones de notificación."""
    def decorator(func):
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            reraise=True
        )
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error en {func.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator

class NotificationManager:
    """Gestor de notificaciones."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self._channels = {}
    
    async def _get_channel(self, channel_name: str) -> Any:
        """Obtiene o crea el canal especificado."""
        if channel_name not in self._channels:
            if channel_name == 'telegram':
                self._channels[channel_name] = TelegramNotificationChannel(self.business_unit)
            elif channel_name == 'whatsapp':
                self._channels[channel_name] = WhatsAppNotificationChannel(self.business_unit)
            elif channel_name == 'slack':
                self._channels[channel_name] = SlackNotificationChannel(self.business_unit)
            elif channel_name == 'messenger':
                self._channels[channel_name] = MessengerNotificationChannel(self.business_unit)
            elif channel_name == 'instagram':
                self._channels[channel_name] = InstagramNotificationChannel(self.business_unit)
            elif channel_name == 'x':
                self._channels[channel_name] = XNotificationChannel(self.business_unit)
            else:
                raise ValueError(f"Canal no soportado: {channel_name}")
        
        return self._channels[channel_name]
    
    @notification_retry(max_attempts=3)
    async def send_notification(
        self,
        message: str,
        channels: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Envía una notificación a través de los canales especificados.
        
        Args:
            message: Mensaje a enviar
            channels: Lista de canales a usar (None para todos los habilitados)
            options: Opciones adicionales
            priority: Prioridad de la notificación
        
        Returns:
            Dict con los resultados por canal
        """
        try:
            # Crear la notificación
            notification = await sync_to_async(Notification.objects.create)(
                message=message,
                business_unit=self.business_unit,
                priority=priority,
                options=options or {}
            )
            
            # Determinar canales a usar
            if not channels:
                channels = ['telegram', 'whatsapp', 'slack', 'messenger', 'instagram', 'x']
            
            results = {}
            for channel_name in channels:
                try:
                    channel = await self._get_channel(channel_name)
                    if channel.is_enabled():
                        result = await channel.send_notification(message, options, priority)
                        
                        # Registrar el resultado
                        await sync_to_async(NotificationLog.objects.create)(
                            notification=notification,
                            channel=channel_name,
                            success=result.get('success', False),
                            error=result.get('error'),
                            timestamp=datetime.now()
                        )
                        
                        results[channel_name] = result
                except Exception as e:
                    logger.error(f"Error en canal {channel_name}: {str(e)}")
                    results[channel_name] = {
                        'success': False,
                        'error': str(e)
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"Error enviando notificación: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @notification_retry(max_attempts=3)
    async def schedule_notification(
        self,
        message: str,
        scheduled_time: datetime,
        channels: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Programa una notificación para ser enviada en el futuro.
        
        Args:
            message: Mensaje a enviar
            scheduled_time: Tiempo programado
            channels: Lista de canales a usar
            options: Opciones adicionales
            priority: Prioridad de la notificación
        
        Returns:
            Dict con el resultado de la operación
        """
        try:
            # Crear la notificación programada
            notification = await sync_to_async(Notification.objects.create)(
                message=message,
                business_unit=self.business_unit,
                priority=priority,
                options=options or {},
                scheduled_time=scheduled_time,
                status='scheduled'
            )
            
            return {
                'success': True,
                'notification_id': notification.id,
                'scheduled_time': scheduled_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error programando notificación: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @notification_retry(max_attempts=3)
    async def verify_notification(self, notification_id: int) -> Dict[str, Any]:
        """
        Verifica el estado de una notificación.
        
        Args:
            notification_id: ID de la notificación
        
        Returns:
            Dict con el estado de la notificación
        """
        try:
            notification = await sync_to_async(Notification.objects.get)(id=notification_id)
            logs = await sync_to_async(list)(NotificationLog.objects.filter(notification=notification))
            
            return {
                'success': True,
                'notification': {
                    'id': notification.id,
                    'message': notification.message,
                    'status': notification.status,
                    'priority': notification.priority,
                    'created_at': notification.created_at.isoformat(),
                    'scheduled_time': notification.scheduled_time.isoformat() if notification.scheduled_time else None,
                    'logs': [
                        {
                            'channel': log.channel,
                            'success': log.success,
                            'error': log.error,
                            'timestamp': log.timestamp.isoformat()
                        }
                        for log in logs
                    ]
                }
            }
            
        except Notification.DoesNotExist:
            return {
                'success': False,
                'error': f"Notificación {notification_id} no encontrada"
            }
        except Exception as e:
            logger.error(f"Error verificando notificación: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Funciones de utilidad para compatibilidad con código existente

def get_notification_manager(business_unit: Optional[BusinessUnit] = None) -> NotificationManager:
    """Obtiene una instancia del gestor de notificaciones."""
    if not business_unit:
        business_unit = BusinessUnit.objects.first()
    return NotificationManager(business_unit)

@notification_retry(max_attempts=3)
async def send_notification(
    message: str,
    channels: Optional[List[str]] = None,
    options: Optional[Dict[str, Any]] = None,
    priority: int = 0,
    business_unit: Optional[BusinessUnit] = None
) -> Dict[str, Any]:
    """Envía una notificación."""
    manager = get_notification_manager(business_unit)
    return await manager.send_notification(message, channels, options, priority)

@notification_retry(max_attempts=3)
async def schedule_notification(
    message: str,
    scheduled_time: datetime,
    channels: Optional[List[str]] = None,
    options: Optional[Dict[str, Any]] = None,
    priority: int = 0,
    business_unit: Optional[BusinessUnit] = None
) -> Dict[str, Any]:
    """Programa una notificación."""
    manager = get_notification_manager(business_unit)
    return await manager.schedule_notification(message, scheduled_time, channels, options, priority)

@notification_retry(max_attempts=3)
async def verify_notification(
    notification_id: int,
    business_unit: Optional[BusinessUnit] = None
) -> Dict[str, Any]:
    """Verifica el estado de una notificación."""
    manager = get_notification_manager(business_unit)
    return await manager.verify_notification(notification_id)
