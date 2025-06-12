"""
Servicio de notificaciones de cola de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class QueueNotificationService(BaseNotificationService):
    """Servicio de notificaciones de cola."""
    
    async def notify_queue_status(
        self,
        queue_name: str,
        status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el estado de una cola.
        
        Args:
            queue_name: Nombre de la cola
            status: Estado de la cola
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.QUEUE_STATUS.value,
            message="",
            context={
                "queue_name": queue_name,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_queue_health(
        self,
        queue_name: str,
        health_status: str,
        metrics: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la salud de una cola.
        
        Args:
            queue_name: Nombre de la cola
            health_status: Estado de salud
            metrics: Métricas de la cola
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.QUEUE_HEALTH.value,
            message="",
            context={
                "queue_name": queue_name,
                "health_status": health_status,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_queue_message(
        self,
        queue_name: str,
        message_type: str,
        message_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un mensaje de cola.
        
        Args:
            queue_name: Nombre de la cola
            message_type: Tipo de mensaje
            message_details: Detalles del mensaje
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.QUEUE_MESSAGE.value,
            message="",
            context={
                "queue_name": queue_name,
                "message_type": message_type,
                "message_details": message_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_queue_error(
        self,
        queue_name: str,
        error_type: str,
        error_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un error de cola.
        
        Args:
            queue_name: Nombre de la cola
            error_type: Tipo de error
            error_details: Detalles del error
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.QUEUE_ERROR.value,
            message="",
            context={
                "queue_name": queue_name,
                "error_type": error_type,
                "error_details": error_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_queue_retry(
        self,
        queue_name: str,
        retry_type: str,
        retry_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un reintento de cola.
        
        Args:
            queue_name: Nombre de la cola
            retry_type: Tipo de reintento
            retry_details: Detalles del reintento
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.QUEUE_RETRY.value,
            message="",
            context={
                "queue_name": queue_name,
                "retry_type": retry_type,
                "retry_details": retry_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de cola
queue_notifier = QueueNotificationService(BusinessUnit.objects.first()) 