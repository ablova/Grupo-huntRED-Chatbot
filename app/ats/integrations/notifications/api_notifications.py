"""
Servicio de notificaciones de API de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class APINotificationService(BaseNotificationService):
    """Servicio de notificaciones de API."""
    
    async def notify_api_status(
        self,
        api_name: str,
        status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el estado de una API.
        
        Args:
            api_name: Nombre de la API
            status: Estado de la API
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.API_STATUS.value,
            message="",
            context={
                "api_name": api_name,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_api_health(
        self,
        api_name: str,
        health_status: str,
        metrics: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la salud de una API.
        
        Args:
            api_name: Nombre de la API
            health_status: Estado de salud
            metrics: Métricas de la API
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.API_HEALTH.value,
            message="",
            context={
                "api_name": api_name,
                "health_status": health_status,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_api_request(
        self,
        api_name: str,
        request_type: str,
        request_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una petición de API.
        
        Args:
            api_name: Nombre de la API
            request_type: Tipo de petición
            request_details: Detalles de la petición
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.API_REQUEST.value,
            message="",
            context={
                "api_name": api_name,
                "request_type": request_type,
                "request_details": request_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_api_response(
        self,
        api_name: str,
        response_type: str,
        response_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una respuesta de API.
        
        Args:
            api_name: Nombre de la API
            response_type: Tipo de respuesta
            response_details: Detalles de la respuesta
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.API_RESPONSE.value,
            message="",
            context={
                "api_name": api_name,
                "response_type": response_type,
                "response_details": response_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_api_error(
        self,
        api_name: str,
        error_type: str,
        error_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un error de API.
        
        Args:
            api_name: Nombre de la API
            error_type: Tipo de error
            error_details: Detalles del error
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.API_ERROR.value,
            message="",
            context={
                "api_name": api_name,
                "error_type": error_type,
                "error_details": error_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de API
api_notifier = APINotificationService(BusinessUnit.objects.first()) 