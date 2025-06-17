"""
Servicio unificado para el tracking de entrevistas.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone

from app.models import Interview, Person, Vacante
from app.ats.integrations.notifications.process.interview_notifications import InterviewNotificationService
from app.ats.utils.location_tracker import LocationTracker

logger = logging.getLogger(__name__)

class InterviewTrackingService:
    """
    Servicio unificado para el seguimiento de entrevistas.
    """
    
    def __init__(self, business_unit):
        self.business_unit = business_unit
        self.notification_service = InterviewNotificationService(business_unit)
        self.location_tracker = LocationTracker()
        
    async def start_tracking(self, interview_id: int) -> bool:
        """
        Inicia el seguimiento de una entrevista.
        
        Args:
            interview_id: ID de la entrevista
            
        Returns:
            bool: True si se inició correctamente
        """
        try:
            interview = await Interview.objects.aget(id=interview_id)
            
            # Verificar que la entrevista sea presencial
            if interview.interview_type != 'presencial':
                logger.info(f"Entrevista {interview_id} no es presencial, no se requiere tracking")
                return True
                
            # Iniciar tracking
            interview.tracking_started = timezone.now()
            interview.status = 'in_progress'
            await interview.asave()
            
            # Enviar notificación inicial
            await self.notification_service.notify_interview_scheduled(
                person=interview.person,
                vacancy=interview.vacancy,
                interview_date=interview.interview_date,
                interview_type=interview.interview_type,
                location=interview.location
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error iniciando tracking: {str(e)}")
            return False
            
    async def update_location(self, interview_id: int) -> bool:
        """
        Actualiza la ubicación del candidato.
        
        Args:
            interview_id: ID de la entrevista
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            interview = await Interview.objects.aget(id=interview_id)
            
            # Obtener ubicación actual
            current_location = await self.location_tracker.get_current_location(interview.person)
            
            # Calcular distancia y tiempo estimado
            distance = await self.location_tracker.calculate_distance(
                current_location,
                interview.location
            )
            
            # Determinar estado
            if distance < 1:  # Menos de 1 km
                status = 'cerca'
            elif distance < 5:  # Menos de 5 km
                status = 'en_traslado'
            else:
                status = 'llegando_tarde'
                
            # Calcular tiempo estimado de llegada
            estimated_arrival = await self.location_tracker.estimate_arrival_time(
                current_location,
                interview.location,
                interview.interview_date
            )
            
            # Actualizar estado
            interview.current_location = current_location
            interview.location_status = status
            interview.estimated_arrival = estimated_arrival
            interview.last_location_update = timezone.now()
            
            # Agregar al historial
            if not interview.location_history:
                interview.location_history = []
            interview.location_history.append({
                'timestamp': timezone.now().isoformat(),
                'location': current_location,
                'distance': distance,
                'status': status,
                'eta': estimated_arrival.isoformat() if estimated_arrival else None
            })
            
            await interview.asave()
            
            # Enviar notificación
            await self.notification_service.notify_candidate_location_update(
                person=interview.person,
                vacancy=interview.vacancy,
                interview_date=interview.interview_date,
                location=current_location,
                status=status,
                estimated_arrival=estimated_arrival
            )
            
            # Verificar retraso
            if estimated_arrival and estimated_arrival > interview.interview_date:
                delay_minutes = int((estimated_arrival - interview.interview_date).total_seconds() / 60)
                await self._handle_delay(interview, delay_minutes)
            
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando ubicación: {str(e)}")
            return False
            
    async def stop_tracking(self, interview_id: int) -> bool:
        """
        Detiene el seguimiento de una entrevista.
        
        Args:
            interview_id: ID de la entrevista
            
        Returns:
            bool: True si se detuvo correctamente
        """
        try:
            interview = await Interview.objects.aget(id=interview_id)
            
            interview.tracking_ended = timezone.now()
            await interview.asave()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deteniendo tracking: {str(e)}")
            return False
            
    async def _handle_delay(self, interview: Interview, delay_minutes: int) -> None:
        """
        Maneja un retraso en la entrevista.
        
        Args:
            interview: Entrevista
            delay_minutes: Minutos de retraso
        """
        try:
            # Actualizar estado
            interview.delay_minutes = delay_minutes
            interview.delay_reason = "Tráfico o distancia"
            await interview.asave()
            
            # Notificar retraso
            await self.notification_service.notify_interview_delay(
                person=interview.person,
                vacancy=interview.vacancy,
                interview_date=interview.interview_date,
                delay_minutes=delay_minutes,
                reason=interview.delay_reason
            )
            
        except Exception as e:
            logger.error(f"Error manejando retraso: {str(e)}") 