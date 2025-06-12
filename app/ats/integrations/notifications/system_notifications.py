"""
Servicio de notificaciones de sistema de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class SystemNotificationService(BaseNotificationService):
    """Servicio de notificaciones de sistema."""
    
    async def notify_system_status(
        self,
        system_name: str,
        status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el estado de un sistema.
        
        Args:
            system_name: Nombre del sistema
            status: Estado del sistema
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SYSTEM_STATUS.value,
            message="",
            context={
                "system_name": system_name,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_system_health(
        self,
        system_name: str,
        health_status: str,
        metrics: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la salud de un sistema.
        
        Args:
            system_name: Nombre del sistema
            health_status: Estado de salud
            metrics: Métricas del sistema
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SYSTEM_HEALTH.value,
            message="",
            context={
                "system_name": system_name,
                "health_status": health_status,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_system_resource(
        self,
        system_name: str,
        resource_type: str,
        resource_name: str,
        resource_status: str,
        resource_metrics: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un recurso del sistema.
        
        Args:
            system_name: Nombre del sistema
            resource_type: Tipo de recurso
            resource_name: Nombre del recurso
            resource_status: Estado del recurso
            resource_metrics: Métricas del recurso
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SYSTEM_RESOURCE.value,
            message="",
            context={
                "system_name": system_name,
                "resource_type": resource_type,
                "resource_name": resource_name,
                "resource_status": resource_status,
                "resource_metrics": resource_metrics,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_system_configuration(
        self,
        system_name: str,
        configuration_type: str,
        configuration_changes: Dict[str, Any],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre cambios en la configuración del sistema.
        
        Args:
            system_name: Nombre del sistema
            configuration_type: Tipo de configuración
            configuration_changes: Cambios en la configuración
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SYSTEM_CONFIGURATION.value,
            message="",
            context={
                "system_name": system_name,
                "configuration_type": configuration_type,
                "configuration_changes": configuration_changes,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_system_dependency(
        self,
        system_name: str,
        dependency_name: str,
        dependency_type: str,
        dependency_status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el estado de una dependencia del sistema.
        
        Args:
            system_name: Nombre del sistema
            dependency_name: Nombre de la dependencia
            dependency_type: Tipo de dependencia
            dependency_status: Estado de la dependencia
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.SYSTEM_DEPENDENCY.value,
            message="",
            context={
                "system_name": system_name,
                "dependency_name": dependency_name,
                "dependency_type": dependency_type,
                "dependency_status": dependency_status,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de sistema
system_notifier = SystemNotificationService(BusinessUnit.objects.first()) 