"""
Servicio de notificaciones de integración de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class IntegrationNotificationService(BaseNotificationService):
    """Servicio de notificaciones de integración."""
    
    async def notify_integration_status(
        self,
        integration_name: str,
        status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el estado de una integración.
        
        Args:
            integration_name: Nombre de la integración
            status: Estado de la integración
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.INTEGRATION_STATUS.value,
            message="",
            context={
                "integration_name": integration_name,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_integration_health(
        self,
        integration_name: str,
        health_status: str,
        metrics: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la salud de una integración.
        
        Args:
            integration_name: Nombre de la integración
            health_status: Estado de salud
            metrics: Métricas de la integración
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.INTEGRATION_HEALTH.value,
            message="",
            context={
                "integration_name": integration_name,
                "health_status": health_status,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_integration_sync(
        self,
        integration_name: str,
        sync_type: str,
        sync_details: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una sincronización de integración.
        
        Args:
            integration_name: Nombre de la integración
            sync_type: Tipo de sincronización
            sync_details: Detalles de la sincronización
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.INTEGRATION_SYNC.value,
            message="",
            context={
                "integration_name": integration_name,
                "sync_type": sync_type,
                "sync_details": sync_details,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_integration_configuration(
        self,
        integration_name: str,
        configuration_type: str,
        configuration_changes: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre cambios en la configuración de una integración.
        
        Args:
            integration_name: Nombre de la integración
            configuration_type: Tipo de configuración
            configuration_changes: Cambios en la configuración
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.INTEGRATION_CONFIGURATION.value,
            message="",
            context={
                "integration_name": integration_name,
                "configuration_type": configuration_type,
                "configuration_changes": configuration_changes,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_integration_dependency(
        self,
        integration_name: str,
        dependency_name: str,
        dependency_type: str,
        dependency_status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el estado de una dependencia de la integración.
        
        Args:
            integration_name: Nombre de la integración
            dependency_name: Nombre de la dependencia
            dependency_type: Tipo de dependencia
            dependency_status: Estado de la dependencia
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.INTEGRATION_DEPENDENCY.value,
            message="",
            context={
                "integration_name": integration_name,
                "dependency_name": dependency_name,
                "dependency_type": dependency_type,
                "dependency_status": dependency_status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de integración
integration_notifier = IntegrationNotificationService(BusinessUnit.objects.first()) 