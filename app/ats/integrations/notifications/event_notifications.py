"""
Servicio de notificaciones de eventos de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class EventNotificationService(BaseNotificationService):
    """Servicio de notificaciones de eventos."""
    
    async def notify_event(
        self,
        event_name: str,
        event_type: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un evento.
        
        Args:
            event_name: Nombre del evento
            event_type: Tipo de evento
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.EVENT.value,
            message="",
            context={
                "event_name": event_name,
                "event_type": event_type,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_event_batch(
        self,
        events: List[Dict[str, Any]],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un lote de eventos.
        
        Args:
            events: Lista de eventos
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.EVENT_BATCH.value,
            message="",
            context={
                "events": events,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_event_alert(
        self,
        event_name: str,
        event_type: str,
        severity: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una alerta de evento.
        
        Args:
            event_name: Nombre del evento
            event_type: Tipo de evento
            severity: Severidad de la alerta
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.EVENT_ALERT.value,
            message="",
            context={
                "event_name": event_name,
                "event_type": event_type,
                "severity": severity,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_event_summary(
        self,
        period: str,
        events: List[Dict[str, Any]],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un resumen de eventos.
        
        Args:
            period: Período del resumen
            events: Lista de eventos
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.EVENT_SUMMARY.value,
            message="",
            context={
                "period": period,
                "events": events,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_event_trend(
        self,
        event_type: str,
        current_count: int,
        previous_count: int,
        trend: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre una tendencia de eventos.
        
        Args:
            event_type: Tipo de evento
            current_count: Conteo actual
            previous_count: Conteo anterior
            trend: Tendencia (up, down, stable)
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.EVENT_TREND.value,
            message="",
            context={
                "event_type": event_type,
                "current_count": current_count,
                "previous_count": previous_count,
                "trend": trend,
                "timestamp": datetime.now().isoformat()
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de eventos
event_notifier = EventNotificationService(BusinessUnit.objects.first()) 