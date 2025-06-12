"""
Servicio de notificaciones para el proceso de onboarding.
"""
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from app.models import BusinessUnit, Person, OnboardingProcess, OnboardingTask
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import NotificationType

logger = logging.getLogger('notifications')

class OnboardingNotificationService(BaseNotificationService):
    """Servicio de notificaciones para el proceso de onboarding."""
    
    async def notify_onboarding_started(
        self,
        onboarding_id: int,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica el inicio del proceso de onboarding.
        
        Args:
            onboarding_id: ID del proceso de onboarding
            additional_data: Datos adicionales
        """
        try:
            process = OnboardingProcess.objects.get(id=onboarding_id)
            person = process.person
            
            # Preparar contexto
            context = {
                'person': person,
                'vacancy': process.vacancy,
                'hire_date': process.hire_date,
                'tasks': OnboardingTask.objects.filter(onboarding=process).order_by('due_date'),
                'dashboard_url': f"{self.business_unit.dashboard_url}/onboarding/{onboarding_id}"
            }
            
            # Enviar notificación
            return await self.send_notification(
                notification_type=NotificationType.ONBOARDING_STARTED.value,
                message=self._get_welcome_message(person),
                context=context,
                additional_data=additional_data
            )
            
        except Exception as e:
            logger.error(f"Error notificando inicio de onboarding: {str(e)}")
            return {'success': False, 'error': str(e)}
            
    async def notify_task_reminder(
        self,
        task_id: int,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Envía recordatorio de tarea pendiente.
        
        Args:
            task_id: ID de la tarea
            additional_data: Datos adicionales
        """
        try:
            task = OnboardingTask.objects.get(id=task_id)
            process = task.onboarding
            person = process.person
            
            # Preparar contexto
            context = {
                'task': task,
                'person': person,
                'days_remaining': (task.due_date - datetime.now()).days,
                'dashboard_url': f"{self.business_unit.dashboard_url}/onboarding/{process.id}"
            }
            
            # Enviar notificación
            return await self.send_notification(
                notification_type=NotificationType.ONBOARDING_TASK_REMINDER.value,
                message=self._get_task_reminder_message(task),
                context=context,
                additional_data=additional_data
            )
            
        except Exception as e:
            logger.error(f"Error enviando recordatorio de tarea: {str(e)}")
            return {'success': False, 'error': str(e)}
            
    async def notify_satisfaction_survey(
        self,
        onboarding_id: int,
        period: int,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica encuesta de satisfacción.
        
        Args:
            onboarding_id: ID del proceso de onboarding
            period: Período de la encuesta
            additional_data: Datos adicionales
        """
        try:
            process = OnboardingProcess.objects.get(id=onboarding_id)
            person = process.person
            
            # Preparar contexto
            context = {
                'person': person,
                'period': period,
                'survey_url': f"{self.business_unit.dashboard_url}/onboarding/{onboarding_id}/survey/{period}",
                'days_since_start': (datetime.now() - process.hire_date).days
            }
            
            # Enviar notificación
            return await self.send_notification(
                notification_type=NotificationType.ONBOARDING_SATISFACTION_SURVEY.value,
                message=self._get_survey_message(period),
                context=context,
                additional_data=additional_data
            )
            
        except Exception as e:
            logger.error(f"Error notificando encuesta de satisfacción: {str(e)}")
            return {'success': False, 'error': str(e)}
            
    async def notify_low_satisfaction(
        self,
        onboarding_id: int,
        period: int,
        score: float,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Notifica baja satisfacción en el proceso.
        
        Args:
            onboarding_id: ID del proceso de onboarding
            period: Período de la encuesta
            score: Puntuación de satisfacción
            additional_data: Datos adicionales
        """
        try:
            process = OnboardingProcess.objects.get(id=onboarding_id)
            person = process.person
            
            # Preparar contexto
            context = {
                'person': person,
                'period': period,
                'score': score,
                'dashboard_url': f"{self.business_unit.dashboard_url}/onboarding/{onboarding_id}",
                'days_since_start': (datetime.now() - process.hire_date).days
            }
            
            # Enviar notificación
            return await self.send_notification(
                notification_type=NotificationType.ONBOARDING_LOW_SATISFACTION.value,
                message=self._get_low_satisfaction_message(score),
                context=context,
                additional_data=additional_data
            )
            
        except Exception as e:
            logger.error(f"Error notificando baja satisfacción: {str(e)}")
            return {'success': False, 'error': str(e)}
            
    def _get_welcome_message(self, person: Person) -> str:
        """Genera mensaje de bienvenida."""
        return f"¡Bienvenido/a {person.first_name}! Tu proceso de onboarding ha comenzado."
        
    def _get_task_reminder_message(self, task: OnboardingTask) -> str:
        """Genera mensaje de recordatorio de tarea."""
        days = (task.due_date - datetime.now()).days
        return f"Recordatorio: Tienes pendiente la tarea '{task.title}' ({days} días restantes)."
        
    def _get_survey_message(self, period: int) -> str:
        """Genera mensaje para encuesta de satisfacción."""
        return f"Es momento de tu encuesta de satisfacción del período {period}."
        
    def _get_low_satisfaction_message(self, score: float) -> str:
        """Genera mensaje de alerta por baja satisfacción."""
        return f"Alerta: Se ha detectado baja satisfacción en el proceso (puntuación: {score})." 