"""
Servicio para gestionar entrevistas.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from django.utils import timezone

from app.models import Interview, Person, Vacante
from app.ats.integrations.notifications.process.interview_notifications import InterviewNotificationService
from app.ats.utils.location_tracker import LocationTracker
from app.tasks import (
    send_interview_notification_task,
    schedule_interview_tracking_task
)

logger = logging.getLogger(__name__)

class InterviewService:
    """
    Servicio para gestionar el proceso de entrevistas.
    """
    
    def __init__(self, business_unit):
        """
        Inicializa el servicio de entrevistas.
        
        Args:
            business_unit: Unidad de negocio
        """
        self.business_unit = business_unit
        self.notification_service = InterviewNotificationService(business_unit)
        self.location_tracker = LocationTracker()
        
    async def schedule_interview(
        self,
        person: Person,
        vacancy: Vacante,
        interview_date: datetime,
        interview_type: str,
        location: Optional[Dict[str, Any]] = None,
        additional_notes: str = ''
    ) -> Interview:
        """
        Programa una nueva entrevista.
        
        Args:
            person: Candidato a entrevistar
            vacancy: Vacante relacionada
            interview_date: Fecha y hora de la entrevista
            interview_type: Tipo de entrevista
            location: Información de ubicación
            additional_notes: Notas adicionales
            
        Returns:
            Interview: Entrevista creada
        """
        try:
            # Crear entrevista
            interview = await Interview.objects.acreate(
                person=person,
                vacancy=vacancy,
                interview_date=interview_date,
                interview_type=interview_type,
                location=location,
                notes=additional_notes,
                status='scheduled'
            )
            
            # Enviar notificaciones
            await self.notification_service.notify_interview_scheduled(
                person=person,
                vacancy=vacancy,
                interview_date=interview_date,
                interview_type=interview_type,
                location=location,
                additional_notes=additional_notes
            )
            
            # Programar seguimiento de ubicación
            await schedule_interview_tracking_task.delay(interview.id)
            
            return interview
            
        except Exception as e:
            logger.error(f"Error programando entrevista: {str(e)}")
            raise
            
    async def cancel_interview(
        self,
        interview: Interview,
        reason: str,
        cancelled_by: str
    ) -> bool:
        """
        Cancela una entrevista programada.
        
        Args:
            interview: Entrevista a cancelar
            reason: Razón de la cancelación
            cancelled_by: Quién canceló la entrevista
            
        Returns:
            bool: True si se canceló correctamente
        """
        try:
            # Actualizar estado
            interview.status = 'cancelled'
            interview.cancellation_reason = reason
            await interview.asave()
            
            # Enviar notificaciones
            await self.notification_service.notify_interview_cancelled(
                person=interview.person,
                vacancy=interview.vacancy,
                interview_date=interview.interview_date,
                reason=reason,
                cancelled_by=cancelled_by
            )
            
            # Detener seguimiento de ubicación
            await self.location_tracker.stop_location_tracking(interview.id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error cancelando entrevista: {str(e)}")
            return False
            
    async def reschedule_interview(
        self,
        interview: Interview,
        new_date: datetime,
        reason: str
    ) -> bool:
        """
        Reprograma una entrevista.
        
        Args:
            interview: Entrevista a reprogramar
            new_date: Nueva fecha y hora
            reason: Razón de la reprogramación
            
        Returns:
            bool: True si se reprogramó correctamente
        """
        try:
            # Actualizar fecha
            interview.interview_date = new_date
            interview.status = 'rescheduled'
            interview.notes = f"Reprogramada: {reason}\n{interview.notes}"
            await interview.asave()
            
            # Enviar notificaciones
            await self.notification_service.notify_interview_scheduled(
                person=interview.person,
                vacancy=interview.vacancy,
                interview_date=new_date,
                interview_type=interview.interview_type,
                location=interview.location,
                additional_notes=f"Reprogramada: {reason}"
            )
            
            # Reprogramar seguimiento de ubicación
            await schedule_interview_tracking_task.delay(interview.id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error reprogramando entrevista: {str(e)}")
            return False
            
    async def get_interview_status(self, interview_id: int) -> Dict[str, Any]:
        """
        Obtiene el estado actual de una entrevista.
        
        Args:
            interview_id: ID de la entrevista
            
        Returns:
            Dict con información del estado
        """
        try:
            interview = await Interview.objects.aget(id=interview_id)
            
            status = {
                'id': interview.id,
                'status': interview.status,
                'interview_date': interview.interview_date,
                'location_status': interview.location_status,
                'estimated_arrival': interview.estimated_arrival,
                'is_delayed': interview.is_delayed,
                'delay_minutes': interview.delay_minutes,
                'delay_reason': interview.delay_reason
            }
            
            if interview.current_location:
                status['current_location'] = {
                    'name': interview.current_location.get('name'),
                    'distance': await self.location_tracker.calculate_distance(
                        interview.current_location,
                        interview.location
                    )
                }
                
            return status
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de entrevista: {str(e)}")
            return None 