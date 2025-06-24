"""
Servicio para gestionar entrevistas.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from django.utils import timezone

from app.models import Interview, Person, Vacante
from app.ats.integrations.notifications.process.interview_notifications import InterviewNotificationService
from app.ats.utils.location_tracker import LocationTracker
from app.tasks import (
    send_interview_notification_task,
    schedule_interview_tracking_task
)
from app.ats.utils.vacantes import requiere_slots_grupales
from app.ats.utils.Events import Event, EventType, EventStatus, EventParticipant
from app.ats.utils.google_calendar import create_calendar_event, get_available_slots

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
        
    async def generate_interview_slots(
        self,
        vacancy: Vacante,
        start_date: datetime,
        end_date: datetime,
        slot_duration: int = 45,
        max_slots_per_day: int = 8
    ) -> List[Event]:
        """
        Genera slots de entrevista automáticamente para una vacante.
        
        Args:
            vacancy: Vacante para la cual generar slots
            start_date: Fecha de inicio para generar slots
            end_date: Fecha final para generar slots
            slot_duration: Duración de cada slot en minutos
            max_slots_per_day: Máximo número de slots por día
            
        Returns:
            Lista de eventos creados
        """
        try:
            created_slots = []
            current_date = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
            
            while current_date <= end_date:
                # Generar slots para cada día hábil (lunes a viernes)
                if current_date.weekday() < 5:  # 0-4 = lunes a viernes
                    day_slots = await self._generate_day_slots(
                        vacancy, current_date, slot_duration, max_slots_per_day
                    )
                    created_slots.extend(day_slots)
                
                current_date += timedelta(days=1)
            
            logger.info(f"Generados {len(created_slots)} slots para vacante {vacancy.id}")
            return created_slots
            
        except Exception as e:
            logger.error(f"Error generando slots de entrevista: {str(e)}")
            raise
    
    async def _generate_day_slots(
        self,
        vacancy: Vacante,
        date: datetime,
        slot_duration: int,
        max_slots_per_day: int
    ) -> List[Event]:
        """
        Genera slots para un día específico.
        """
        slots = []
        current_time = date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = date.replace(hour=17, minute=0, second=0, microsecond=0)
        slots_created = 0
        
        while current_time < end_time and slots_created < max_slots_per_day:
            # Verificar si ya existe un slot en este horario
            existing_slot = await Event.objects.filter(
                event_type=EventType.ENTREVISTA,
                start_time=current_time,
                description__icontains=str(vacancy.id)
            ).afirst()
            
            if not existing_slot:
                # Determinar si usar slot grupal o individual
                use_group_slot = requiere_slots_grupales(vacancy)
                
                slot = await Event.objects.acreate(
                    title=f"Entrevista {'grupal' if use_group_slot else 'individual'} - {vacancy.titulo}",
                    description=f"Slot de entrevista para vacante {vacancy.id} - {vacancy.titulo}",
                    event_type=EventType.ENTREVISTA,
                    status=EventStatus.PENDIENTE,
                    start_time=current_time,
                    end_time=current_time + timedelta(minutes=slot_duration),
                    session_type="grupal" if use_group_slot else "individual",
                    cupo_maximo=vacancy.numero_plazas if use_group_slot else 1,
                    location=vacancy.ubicacion,
                    virtual_link=None,  # Se generará cuando se confirme
                    event_mode=getattr(vacancy, 'modalidad', 'virtual')
                )
                
                # Crear evento en Google Calendar si está configurado
                if self.business_unit.calendar_id:
                    await self._create_google_calendar_slot(slot, vacancy)
                
                slots.append(slot)
                slots_created += 1
            
            current_time += timedelta(minutes=slot_duration)
        
        return slots
    
    async def _create_google_calendar_slot(self, slot: Event, vacancy: Vacante):
        """
        Crea un slot en Google Calendar.
        """
        try:
            event_data = {
                'title': f"Available Slot - {vacancy.titulo}",
                'description': f"Slot disponible para entrevista de {vacancy.titulo}",
                'start_time': slot.start_time.isoformat(),
                'end_time': slot.end_time.isoformat(),
                'add_video_conference': slot.event_mode == 'virtual',
                'send_updates': 'none',
                'id': f"slot-{slot.id}"
            }
            
            result = await create_calendar_event(
                event_data, 
                calendar_id=self.business_unit.calendar_id
            )
            
            if result.get('success'):
                # Actualizar el slot con el link de Google Calendar
                slot.virtual_link = result.get('html_link')
                await slot.asave()
                logger.info(f"Slot creado en Google Calendar: {result.get('event_id')}")
            
        except Exception as e:
            logger.error(f"Error creando slot en Google Calendar: {str(e)}")
        
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
        Si la vacante requiere slots grupales, asigna al candidato a un slot grupal existente o crea uno nuevo.
        Si no, crea una entrevista individual como siempre.
        """
        try:
            # --- LÓGICA PARA SLOTS GRUPALES ---
            if requiere_slots_grupales(vacancy):
                # Buscar slot grupal existente para la vacante y fecha con cupo disponible
                slot = await Event.objects.filter(
                    event_type=EventType.ENTREVISTA,
                    session_type="grupal",
                    start_time__date=interview_date.date(),
                    status=EventStatus.PENDIENTE,
                    description__icontains=str(vacancy.id)
                ).afirst()
                
                if slot and slot.lugares_disponibles() > 0:
                    # Asignar candidato a slot existente
                    participant = await EventParticipant.objects.acreate(
                        event=slot,
                        person=person,
                        status=EventStatus.CONFIRMADO,
                        notes=f"Entrevista para {vacancy.titulo}"
                    )
                    
                    # Si es el primer participante, confirmar el slot
                    if slot.participants.count() == 1:
                        slot.status = EventStatus.CONFIRMADO
                        await slot.asave()
                    
                    # Crear registro de entrevista tradicional para compatibilidad
                    interview = await Interview.objects.acreate(
                        person=person,
                        vacancy=vacancy,
                        interview_date=slot.start_time,
                        interview_type=interview_type,
                        location=location,
                        notes=additional_notes + " (Slot grupal)",
                        status='scheduled',
                        event_mode=slot.event_mode
                    )
                    
                else:
                    # Crear nuevo slot grupal
                    slot = await Event.objects.acreate(
                        title=f"Entrevista grupal {vacancy.titulo}",
                        description=f"Slot grupal para vacante {vacancy.id}",
                        event_type=EventType.ENTREVISTA,
                        status=EventStatus.CONFIRMADO,
                        start_time=interview_date,
                        end_time=interview_date + timedelta(minutes=45),
                        session_type="grupal",
                        cupo_maximo=vacancy.numero_plazas,
                        location=location.get('address') if location else None,
                        virtual_link=location.get('virtual_link') if location else None,
                        event_mode=getattr(vacancy, 'modalidad', 'virtual')
                    )
                    
                    await EventParticipant.objects.acreate(
                        event=slot,
                        person=person,
                        status=EventStatus.CONFIRMADO,
                        notes=f"Entrevista para {vacancy.titulo}"
                    )
                    
                    # Crear registro de entrevista tradicional
                    interview = await Interview.objects.acreate(
                        person=person,
                        vacancy=vacancy,
                        interview_date=interview_date,
                        interview_type=interview_type,
                        location=location,
                        notes=additional_notes + " (Slot grupal)",
                        status='scheduled',
                        event_mode=slot.event_mode
                    )
                
                # Notificar y programar seguimiento
                await self.notification_service.notify_interview_scheduled(
                    person=person,
                    vacancy=vacancy,
                    interview_date=slot.start_time,
                    interview_type=interview_type,
                    location=location,
                    additional_notes=additional_notes + " (Slot grupal)"
                )
                
                await schedule_interview_tracking_task.delay(interview.id)
                return interview
                
            # --- FIN LÓGICA SLOTS GRUPALES ---

            # Lógica tradicional (individual)
            event_mode = getattr(vacancy, 'modalidad', None) or 'virtual'
            interview = await Interview.objects.acreate(
                person=person,
                vacancy=vacancy,
                interview_date=interview_date,
                interview_type=interview_type,
                location=location,
                notes=additional_notes,
                status='scheduled',
                event_mode=event_mode
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
    
    async def get_available_slots_for_vacancy(
        self,
        vacancy: Vacante,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene slots disponibles para una vacante específica.
        
        Args:
            vacancy: Vacante para buscar slots
            start_date: Fecha de inicio (por defecto hoy)
            end_date: Fecha final (por defecto en 7 días)
            
        Returns:
            Lista de slots disponibles con información detallada
        """
        try:
            if not start_date:
                start_date = timezone.now()
            if not end_date:
                end_date = start_date + timedelta(days=7)
            
            # Buscar slots en la base de datos
            slots = await Event.objects.filter(
                event_type=EventType.ENTREVISTA,
                start_time__gte=start_date,
                start_time__lte=end_date,
                description__icontains=str(vacancy.id),
                status__in=[EventStatus.PENDIENTE, EventStatus.CONFIRMADO]
            ).order_by('start_time').all()
            
            available_slots = []
            for slot in slots:
                if slot.lugares_disponibles() > 0:
                    # Formatear información del slot
                    slot_info = {
                        'id': str(slot.id),
                        'label': f"{slot.start_time.strftime('%A %d/%m %H:%M')} - {slot.get_session_type_display()}",
                        'datetime': slot.start_time.isoformat(),
                        'session_type': slot.session_type,
                        'available_spots': slot.lugares_disponibles(),
                        'total_spots': slot.cupo_maximo or 1,
                        'mode': slot.get_event_mode_display(),
                        'location': slot.location
                    }
                    available_slots.append(slot_info)
            
            # Si no hay slots en la BD, buscar en Google Calendar
            if not available_slots and self.business_unit.calendar_id:
                calendar_slots = await get_available_slots(
                    vacancy.titulo,
                    start_date.isoformat(),
                    end_date.isoformat(),
                    self.business_unit.calendar_id
                )
                
                for i, calendar_slot in enumerate(calendar_slots):
                    available_slots.append({
                        'id': f"calendar_{i}",
                        'label': calendar_slot['label'],
                        'datetime': calendar_slot['datetime'],
                        'session_type': 'individual',
                        'available_spots': 1,
                        'total_spots': 1,
                        'mode': 'Virtual',
                        'location': None,
                        'source': 'google_calendar'
                    })
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Error obteniendo slots disponibles: {str(e)}")
            return []
    
    async def book_slot_for_candidate(
        self,
        person: Person,
        vacancy: Vacante,
        slot_id: str,
        interview_type: str = 'video'
    ) -> Dict[str, Any]:
        """
        Reserva un slot específico para un candidato.
        
        Args:
            person: Candidato
            vacancy: Vacante
            slot_id: ID del slot a reservar
            interview_type: Tipo de entrevista
            
        Returns:
            Resultado de la reserva
        """
        try:
            # Buscar el slot
            if slot_id.startswith('calendar_'):
                # Slot de Google Calendar - crear nuevo evento
                return await self._book_google_calendar_slot(person, vacancy, slot_id, interview_type)
            else:
                # Slot de la base de datos
                slot = await Event.objects.filter(id=slot_id).afirst()
                if not slot:
                    return {'success': False, 'error': 'Slot no encontrado'}
                
                if slot.lugares_disponibles() <= 0:
                    return {'success': False, 'error': 'Slot sin cupo disponible'}
                
                # Verificar que el candidato no esté ya registrado
                existing_participant = await EventParticipant.objects.filter(
                    event=slot,
                    person=person
                ).afirst()
                
                if existing_participant:
                    return {'success': False, 'error': 'Ya estás registrado en este slot'}
                
                # Registrar participante
                await EventParticipant.objects.acreate(
                    event=slot,
                    person=person,
                    status=EventStatus.CONFIRMADO,
                    notes=f"Entrevista para {vacancy.titulo}"
                )
                
                # Crear entrevista
                interview = await Interview.objects.acreate(
                    person=person,
                    vacancy=vacancy,
                    interview_date=slot.start_time,
                    interview_type=interview_type,
                    status='scheduled',
                    event_mode=slot.event_mode,
                    location={'address': slot.location} if slot.location else None
                )
                
                # Notificar
                await self.notification_service.notify_interview_scheduled(
                    person=person,
                    vacancy=vacancy,
                    interview_date=slot.start_time,
                    interview_type=interview_type,
                    location={'address': slot.location} if slot.location else None,
                    additional_notes=f"Slot {slot.get_session_type_display()}"
                )
                
                return {
                    'success': True,
                    'interview_id': interview.id,
                    'slot_id': str(slot.id),
                    'datetime': slot.start_time.isoformat(),
                    'session_type': slot.session_type
                }
                
        except Exception as e:
            logger.error(f"Error reservando slot: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _book_google_calendar_slot(
        self,
        person: Person,
        vacancy: Vacante,
        slot_id: str,
        interview_type: str
    ) -> Dict[str, Any]:
        """
        Reserva un slot de Google Calendar creando un nuevo evento.
        """
        try:
            # Crear evento individual en Google Calendar
            event_data = {
                'title': f"Entrevista - {person.first_name} {person.last_name} - {vacancy.titulo}",
                'description': f"Entrevista para {vacancy.titulo}",
                'start_time': timezone.now() + timedelta(hours=1),  # Próximo slot disponible
                'end_time': timezone.now() + timedelta(hours=1, minutes=45),
                'attendees': [person.email],
                'add_video_conference': True,
                'send_updates': 'all'
            }
            
            result = await create_calendar_event(
                event_data,
                calendar_id=self.business_unit.calendar_id
            )
            
            if result.get('success'):
                # Crear entrevista
                interview = await Interview.objects.acreate(
                    person=person,
                    vacancy=vacancy,
                    interview_date=event_data['start_time'],
                    interview_type=interview_type,
                    status='scheduled',
                    event_mode='virtual',
                    location={'virtual_link': result.get('video_link')}
                )
                
                # Notificar
                await self.notification_service.notify_interview_scheduled(
                    person=person,
                    vacancy=vacancy,
                    interview_date=event_data['start_time'],
                    interview_type=interview_type,
                    location={'virtual_link': result.get('video_link')},
                    additional_notes="Entrevista individual"
                )
                
                return {
                    'success': True,
                    'interview_id': interview.id,
                    'datetime': event_data['start_time'].isoformat(),
                    'session_type': 'individual',
                    'google_event_id': result.get('event_id')
                }
            else:
                return {'success': False, 'error': 'Error creando evento en Google Calendar'}
                
        except Exception as e:
            logger.error(f"Error reservando slot de Google Calendar: {str(e)}")
            return {'success': False, 'error': str(e)}
            
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