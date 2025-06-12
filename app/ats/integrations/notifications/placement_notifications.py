"""
Servicio de notificaciones de colocaciones de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit, Placement
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class PlacementNotificationService(BaseNotificationService):
    """Servicio de notificaciones de colocaciones."""
    
    async def notify_new_placement(
        self,
        placement: Placement,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una nueva colocación.
        
        Args:
            placement: Objeto Placement
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.NEW_PLACEMENT.value,
            message="",
            context={
                "candidate_name": placement.candidate.full_name,
                "position": placement.position.title,
                "company": placement.company.name,
                "salary": placement.salary,
                "start_date": placement.start_date.isoformat() if placement.start_date else None
            },
            additional_data=additional_details
        )
    
    async def notify_placement_update(
        self,
        placement: Placement,
        update_type: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una actualización de colocación.
        
        Args:
            placement: Objeto Placement
            update_type: Tipo de actualización
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PLACEMENT_UPDATE.value,
            message="",
            context={
                "candidate_name": placement.candidate.full_name,
                "position": placement.position.title,
                "company": placement.company.name,
                "update_type": update_type
            },
            additional_data=additional_details
        )
    
    async def notify_placement_completion(
        self,
        placement: Placement,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la finalización de una colocación.
        
        Args:
            placement: Objeto Placement
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PLACEMENT_COMPLETION.value,
            message="",
            context={
                "candidate_name": placement.candidate.full_name,
                "position": placement.position.title,
                "company": placement.company.name,
                "end_date": placement.end_date.isoformat() if placement.end_date else None
            },
            additional_data=additional_details
        )
    
    async def notify_placement_cancellation(
        self,
        placement: Placement,
        reason: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la cancelación de una colocación.
        
        Args:
            placement: Objeto Placement
            reason: Razón de la cancelación
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PLACEMENT_CANCELLATION.value,
            message="",
            context={
                "candidate_name": placement.candidate.full_name,
                "position": placement.position.title,
                "company": placement.company.name,
                "reason": reason
            },
            additional_data=additional_details
        )
    
    async def notify_placement_payment(
        self,
        placement: Placement,
        amount: float,
        payment_type: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un pago de colocación.
        
        Args:
            placement: Objeto Placement
            amount: Monto del pago
            payment_type: Tipo de pago
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PLACEMENT_PAYMENT.value,
            message="",
            context={
                "candidate_name": placement.candidate.full_name,
                "position": placement.position.title,
                "company": placement.company.name,
                "amount": amount,
                "payment_type": payment_type
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de colocaciones
placement_notifier = PlacementNotificationService(BusinessUnit.objects.first()) 