"""
Servicio de notificaciones de servicio de correo de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class EmailServiceNotificationService(BaseNotificationService):
    """Servicio de notificaciones de servicio de correo."""
    
    async def notify_email_service_status(
        self,
        service_name: str,
        status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el estado de un servicio de correo.
        
        Args:
            service_name: Nombre del servicio
            status: Estado del servicio
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.EMAIL_SERVICE_STATUS.value,
            message="",
            context={
                "service_name": service_name,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_email_service_health(
        self,
        service_name: str,
        health_status: str,
        metrics: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la salud de un servicio de correo.
        
        Args:
            service_name: Nombre del servicio
            health_status: Estado de salud
            metrics: Métricas del servicio
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.EMAIL_SERVICE_HEALTH.value,
            message="",
            context={
                "service_name": service_name,
                "health_status": health_status,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_email_sent(
        self,
        service_name: str,
        email_type: str,
        email_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un correo enviado.
        
        Args:
            service_name: Nombre del servicio
            email_type: Tipo de correo
            email_details: Detalles del correo
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.EMAIL_SENT.value,
            message="",
            context={
                "service_name": service_name,
                "email_type": email_type,
                "email_details": email_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_email_received(
        self,
        service_name: str,
        email_type: str,
        email_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un correo recibido.
        
        Args:
            service_name: Nombre del servicio
            email_type: Tipo de correo
            email_details: Detalles del correo
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.EMAIL_RECEIVED.value,
            message="",
            context={
                "service_name": service_name,
                "email_type": email_type,
                "email_details": email_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_email_error(
        self,
        service_name: str,
        error_type: str,
        error_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un error de servicio de correo.
        
        Args:
            service_name: Nombre del servicio
            error_type: Tipo de error
            error_details: Detalles del error
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.EMAIL_ERROR.value,
            message="",
            context={
                "service_name": service_name,
                "error_type": error_type,
                "error_details": error_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de servicio de correo
email_service_notifier = EmailServiceNotificationService(BusinessUnit.objects.first()) 