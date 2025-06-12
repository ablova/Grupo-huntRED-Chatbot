"""
Servicio de notificaciones de aplicación de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class ApplicationNotificationService(BaseNotificationService):
    """Servicio de notificaciones de aplicación."""
    
    async def notify_application_status(
        self,
        application_name: str,
        status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el estado de una aplicación.
        
        Args:
            application_name: Nombre de la aplicación
            status: Estado de la aplicación
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.APPLICATION_STATUS.value,
            message="",
            context={
                "application_name": application_name,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_application_health(
        self,
        application_name: str,
        health_status: str,
        metrics: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la salud de una aplicación.
        
        Args:
            application_name: Nombre de la aplicación
            health_status: Estado de salud
            metrics: Métricas de la aplicación
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.APPLICATION_HEALTH.value,
            message="",
            context={
                "application_name": application_name,
                "health_status": health_status,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_application_deployment(
        self,
        application_name: str,
        deployment_type: str,
        deployment_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un despliegue de aplicación.
        
        Args:
            application_name: Nombre de la aplicación
            deployment_type: Tipo de despliegue
            deployment_details: Detalles del despliegue
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.APPLICATION_DEPLOYMENT.value,
            message="",
            context={
                "application_name": application_name,
                "deployment_type": deployment_type,
                "deployment_details": deployment_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_application_configuration(
        self,
        application_name: str,
        configuration_type: str,
        configuration_changes: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre cambios en la configuración de una aplicación.
        
        Args:
            application_name: Nombre de la aplicación
            configuration_type: Tipo de configuración
            configuration_changes: Cambios en la configuración
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.APPLICATION_CONFIGURATION.value,
            message="",
            context={
                "application_name": application_name,
                "configuration_type": configuration_type,
                "configuration_changes": configuration_changes,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_application_dependency(
        self,
        application_name: str,
        dependency_name: str,
        dependency_type: str,
        dependency_status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el estado de una dependencia de la aplicación.
        
        Args:
            application_name: Nombre de la aplicación
            dependency_name: Nombre de la dependencia
            dependency_type: Tipo de dependencia
            dependency_status: Estado de la dependencia
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.APPLICATION_DEPENDENCY.value,
            message="",
            context={
                "application_name": application_name,
                "dependency_name": dependency_name,
                "dependency_type": dependency_type,
                "dependency_status": dependency_status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de aplicación
application_notifier = ApplicationNotificationService(BusinessUnit.objects.first()) 