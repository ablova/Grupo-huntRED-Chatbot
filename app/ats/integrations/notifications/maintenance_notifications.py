"""
Servicio de notificaciones de mantenimiento de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class MaintenanceNotificationService(BaseNotificationService):
    """Servicio de notificaciones de mantenimiento."""
    
    async def notify_maintenance_scheduled(
        self,
        maintenance_name: str,
        maintenance_type: str,
        start_time: datetime,
        end_time: datetime,
        affected_systems: List[str],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un mantenimiento programado.
        
        Args:
            maintenance_name: Nombre del mantenimiento
            maintenance_type: Tipo de mantenimiento
            start_time: Hora de inicio
            end_time: Hora de fin
            affected_systems: Sistemas afectados
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.MAINTENANCE_SCHEDULED.value,
            message="",
            context={
                "maintenance_name": maintenance_name,
                "maintenance_type": maintenance_type,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "affected_systems": affected_systems,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_maintenance_start(
        self,
        maintenance_name: str,
        maintenance_type: str,
        affected_systems: List[str],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el inicio de un mantenimiento.
        
        Args:
            maintenance_name: Nombre del mantenimiento
            maintenance_type: Tipo de mantenimiento
            affected_systems: Sistemas afectados
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.MAINTENANCE_START.value,
            message="",
            context={
                "maintenance_name": maintenance_name,
                "maintenance_type": maintenance_type,
                "affected_systems": affected_systems,
                "start_time": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_maintenance_completion(
        self,
        maintenance_name: str,
        maintenance_type: str,
        affected_systems: List[str],
        status: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la finalización de un mantenimiento.
        
        Args:
            maintenance_name: Nombre del mantenimiento
            maintenance_type: Tipo de mantenimiento
            affected_systems: Sistemas afectados
            status: Estado del mantenimiento
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.MAINTENANCE_COMPLETION.value,
            message="",
            context={
                "maintenance_name": maintenance_name,
                "maintenance_type": maintenance_type,
                "affected_systems": affected_systems,
                "status": status,
                "completion_time": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_maintenance_delay(
        self,
        maintenance_name: str,
        maintenance_type: str,
        affected_systems: List[str],
        delay_reason: str,
        estimated_delay: int,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un retraso en el mantenimiento.
        
        Args:
            maintenance_name: Nombre del mantenimiento
            maintenance_type: Tipo de mantenimiento
            affected_systems: Sistemas afectados
            delay_reason: Razón del retraso
            estimated_delay: Retraso estimado en minutos
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.MAINTENANCE_DELAY.value,
            message="",
            context={
                "maintenance_name": maintenance_name,
                "maintenance_type": maintenance_type,
                "affected_systems": affected_systems,
                "delay_reason": delay_reason,
                "estimated_delay": estimated_delay,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_maintenance_cancellation(
        self,
        maintenance_name: str,
        maintenance_type: str,
        affected_systems: List[str],
        cancellation_reason: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la cancelación de un mantenimiento.
        
        Args:
            maintenance_name: Nombre del mantenimiento
            maintenance_type: Tipo de mantenimiento
            affected_systems: Sistemas afectados
            cancellation_reason: Razón de la cancelación
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.MAINTENANCE_CANCELLATION.value,
            message="",
            context={
                "maintenance_name": maintenance_name,
                "maintenance_type": maintenance_type,
                "affected_systems": affected_systems,
                "cancellation_reason": cancellation_reason,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de mantenimiento
maintenance_notifier = MaintenanceNotificationService(BusinessUnit.objects.first()) 