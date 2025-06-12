"""
Módulo de notificaciones específicas para el proceso de screening.
Maneja todas las notificaciones relacionadas con la evaluación inicial de candidatos.
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

class ScreeningNotificationService(BaseNotificationService):
    """
    Servicio de notificaciones para el proceso de screening.
    Extiende el servicio base con funcionalidad específica para screening.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el servicio de notificaciones de screening.
        
        Args:
            business_unit: Unidad de negocio requerida para las notificaciones
        """
        if not business_unit:
            raise ValueError("Se requiere especificar una unidad de negocio")
            
        super().__init__(business_unit)
        
    async def notify_screening_started(
        self,
        person: Person,
        vacancy: Vacante,
        screening_type: str = 'inicial',
        additional_notes: str = ''
    ) -> bool:
        """
        Notifica sobre el inicio del proceso de screening.
        
        Args:
            person: Candidato a evaluar
            vacancy: Vacante relacionada
            screening_type: Tipo de screening
            additional_notes: Notas adicionales
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            # Preparar contexto
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'screening_type': screening_type,
                'additional_notes': additional_notes,
                'business_unit': self.business_unit.name
            }
            
            # Notificar al candidato
            await self.send_notification(
                notification_type=NotificationType.PROCESS_EVENT.value,
                message=self._get_screening_start_template('candidate'),
                context=context,
                channels=['email', 'whatsapp']
            )
            
            # Notificar al consultor
            if vacancy.assigned_consultant:
                await self.send_notification(
                    notification_type=NotificationType.PROCESS_EVENT.value,
                    message=self._get_screening_start_template('consultant'),
                    context=context,
                    channels=['email', 'telegram']
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error notificando inicio de screening: {str(e)}", exc_info=True)
            return False
            
    async def notify_screening_completed(
        self,
        person: Person,
        vacancy: Vacante,
        result: str,
        feedback: str,
        screening_type: str = 'inicial'
    ) -> bool:
        """
        Notifica sobre la finalización del proceso de screening.
        
        Args:
            person: Candidato evaluado
            vacancy: Vacante relacionada
            result: Resultado del screening
            feedback: Feedback del screening
            screening_type: Tipo de screening
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            # Preparar contexto
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'screening_type': screening_type,
                'result': result,
                'feedback': feedback,
                'business_unit': self.business_unit.name
            }
            
            # Notificar al candidato
            await self.send_notification(
                notification_type=NotificationType.PROCESS_EVENT.value,
                message=self._get_screening_complete_template('candidate'),
                context=context,
                channels=['email', 'whatsapp']
            )
            
            # Notificar al consultor
            if vacancy.assigned_consultant:
                await self.send_notification(
                    notification_type=NotificationType.PROCESS_EVENT.value,
                    message=self._get_screening_complete_template('consultant'),
                    context=context,
                    channels=['email', 'telegram']
                )
            
            # Notificar al cliente si es necesario
            if result.lower() == 'aprobado':
                await self.send_notification(
                    notification_type=NotificationType.PROCESS_EVENT.value,
                    message=self._get_screening_complete_template('client'),
                    context=context,
                    channels=['email']
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error notificando finalización de screening: {str(e)}", exc_info=True)
            return False
            
    def _get_screening_start_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'candidate': (
                "👋 *{candidate_name}*\n\n"
                "Hemos iniciado el proceso de evaluación {screening_type} para la posición de {position} en {company}.\n\n"
                "{additional_notes}"
            ),
            'consultant': (
                "📋 *Inicio de Screening*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📝 *Tipo:* {screening_type}\n\n"
                "{additional_notes}"
            )
        }
        return templates.get(recipient_type, templates['candidate'])
        
    def _get_screening_complete_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'candidate': (
                "📋 *Resultado de Evaluación*\n\n"
                "Hemos completado tu evaluación {screening_type} para {position} en {company}.\n\n"
                "📊 *Resultado:* {result}\n"
                "💬 *Feedback:* {feedback}"
            ),
            'consultant': (
                "📋 *Screening Completado*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📝 *Tipo:* {screening_type}\n"
                "📊 *Resultado:* {result}\n"
                "💬 *Feedback:* {feedback}"
            ),
            'client': (
                "📋 *Candidato Aprobado en Screening*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "📝 *Tipo de Evaluación:* {screening_type}\n"
                "💬 *Feedback:* {feedback}"
            )
        }
        return templates.get(recipient_type, templates['candidate']) 