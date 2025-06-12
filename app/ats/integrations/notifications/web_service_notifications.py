"""
Servicio de notificaciones de servicio web de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class WebServiceNotificationService(BaseNotificationService):
    """Servicio de notificaciones de servicio web."""
    
    async def notify_web_service_status(
        self,
        service_name: str,
        status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el estado de un servicio web.
        
        Args:
            service_name: Nombre del servicio
            status: Estado del servicio
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.WEB_SERVICE_STATUS.value,
            message="",
            context={
                "service_name": service_name,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_web_service_health(
        self,
        service_name: str,
        health_status: str,
        metrics: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la salud de un servicio web.
        
        Args:
            service_name: Nombre del servicio
            health_status: Estado de salud
            metrics: Métricas del servicio
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.WEB_SERVICE_HEALTH.value,
            message="",
            context={
                "service_name": service_name,
                "health_status": health_status,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_web_service_request(
        self,
        service_name: str,
        request_type: str,
        request_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una petición de servicio web.
        
        Args:
            service_name: Nombre del servicio
            request_type: Tipo de petición
            request_details: Detalles de la petición
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.WEB_SERVICE_REQUEST.value,
            message="",
            context={
                "service_name": service_name,
                "request_type": request_type,
                "request_details": request_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_web_service_response(
        self,
        service_name: str,
        response_type: str,
        response_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una respuesta de servicio web.
        
        Args:
            service_name: Nombre del servicio
            response_type: Tipo de respuesta
            response_details: Detalles de la respuesta
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.WEB_SERVICE_RESPONSE.value,
            message="",
            context={
                "service_name": service_name,
                "response_type": response_type,
                "response_details": response_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_web_service_error(
        self,
        service_name: str,
        error_type: str,
        error_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un error de servicio web.
        
        Args:
            service_name: Nombre del servicio
            error_type: Tipo de error
            error_details: Detalles del error
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.WEB_SERVICE_ERROR.value,
            message="",
            context={
                "service_name": service_name,
                "error_type": error_type,
                "error_details": error_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de servicio web
web_service_notifier = WebServiceNotificationService(BusinessUnit.objects.first()) 