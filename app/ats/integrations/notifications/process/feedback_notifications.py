# /home/pablo/app/ats/integrations/notifications/process/feedback_notifications.py
"""
Módulo de notificaciones específicas para el proceso de feedback.
Maneja todas las notificaciones relacionadas con la solicitud y recepción de feedback.
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

class FeedbackNotificationService(BaseNotificationService):
    """
    Servicio de notificaciones para el proceso de feedback.
    Extiende el servicio base con funcionalidad específica para feedback.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el servicio de notificaciones de feedback.
        
        Args:
            business_unit: Unidad de negocio requerida para las notificaciones
        """
        if not business_unit:
            raise ValueError("Se requiere especificar una unidad de negocio")
            
        super().__init__(business_unit)
        
    async def request_interview_feedback(
        self,
        person: Person,
        vacancy: Vacante,
        interview_date: datetime,
        interviewer: str,
        deadline: datetime
    ) -> bool:
        """
        Solicita feedback sobre una entrevista.
        
        Args:
            person: Candidato entrevistado
            vacancy: Vacante relacionada
            interview_date: Fecha de la entrevista
            interviewer: Nombre del entrevistador
            deadline: Fecha límite para enviar el feedback
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'interview_date': interview_date.strftime('%d/%m/%Y %H:%M'),
                'interviewer': interviewer,
                'deadline': deadline.strftime('%d/%m/%Y %H:%M'),
                'business_unit': self.business_unit.name
            }
            
            # Notificar al entrevistador
            await self.send_notification(
                notification_type=NotificationType.FEEDBACK_REQUEST.value,
                message=self._get_feedback_request_template('interviewer'),
                context=context,
                channels=['email', 'telegram']
            )
            
            # Notificar al consultor
            if vacancy.assigned_consultant:
                await self.send_notification(
                    notification_type=NotificationType.FEEDBACK_REQUEST.value,
                    message=self._get_feedback_request_template('consultant'),
                    context=context,
                    channels=['email', 'telegram']
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error solicitando feedback de entrevista: {str(e)}", exc_info=True)
            return False
            
    async def notify_feedback_received(
        self,
        person: Person,
        vacancy: Vacante,
        feedback: Dict[str, Any],
        feedback_type: str = 'interview'
    ) -> bool:
        """
        Notifica sobre la recepción de feedback.
        
        Args:
            person: Candidato evaluado
            vacancy: Vacante relacionada
            feedback: Contenido del feedback
            feedback_type: Tipo de feedback
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'feedback_type': feedback_type,
                'evaluation': feedback.get('evaluation', ''),
                'strengths': feedback.get('strengths', []),
                'areas_for_improvement': feedback.get('areas_for_improvement', []),
                'recommendation': feedback.get('recommendation', ''),
                'business_unit': self.business_unit.name
            }
            
            # Notificar al consultor
            if vacancy.assigned_consultant:
                await self.send_notification(
                    notification_type=NotificationType.FEEDBACK_RECEIVED.value,
                    message=self._get_feedback_received_template('consultant'),
                    context=context,
                    channels=['email', 'telegram']
                )
            
            # Notificar al candidato si es apropiado
            if feedback_type == 'final' and feedback.get('share_with_candidate', False):
                await self.send_notification(
                    notification_type=NotificationType.FEEDBACK_RECEIVED.value,
                    message=self._get_feedback_received_template('candidate'),
                    context=context,
                    channels=['email']
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error notificando recepción de feedback: {str(e)}", exc_info=True)
            return False
            
    async def send_feedback_reminder(
        self,
        person: Person,
        vacancy: Vacante,
        interviewer: str,
        deadline: datetime
    ) -> bool:
        """
        Envía un recordatorio para enviar feedback.
        
        Args:
            person: Candidato evaluado
            vacancy: Vacante relacionada
            interviewer: Nombre del entrevistador
            deadline: Fecha límite para enviar el feedback
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'interviewer': interviewer,
                'deadline': deadline.strftime('%d/%m/%Y %H:%M'),
                'business_unit': self.business_unit.name
            }
            
            await self.send_notification(
                notification_type=NotificationType.REMINDER.value,
                message=self._get_feedback_reminder_template(),
                context=context,
                channels=['email', 'telegram']
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error enviando recordatorio de feedback: {str(e)}", exc_info=True)
            return False
            
    def _get_feedback_request_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'interviewer': (
                "📝 *Solicitud de Feedback*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📅 *Fecha de entrevista:* {interview_date}\n"
                "⏰ *Fecha límite:* {deadline}\n\n"
                "Por favor, completa el formulario de feedback antes de la fecha límite."
            ),
            'consultant': (
                "📝 *Solicitud de Feedback Enviada*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "👥 *Entrevistador:* {interviewer}\n"
                "📅 *Fecha de entrevista:* {interview_date}\n"
                "⏰ *Fecha límite:* {deadline}"
            )
        }
        return templates.get(recipient_type, templates['interviewer'])
        
    def _get_feedback_received_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'consultant': (
                "📋 *Feedback Recibido*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📝 *Tipo:* {feedback_type}\n\n"
                "📊 *Evaluación:* {evaluation}\n"
                "✅ *Fortalezas:*\n{strengths}\n"
                "📈 *Áreas de mejora:*\n{areas_for_improvement}\n"
                "💡 *Recomendación:* {recommendation}"
            ),
            'candidate': (
                "📋 *Feedback de Evaluación*\n\n"
                "👋 *{candidate_name}*\n\n"
                "Hemos recibido el feedback de tu evaluación para {position} en {company}.\n\n"
                "📊 *Evaluación:* {evaluation}\n"
                "✅ *Fortalezas:*\n{strengths}\n"
                "📈 *Áreas de mejora:*\n{areas_for_improvement}\n"
                "💡 *Recomendación:* {recommendation}"
            )
        }
        return templates.get(recipient_type, templates['consultant'])
        
    def _get_feedback_reminder_template(self) -> str:
        """Obtiene la plantilla para recordatorio de feedback."""
        return (
            "⏰ *Recordatorio de Feedback*\n\n"
            "👤 *Candidato:* {candidate_name}\n"
            "💼 *Posición:* {position}\n"
            "🏢 *Empresa:* {company}\n"
            "👥 *Entrevistador:* {interviewer}\n"
            "⏰ *Fecha límite:* {deadline}\n\n"
            "Por favor, completa el formulario de feedback antes de la fecha límite."
        )
