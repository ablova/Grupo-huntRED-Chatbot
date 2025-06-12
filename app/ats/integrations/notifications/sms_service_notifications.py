"""
Servicio de notificaciones de servicio de SMS de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class SMSServiceNotificationService(BaseNotificationService):
    """Servicio de notificaciones de servicio de SMS."""
    
    async def notify_sms_service_status(
        self,
        service_name: str,
        status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el estado de un servicio de SMS.
        
        Args:
            service_name: Nombre del servicio
            status: Estado del servicio
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SMS_SERVICE_STATUS.value,
            message="",
            context={
                "service_name": service_name,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_sms_service_health(
        self,
        service_name: str,
        health_status: str,
        metrics: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la salud de un servicio de SMS.
        
        Args:
            service_name: Nombre del servicio
            health_status: Estado de salud
            metrics: Métricas del servicio
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SMS_SERVICE_HEALTH.value,
            message="",
            context={
                "service_name": service_name,
                "health_status": health_status,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_sms_sent(
        self,
        service_name: str,
        sms_type: str,
        sms_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un SMS enviado.
        
        Args:
            service_name: Nombre del servicio
            sms_type: Tipo de SMS
            sms_details: Detalles del SMS
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SMS_SENT.value,
            message="",
            context={
                "service_name": service_name,
                "sms_type": sms_type,
                "sms_details": sms_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_sms_received(
        self,
        service_name: str,
        sms_type: str,
        sms_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un SMS recibido.
        
        Args:
            service_name: Nombre del servicio
            sms_type: Tipo de SMS
            sms_details: Detalles del SMS
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SMS_RECEIVED.value,
            message="",
            context={
                "service_name": service_name,
                "sms_type": sms_type,
                "sms_details": sms_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_sms_error(
        self,
        service_name: str,
        error_type: str,
        error_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un error de servicio de SMS.
        
        Args:
            service_name: Nombre del servicio
            error_type: Tipo de error
            error_details: Detalles del error
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SMS_ERROR.value,
            message="",
            context={
                "service_name": service_name,
                "error_type": error_type,
                "error_details": error_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de servicio de SMS
sms_service_notifier = SMSServiceNotificationService(BusinessUnit.objects.first()) 