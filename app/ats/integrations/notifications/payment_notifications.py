"""
Servicio de notificaciones de pagos de Grupo huntRED®.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import BusinessUnit, Payment
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class PaymentNotificationService(BaseNotificationService):
    """Servicio de notificaciones de pagos."""
    
    async def notify_new_payment(
        self,
        payment: Payment,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un nuevo pago.
        
        Args:
            payment: Objeto Payment
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.NEW_PAYMENT.value,
            message="",
            context={
                "amount": payment.amount,
                "currency": payment.currency,
                "payment_type": payment.payment_type,
                "payment_method": payment.payment_method,
                "reference": payment.reference,
                "date": payment.date.isoformat() if payment.date else None
            },
            additional_data=additional_details
        )
    
    async def notify_payment_confirmation(
        self,
        payment: Payment,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre la confirmación de un pago.
        
        Args:
            payment: Objeto Payment
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PAYMENT_CONFIRMATION.value,
            message="",
            context={
                "amount": payment.amount,
                "currency": payment.currency,
                "payment_type": payment.payment_type,
                "payment_method": payment.payment_method,
                "reference": payment.reference,
                "confirmation_date": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_payment_rejection(
        self,
        payment: Payment,
        reason: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre el rechazo de un pago.
        
        Args:
            payment: Objeto Payment
            reason: Razón del rechazo
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PAYMENT_REJECTION.value,
            message="",
            context={
                "amount": payment.amount,
                "currency": payment.currency,
                "payment_type": payment.payment_type,
                "payment_method": payment.payment_method,
                "reference": payment.reference,
                "reason": reason,
                "rejection_date": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_payment_refund(
        self,
        payment: Payment,
        refund_amount: float,
        reason: str,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un reembolso de pago.
        
        Args:
            payment: Objeto Payment
            refund_amount: Monto del reembolso
            reason: Razón del reembolso
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PAYMENT_REFUND.value,
            message="",
            context={
                "original_amount": payment.amount,
                "refund_amount": refund_amount,
                "currency": payment.currency,
                "payment_type": payment.payment_type,
                "payment_method": payment.payment_method,
                "reference": payment.reference,
                "reason": reason,
                "refund_date": datetime.now().isoformat()
            },
            additional_data=additional_details
        )
    
    async def notify_payment_reminder(
        self,
        payment: Payment,
        days_overdue: int,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica sobre un recordatorio de pago.
        
        Args:
            payment: Objeto Payment
            days_overdue: Días de atraso
            additional_details: Detalles adicionales
        """
        return await self.send_notification(
            notification_type=NotificationType.PAYMENT_REMINDER.value,
            message="",
            context={
                "amount": payment.amount,
                "currency": payment.currency,
                "payment_type": payment.payment_type,
                "payment_method": payment.payment_method,
                "reference": payment.reference,
                "due_date": payment.due_date.isoformat() if payment.due_date else None,
                "days_overdue": days_overdue
            },
            additional_data=additional_details
        )

# Instancia global del servicio de notificaciones de pagos
payment_notifier = PaymentNotificationService(BusinessUnit.objects.first()) 