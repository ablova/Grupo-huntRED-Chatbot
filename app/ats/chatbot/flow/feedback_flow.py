# /home/pablo/app/ats/chatbot/flow/feedback_flow.py
from typing import Dict, Any, Optional
from django.utils import timezone
from datetime import timedelta
import logging

from app.models import Person, BusinessUnit, Vacante
from app.ats.feedback.feedback_models import SkillFeedback
from app.ats.notifications.notification_manager import SkillFeedbackNotificationManager
from app.ats.chatbot.flow.conversational_flow import ConversationalFlowManager
# TODO: Implementar notificadores específicos
# from app.ats.notifications.specific_notifications import (
#     placement_notifier, payment_notifier,
#     process_notifier, metrics_notifier, event_notifier,
#     alert_notifier
# )
from app.ats.integrations.notifications.user_notifications import get_user_notifier

logger = logging.getLogger(__name__)

class FeedbackFlowManager(ConversationalFlowManager):
    """
    Gestor de flujo para el feedback de habilidades.
    Integra notificaciones multicanal y seguimiento del proceso.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        super().__init__(business_unit)
        self.notification_manager = SkillFeedbackNotificationManager(business_unit)
        
        # Inicializar notificadores específicos
        self.user_notifier = get_user_notifier()
        # TODO: Implementar notificadores específicos
        # self.process_notifier = process_notifier(business_unit)
        # self.event_notifier = event_notifier(business_unit)
        # self.alert_notifier = alert_notifier(business_unit)
        
    async def handle_feedback_request(self, person: Person, vacante: Vacante, candidate: Person) -> Dict[str, Any]:
        """
        Maneja la solicitud de feedback, enviando notificaciones por múltiples canales.
        """
        try:
            # Crear o obtener el feedback
            feedback, created = await SkillFeedback.objects.aget_or_create(
                vacante=vacante,
                candidate=candidate,
                defaults={
                    'created_by': person,
                    'business_unit': self.business_unit
                }
            )
            
            # Configurar notificaciones multicanal
            notification_channels = ['whatsapp', 'email', 'app']
            deadline = timezone.now() + timedelta(days=2)
            
            # Enviar notificaciones por cada canal
            for channel in notification_channels:
                try:
                    await self.notification_manager.notify_feedback_required(
                        recipient=person,
                        vacante=vacante,
                        candidate=candidate,
                        skills=feedback.detected_skills,
                        deadline=deadline
                    )
                    logger.info(f"Notification sent via {channel} for feedback request")
                except Exception as e:
                    logger.error(f"Error sending notification via {channel}: {str(e)}")
            
            # Programar recordatorios
            await self._schedule_reminders(person, vacante, candidate, feedback)
            
            # TODO: Implementar notificadores específicos
            # # Notificar inicio del proceso de feedback
            # await self.process_notifier.notify_process_start(
            #     recipient=person,
            #     process_type='feedback_request',
            #     process_id=str(feedback.id)
            # )
            # 
            # # Notificar evento del sistema
            # await self.event_notifier.notify_system_event(
            #     recipient=person,
            #     event_name='feedback_requested',
            #     event_type='feedback_event',
            #     event_data={
            #         'feedback_id': feedback.id,
            #         'vacante_id': vacante.id,
            #         'candidate_id': candidate.id
            #     }
            # )
            
            return {
                'success': True,
                'feedback_id': feedback.id,
                'channels_notified': notification_channels
            }
            
        except Exception as e:
            logger.error(f"Error handling feedback request: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _schedule_reminders(self, person: Person, vacante: Vacante, candidate: Person, feedback: SkillFeedback):
        """
        Programa recordatorios automáticos para el feedback.
        """
        reminder_times = [
            timezone.now() + timedelta(hours=12),  # Recordatorio a las 12 horas
            timezone.now() + timedelta(hours=24),  # Recordatorio a las 24 horas
            timezone.now() + timedelta(hours=36)   # Recordatorio a las 36 horas
        ]
        
        for reminder_time in reminder_times:
            try:
                await self.notification_manager.schedule_notification(
                    notification_type='SKILL_FEEDBACK_REQUERIDO',
                    recipient=person,
                    scheduled_time=reminder_time,
                    vacante=vacante,
                    context={
                        'candidate_name': candidate.nombre,
                        'vacante_title': vacante.titulo,
                        'is_reminder': True,
                        'hours_remaining': int((reminder_time - timezone.now()).total_seconds() / 3600)
                    }
                )
            except Exception as e:
                logger.error(f"Error scheduling reminder: {str(e)}")
    
    async def handle_feedback_completion(self, person: Person, vacante: Vacante, candidate: Person, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja la finalización del feedback, enviando notificaciones y actualizando el estado.
        """
        try:
            feedback = await SkillFeedback.objects.aget(
                vacante=vacante,
                candidate=candidate
            )
            
            # Actualizar el feedback
            for key, value in feedback_data.items():
                setattr(feedback, key, value)
            feedback.updated_by = person
            feedback.updated_at = timezone.now()
            await feedback.asave()
            
            # Enviar notificación de completado
            await self.notification_manager.notify_feedback_completed(
                recipient=person,
                vacante=vacante,
                candidate=candidate,
                feedback_data=feedback_data
            )
            
            # TODO: Implementar notificadores específicos
            # # Notificar finalización del proceso
            # await self.process_notifier.notify_process_start(
            #     recipient=person,
            #     process_type='feedback_completed',
            #     process_id=str(feedback.id)
            # )
            # 
            # # Notificar evento del sistema
            # await self.event_notifier.notify_system_event(
            #     recipient=person,
            #     event_name='feedback_completed',
            #     event_type='feedback_event',
            #     event_data={
            #             'feedback_id': feedback.id,
            #             'vacante_id': vacante.id,
            #             'candidate_id': candidate.id,
            #             'feedback_data': feedback_data
            #         }
            # )
            # 
            # # Si hay habilidades críticas, enviar alerta
            # if feedback_data.get('critical_skills'):
            #     await self.alert_notifier.notify_system_alert(
            #         recipient=person,
            #         alert_type='critical_skills',
            #         alert_message=f"Habilidades críticas detectadas para {candidate.name}",
            #         severity='high'
            #     )
            
            return {
                'success': True,
                'feedback_id': feedback.id,
                'notifications_sent': True
            }
            
        except Exception as e:
            logger.error(f"Error handling feedback completion: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def check_feedback_status(self, person: Person, vacante: Vacante, candidate: Person) -> Dict[str, Any]:
        """
        Verifica el estado del feedback y envía recordatorios si es necesario.
        """
        try:
            feedback = await SkillFeedback.objects.aget(
                vacante=vacante,
                candidate=candidate
            )
            
            # Si el feedback está pendiente y han pasado más de 24 horas
            if not feedback.is_completed and (timezone.now() - feedback.created_at) > timedelta(hours=24):
                # Enviar alerta de recordatorio urgente
                await self.alert_notifier.notify_system_alert(
                    recipient=person,
                    alert_type='feedback_reminder',
                    alert_message=f"Recordatorio urgente de feedback para {candidate.name}",
                    severity='medium'
                )
                
                return {
                    'status': 'pending',
                    'hours_pending': int((timezone.now() - feedback.created_at).total_seconds() / 3600),
                    'reminder_sent': True
                }
            
            return {
                'status': 'completed' if feedback.is_completed else 'pending',
                'last_update': feedback.updated_at
            }
            
        except SkillFeedback.DoesNotExist:
            return {
                'status': 'not_found'
            }
        except Exception as e:
            logger.error(f"Error checking feedback status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            } 