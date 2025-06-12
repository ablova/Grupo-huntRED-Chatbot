"""
Módulo de notificaciones específicas para el proceso de ofertas.
Maneja todas las notificaciones relacionadas con ofertas laborales y contrataciones.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import Person, Vacante, BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import (
    NotificationType,
    NotificationSeverity
)

logger = logging.getLogger(__name__)

class OfferNotificationService(BaseNotificationService):
    """
    Servicio de notificaciones para el proceso de ofertas.
    Extiende el servicio base con funcionalidad específica para ofertas.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el servicio de notificaciones de ofertas.
        
        Args:
            business_unit: Unidad de negocio requerida para las notificaciones
        """
        if not business_unit:
            raise ValueError("Se requiere especificar una unidad de negocio")
            
        super().__init__(business_unit)
        
    async def notify_offer_made(
        self,
        person: Person,
        vacancy: Vacante,
        offer_details: Dict[str, Any],
        deadline: datetime
    ) -> bool:
        """
        Notifica sobre una oferta laboral realizada.
        
        Args:
            person: Candidato que recibe la oferta
            vacancy: Vacante relacionada
            offer_details: Detalles de la oferta
            deadline: Fecha límite para aceptar la oferta
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            # Preparar contexto
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'salary': offer_details.get('salary', ''),
                'benefits': offer_details.get('benefits', []),
                'start_date': offer_details.get('start_date', ''),
                'deadline': deadline.strftime('%d/%m/%Y %H:%M'),
                'business_unit': self.business_unit.name
            }
            
            # Notificar al candidato
            await self.send_notification(
                notification_type=NotificationType.PROCESS_EVENT.value,
                message=self._get_offer_made_template('candidate'),
                context=context,
                channels=['email', 'whatsapp']
            )
            
            # Notificar al consultor
            if vacancy.assigned_consultant:
                await self.send_notification(
                    notification_type=NotificationType.PROCESS_EVENT.value,
                    message=self._get_offer_made_template('consultant'),
                    context=context,
                    channels=['email', 'telegram']
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error notificando oferta realizada: {str(e)}", exc_info=True)
            return False
            
    async def notify_offer_accepted(
        self,
        person: Person,
        vacancy: Vacante,
        acceptance_date: datetime
    ) -> bool:
        """
        Notifica sobre la aceptación de una oferta.
        
        Args:
            person: Candidato que aceptó la oferta
            vacancy: Vacante relacionada
            acceptance_date: Fecha de aceptación
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'acceptance_date': acceptance_date.strftime('%d/%m/%Y %H:%M'),
                'business_unit': self.business_unit.name
            }
            
            # Notificar al consultor
            if vacancy.assigned_consultant:
                await self.send_notification(
                    notification_type=NotificationType.PROCESS_EVENT.value,
                    message=self._get_offer_accepted_template('consultant'),
                    context=context,
                    channels=['email', 'telegram']
                )
            
            # Notificar al cliente
            await self.send_notification(
                notification_type=NotificationType.PROCESS_EVENT.value,
                message=self._get_offer_accepted_template('client'),
                context=context,
                channels=['email']
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error notificando aceptación de oferta: {str(e)}", exc_info=True)
            return False
            
    async def notify_offer_declined(
        self,
        person: Person,
        vacancy: Vacante,
        reason: str
    ) -> bool:
        """
        Notifica sobre el rechazo de una oferta.
        
        Args:
            person: Candidato que rechazó la oferta
            vacancy: Vacante relacionada
            reason: Razón del rechazo
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'reason': reason,
                'business_unit': self.business_unit.name
            }
            
            # Notificar al consultor
            if vacancy.assigned_consultant:
                await self.send_notification(
                    notification_type=NotificationType.PROCESS_EVENT.value,
                    message=self._get_offer_declined_template('consultant'),
                    context=context,
                    channels=['email', 'telegram']
                )
            
            # Notificar al cliente
            await self.send_notification(
                notification_type=NotificationType.PROCESS_EVENT.value,
                message=self._get_offer_declined_template('client'),
                context=context,
                channels=['email']
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error notificando rechazo de oferta: {str(e)}", exc_info=True)
            return False
            
    def _get_offer_made_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'candidate': (
                "🎉 *¡Oferta Laboral!*\n\n"
                "👋 *{candidate_name}*\n\n"
                "¡Felicitaciones! Has recibido una oferta para la posición de {position} en {company}.\n\n"
                "💰 *Salario:* {salary}\n"
                "🎁 *Beneficios:*\n{benefits}\n"
                "📅 *Fecha de inicio:* {start_date}\n"
                "⏰ *Fecha límite para aceptar:* {deadline}\n\n"
                "Por favor, revisa los detalles y comunica tu decisión antes de la fecha límite."
            ),
            'consultant': (
                "🎉 *Nueva Oferta Realizada*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "💰 *Salario:* {salary}\n"
                "🎁 *Beneficios:*\n{benefits}\n"
                "📅 *Fecha de inicio:* {start_date}\n"
                "⏰ *Fecha límite:* {deadline}"
            )
        }
        return templates.get(recipient_type, templates['candidate'])
        
    def _get_offer_accepted_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'consultant': (
                "✅ *Oferta Aceptada*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📅 *Fecha de aceptación:* {acceptance_date}"
            ),
            'client': (
                "✅ *Oferta Aceptada*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "📅 *Fecha de aceptación:* {acceptance_date}\n\n"
                "¡Felicitaciones! El candidato ha aceptado la oferta."
            )
        }
        return templates.get(recipient_type, templates['consultant'])
        
    def _get_offer_declined_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'consultant': (
                "❌ *Oferta Rechazada*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📝 *Razón:* {reason}"
            ),
            'client': (
                "❌ *Oferta Rechazada*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "📝 *Razón:* {reason}\n\n"
                "El candidato ha declinado la oferta. Por favor, revisa los detalles para futuras referencias."
            )
        }
        return templates.get(recipient_type, templates['consultant'])
