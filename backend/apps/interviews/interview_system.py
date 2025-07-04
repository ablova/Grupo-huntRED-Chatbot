"""
Sistema Completo de Entrevistas para huntRED® v2
==============================================

Funcionalidades:
- Creación de entrevistas con slots personalizados
- Sincronización bidireccional con Google Calendar
- Soporte para múltiples ciclos de entrevistas
- Gestión de disponibilidad automática
- Recordatorios inteligentes
- Análisis de rendimiento de entrevistadores
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from zoneinfo import ZoneInfo

# Google Calendar API
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# huntRED imports
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

class InterviewType(Enum):
    SCREENING = "screening"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    PANEL = "panel"
    FINAL = "final"
    CULTURAL_FIT = "cultural_fit"
    MANAGERIAL = "managerial"
    PRESENTATION = "presentation"

class InterviewStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"

class InterviewMode(Enum):
    VIRTUAL = "virtual"
    IN_PERSON = "in_person"
    PHONE = "phone"
    HYBRID = "hybrid"

class CycleStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"

@dataclass
class TimeSlot:
    """Representa un slot de tiempo disponible para entrevistas."""
    start_time: datetime
    end_time: datetime
    interviewer_id: str
    is_available: bool = True
    booking_id: Optional[str] = None
    timezone: str = "UTC"
    
    def __post_init__(self):
        if isinstance(self.start_time, str):
            self.start_time = datetime.fromisoformat(self.start_time)
        if isinstance(self.end_time, str):
            self.end_time = datetime.fromisoformat(self.end_time)

@dataclass
class InterviewParticipant:
    """Participante en una entrevista."""
    id: str
    name: str
    email: str
    role: str  # interviewer, candidate, observer, panel_member
    required: bool = True
    phone: Optional[str] = None
    calendar_id: Optional[str] = None
    timezone: str = "UTC"

@dataclass
class Interview:
    """Representación completa de una entrevista."""
    id: str
    job_id: str
    candidate_id: str
    cycle_number: int
    interview_type: InterviewType
    status: InterviewStatus
    mode: InterviewMode
    
    # Información de tiempo
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    timezone: str = "UTC"
    
    # Participantes y ubicación
    participants: List[InterviewParticipant] = field(default_factory=list)
    location: Optional[str] = None
    virtual_meeting_url: Optional[str] = None
    meeting_password: Optional[str] = None
    
    # Configuración
    preparation_time: int = 15  # minutos antes
    buffer_time: int = 15  # minutos después
    auto_reminder: bool = True
    allow_rescheduling: bool = True
    
    # Google Calendar
    google_event_id: Optional[str] = None
    calendar_sync_enabled: bool = True
    
    # Metadatos
    instructions: str = ""
    agenda: Dict[str, Any] = field(default_factory=dict)
    feedback_form_id: Optional[str] = None
    recording_enabled: bool = False
    
    # Resultados
    feedback: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None
    decision: Optional[str] = None  # pass, fail, on_hold
    next_steps: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class InterviewCycle:
    """Ciclo completo de entrevistas para un candidato."""
    id: str
    job_id: str
    candidate_id: str
    cycle_number: int
    status: CycleStatus
    
    # Configuración del ciclo
    total_stages: int
    current_stage: int = 1
    required_approvals: int = 1
    
    # Entrevistas del ciclo
    interviews: List[Interview] = field(default_factory=list)
    
    # Configuración de timing
    max_duration_days: int = 14
    buffer_between_interviews: int = 24  # horas
    
    # Resultados del ciclo
    overall_score: Optional[float] = None
    recommendation: Optional[str] = None  # hire, reject, next_cycle
    feedback_summary: Dict[str, Any] = field(default_factory=dict)
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

class GoogleCalendarService:
    """Servicio para integración con Google Calendar."""
    
    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path or settings.GOOGLE_CALENDAR_CREDENTIALS
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Inicializa el servicio de Google Calendar."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            self.service = build('calendar', 'v3', credentials=credentials)
            logger.info("Google Calendar service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar service: {str(e)}")
            self.service = None
    
    async def create_event(self, interview: Interview) -> Optional[str]:
        """Crea un evento en Google Calendar."""
        if not self.service:
            logger.warning("Google Calendar service not available")
            return None
        
        try:
            # Construir lista de asistentes
            attendees = []
            for participant in interview.participants:
                attendees.append({
                    'email': participant.email,
                    'displayName': participant.name,
                    'responseStatus': 'needsAction' if participant.required else 'tentative'
                })
            
            # Configurar evento
            event = {
                'summary': f'Entrevista {interview.interview_type.value.title()} - {interview.candidate_id}',
                'description': self._build_event_description(interview),
                'start': {
                    'dateTime': interview.scheduled_start.isoformat(),
                    'timeZone': interview.timezone,
                },
                'end': {
                    'dateTime': interview.scheduled_end.isoformat(),
                    'timeZone': interview.timezone,
                },
                'attendees': attendees,
                'location': interview.location or interview.virtual_meeting_url,
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 día antes
                        {'method': 'popup', 'minutes': interview.preparation_time},
                    ],
                },
                'conferenceData': self._build_conference_data(interview) if interview.mode == InterviewMode.VIRTUAL else None,
                'extendedProperties': {
                    'private': {
                        'huntred_interview_id': interview.id,
                        'huntred_cycle': str(interview.cycle_number),
                        'huntred_type': interview.interview_type.value
                    }
                }
            }
            
            # Crear evento en el calendario principal
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1 if interview.mode == InterviewMode.VIRTUAL else 0
            ).execute()
            
            return created_event.get('id')
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            return None
    
    def _build_event_description(self, interview: Interview) -> str:
        """Construye la descripción del evento."""
        description = f"""
🎯 Entrevista {interview.interview_type.value.title()}
📊 Ciclo {interview.cycle_number} 
🏢 Posición: {interview.job_id}
👤 Candidato: {interview.candidate_id}

📋 Modalidad: {interview.mode.value.title()}
⏱️ Duración estimada: {(interview.scheduled_end - interview.scheduled_start).total_seconds() / 60:.0f} minutos

{interview.instructions}

🔗 Sistema huntRED®: https://app.huntred.com/interviews/{interview.id}
        """.strip()
        
        if interview.virtual_meeting_url:
            description += f"\n\n🎥 Enlace de reunión: {interview.virtual_meeting_url}"
        
        if interview.meeting_password:
            description += f"\n🔐 Contraseña: {interview.meeting_password}"
        
        return description
    
    def _build_conference_data(self, interview: Interview) -> Dict:
        """Construye los datos de conferencia para reuniones virtuales."""
        if interview.virtual_meeting_url:
            return {
                'createRequest': {
                    'requestId': interview.id,
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
        return {}
    
    async def update_event(self, event_id: str, interview: Interview) -> bool:
        """Actualiza un evento existente."""
        if not self.service or not event_id:
            return False
        
        try:
            # Obtener evento actual
            existing_event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Actualizar campos necesarios
            existing_event.update({
                'summary': f'Entrevista {interview.interview_type.value.title()} - {interview.candidate_id}',
                'description': self._build_event_description(interview),
                'start': {
                    'dateTime': interview.scheduled_start.isoformat(),
                    'timeZone': interview.timezone,
                },
                'end': {
                    'dateTime': interview.scheduled_end.isoformat(),
                    'timeZone': interview.timezone,
                },
                'location': interview.location or interview.virtual_meeting_url,
            })
            
            self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=existing_event
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating calendar event: {str(e)}")
            return False
    
    async def delete_event(self, event_id: str) -> bool:
        """Elimina un evento del calendario."""
        if not self.service or not event_id:
            return False
        
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting calendar event: {str(e)}")
            return False
    
    async def get_availability(self, interviewer_email: str, 
                             start_time: datetime, end_time: datetime) -> List[TimeSlot]:
        """Obtiene la disponibilidad de un entrevistador."""
        if not self.service:
            return []
        
        try:
            # Buscar eventos en el rango de tiempo
            events_result = self.service.events().list(
                calendarId=interviewer_email,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Generar slots disponibles (simplificado - en producción sería más complejo)
            available_slots = []
            current = start_time
            
            while current < end_time:
                slot_end = current + timedelta(hours=1)
                
                # Verificar si hay conflictos
                has_conflict = any(
                    datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date'))) < slot_end and
                    datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date'))) > current
                    for event in events
                )
                
                if not has_conflict:
                    available_slots.append(TimeSlot(
                        start_time=current,
                        end_time=slot_end,
                        interviewer_id=interviewer_email,
                        is_available=True
                    ))
                
                current += timedelta(minutes=30)  # Slots de 30 minutos
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting availability: {str(e)}")
            return []

class InterviewScheduler:
    """Coordinador principal del sistema de entrevistas."""
    
    def __init__(self):
        self.calendar_service = GoogleCalendarService()
        self.active_interviews: Dict[str, Interview] = {}
        self.active_cycles: Dict[str, InterviewCycle] = {}
        
        # Configuración
        self.default_interview_durations = {
            InterviewType.SCREENING: 30,
            InterviewType.TECHNICAL: 90,
            InterviewType.BEHAVIORAL: 60,
            InterviewType.PANEL: 120,
            InterviewType.FINAL: 45,
            InterviewType.CULTURAL_FIT: 45,
            InterviewType.MANAGERIAL: 60,
            InterviewType.PRESENTATION: 90
        }
        
        self.cycle_templates = {
            'junior': [InterviewType.SCREENING, InterviewType.TECHNICAL, InterviewType.BEHAVIORAL],
            'senior': [InterviewType.SCREENING, InterviewType.TECHNICAL, InterviewType.BEHAVIORAL, InterviewType.FINAL],
            'leadership': [InterviewType.SCREENING, InterviewType.BEHAVIORAL, InterviewType.MANAGERIAL, InterviewType.PANEL, InterviewType.FINAL],
            'executive': [InterviewType.SCREENING, InterviewType.BEHAVIORAL, InterviewType.PRESENTATION, InterviewType.PANEL, InterviewType.FINAL]
        }
    
    async def create_interview_cycle(self, job_id: str, candidate_id: str, 
                                   cycle_template: str = 'senior',
                                   custom_stages: List[InterviewType] = None) -> InterviewCycle:
        """Crea un nuevo ciclo de entrevistas."""
        cycle_id = str(uuid.uuid4())
        
        # Determinar etapas del ciclo
        if custom_stages:
            stages = custom_stages
        else:
            stages = self.cycle_templates.get(cycle_template, self.cycle_templates['senior'])
        
        cycle = InterviewCycle(
            id=cycle_id,
            job_id=job_id,
            candidate_id=candidate_id,
            cycle_number=1,  # Se incrementará automáticamente
            status=CycleStatus.PENDING,
            total_stages=len(stages),
            current_stage=1
        )
        
        self.active_cycles[cycle_id] = cycle
        
        logger.info(f"Created interview cycle {cycle_id} for candidate {candidate_id} with {len(stages)} stages")
        return cycle
    
    async def schedule_interview(self, cycle_id: str, interview_type: InterviewType,
                               participants: List[InterviewParticipant],
                               preferred_slots: List[TimeSlot],
                               **kwargs) -> Optional[Interview]:
        """Programa una entrevista específica dentro de un ciclo."""
        
        if cycle_id not in self.active_cycles:
            logger.error(f"Cycle {cycle_id} not found")
            return None
        
        cycle = self.active_cycles[cycle_id]
        interview_id = str(uuid.uuid4())
        
        # Encontrar el mejor slot disponible
        best_slot = await self._find_best_slot(participants, preferred_slots)
        if not best_slot:
            logger.error("No available slots found for interview")
            return None
        
        # Crear entrevista
        duration = kwargs.get('duration', self.default_interview_durations[interview_type])
        
        interview = Interview(
            id=interview_id,
            job_id=cycle.job_id,
            candidate_id=cycle.candidate_id,
            cycle_number=cycle.cycle_number,
            interview_type=interview_type,
            status=InterviewStatus.SCHEDULED,
            mode=kwargs.get('mode', InterviewMode.VIRTUAL),
            scheduled_start=best_slot.start_time,
            scheduled_end=best_slot.start_time + timedelta(minutes=duration),
            timezone=kwargs.get('timezone', 'UTC'),
            participants=participants,
            location=kwargs.get('location'),
            virtual_meeting_url=kwargs.get('virtual_meeting_url'),
            instructions=kwargs.get('instructions', ''),
            agenda=kwargs.get('agenda', {}),
            calendar_sync_enabled=kwargs.get('calendar_sync', True)
        )
        
        # Sincronizar con Google Calendar
        if interview.calendar_sync_enabled:
            google_event_id = await self.calendar_service.create_event(interview)
            interview.google_event_id = google_event_id
        
        # Agregar a ciclo y cache
        cycle.interviews.append(interview)
        self.active_interviews[interview_id] = interview
        
        # Enviar notificaciones
        await self._send_interview_notifications(interview)
        
        logger.info(f"Scheduled interview {interview_id} for cycle {cycle_id}")
        return interview
    
    async def _find_best_slot(self, participants: List[InterviewParticipant], 
                            preferred_slots: List[TimeSlot]) -> Optional[TimeSlot]:
        """Encuentra el mejor slot disponible para todos los participantes."""
        
        for slot in preferred_slots:
            if await self._check_slot_availability(participants, slot):
                return slot
        
        return None
    
    async def _check_slot_availability(self, participants: List[InterviewParticipant], 
                                     slot: TimeSlot) -> bool:
        """Verifica disponibilidad de todos los participantes en un slot."""
        
        for participant in participants:
            if participant.role == 'interviewer' and participant.required:
                availability = await self.calendar_service.get_availability(
                    participant.email,
                    slot.start_time,
                    slot.end_time
                )
                
                # Verificar si hay conflictos
                has_conflict = any(
                    existing_slot.start_time < slot.end_time and 
                    existing_slot.end_time > slot.start_time and
                    not existing_slot.is_available
                    for existing_slot in availability
                )
                
                if has_conflict:
                    return False
        
        return True
    
    async def reschedule_interview(self, interview_id: str, 
                                 new_slot: TimeSlot) -> bool:
        """Reprograma una entrevista existente."""
        
        if interview_id not in self.active_interviews:
            logger.error(f"Interview {interview_id} not found")
            return False
        
        interview = self.active_interviews[interview_id]
        
        if not interview.allow_rescheduling:
            logger.error(f"Interview {interview_id} does not allow rescheduling")
            return False
        
        # Verificar disponibilidad del nuevo slot
        if not await self._check_slot_availability(interview.participants, new_slot):
            logger.error("New slot not available for all participants")
            return False
        
        # Actualizar entrevista
        old_start = interview.scheduled_start
        interview.scheduled_start = new_slot.start_time
        interview.scheduled_end = new_slot.end_time
        interview.status = InterviewStatus.RESCHEDULED
        interview.updated_at = datetime.now()
        
        # Actualizar en Google Calendar
        if interview.google_event_id:
            await self.calendar_service.update_event(interview.google_event_id, interview)
        
        # Enviar notificaciones de cambio
        await self._send_reschedule_notifications(interview, old_start)
        
        logger.info(f"Rescheduled interview {interview_id} from {old_start} to {new_slot.start_time}")
        return True
    
    async def complete_interview(self, interview_id: str, 
                               feedback: Dict[str, Any],
                               score: float,
                               decision: str) -> bool:
        """Marca una entrevista como completada y procesa resultados."""
        
        if interview_id not in self.active_interviews:
            return False
        
        interview = self.active_interviews[interview_id]
        interview.status = InterviewStatus.COMPLETED
        interview.actual_end = datetime.now()
        interview.feedback = feedback
        interview.score = score
        interview.decision = decision
        interview.updated_at = datetime.now()
        
        # Evaluar si el ciclo puede continuar
        cycle_id = None
        for cid, cycle in self.active_cycles.items():
            if any(i.id == interview_id for i in cycle.interviews):
                cycle_id = cid
                break
        
        if cycle_id:
            await self._evaluate_cycle_progress(cycle_id)
        
        logger.info(f"Completed interview {interview_id} with decision: {decision}")
        return True
    
    async def _evaluate_cycle_progress(self, cycle_id: str):
        """Evalúa el progreso del ciclo y determina próximos pasos."""
        
        cycle = self.active_cycles[cycle_id]
        completed_interviews = [i for i in cycle.interviews if i.status == InterviewStatus.COMPLETED]
        
        # Calcular score promedio
        if completed_interviews:
            scores = [i.score for i in completed_interviews if i.score is not None]
            cycle.overall_score = sum(scores) / len(scores) if scores else None
        
        # Verificar si todas las entrevistas del ciclo están completas
        if len(completed_interviews) == cycle.total_stages:
            cycle.status = CycleStatus.COMPLETED
            cycle.completed_at = datetime.now()
            
            # Generar recomendación final
            passing_decisions = [i for i in completed_interviews if i.decision == 'pass']
            if len(passing_decisions) >= cycle.required_approvals:
                cycle.recommendation = 'hire'
            else:
                cycle.recommendation = 'reject'
            
            logger.info(f"Cycle {cycle_id} completed with recommendation: {cycle.recommendation}")
    
    async def _send_interview_notifications(self, interview: Interview):
        """Envía notificaciones de entrevista programada."""
        
        for participant in interview.participants:
            try:
                # Email personalizado según el rol
                if participant.role == 'candidate':
                    subject = f"Entrevista programada - {interview.interview_type.value.title()}"
                    message = self._build_candidate_notification(interview, participant)
                else:
                    subject = f"Nueva entrevista asignada - {interview.interview_type.value.title()}"
                    message = self._build_interviewer_notification(interview, participant)
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[participant.email],
                    fail_silently=False
                )
                
            except Exception as e:
                logger.error(f"Error sending notification to {participant.email}: {str(e)}")
    
    def _build_candidate_notification(self, interview: Interview, participant: InterviewParticipant) -> str:
        """Construye notificación para candidatos."""
        return f"""
Hola {participant.name},

¡Excelentes noticias! Hemos programado tu entrevista {interview.interview_type.value.title()}.

📅 Fecha: {interview.scheduled_start.strftime('%d/%m/%Y')}
🕒 Hora: {interview.scheduled_start.strftime('%H:%M')} - {interview.scheduled_end.strftime('%H:%M')}
⏱️ Duración: {(interview.scheduled_end - interview.scheduled_start).total_seconds() / 60:.0f} minutos
🌍 Zona horaria: {interview.timezone}

{'📍 Ubicación: ' + interview.location if interview.location else ''}
{'🎥 Enlace de reunión: ' + interview.virtual_meeting_url if interview.virtual_meeting_url else ''}

📋 Instrucciones especiales:
{interview.instructions}

¡Te deseamos mucho éxito!

Equipo huntRED®
        """.strip()
    
    def _build_interviewer_notification(self, interview: Interview, participant: InterviewParticipant) -> str:
        """Construye notificación para entrevistadores."""
        return f"""
Hola {participant.name},

Se te ha asignado una nueva entrevista:

🎯 Tipo: {interview.interview_type.value.title()}
👤 Candidato: {interview.candidate_id}
📊 Ciclo: {interview.cycle_number}

📅 Fecha: {interview.scheduled_start.strftime('%d/%m/%Y')}
🕒 Hora: {interview.scheduled_start.strftime('%H:%M')} - {interview.scheduled_end.strftime('%H:%M')}

🔗 Acceso al sistema: https://app.huntred.com/interviews/{interview.id}

Equipo huntRED®
        """.strip()
    
    async def _send_reschedule_notifications(self, interview: Interview, old_start: datetime):
        """Envía notificaciones de reprogramación."""
        
        for participant in interview.participants:
            try:
                subject = f"Entrevista reprogramada - {interview.interview_type.value.title()}"
                message = f"""
Hola {participant.name},

Tu entrevista ha sido reprogramada:

⏰ Hora anterior: {old_start.strftime('%d/%m/%Y %H:%M')}
🔄 Nueva hora: {interview.scheduled_start.strftime('%d/%m/%Y %H:%M')}

Por favor actualiza tu calendario.

Equipo huntRED®
                """.strip()
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[participant.email],
                    fail_silently=False
                )
                
            except Exception as e:
                logger.error(f"Error sending reschedule notification: {str(e)}")
    
    async def get_interviewer_availability(self, interviewer_emails: List[str],
                                         start_date: datetime, end_date: datetime,
                                         slot_duration: int = 60) -> Dict[str, List[TimeSlot]]:
        """Obtiene disponibilidad de múltiples entrevistadores."""
        
        availability_map = {}
        
        for email in interviewer_emails:
            slots = await self.calendar_service.get_availability(email, start_date, end_date)
            # Filtrar slots por duración mínima
            filtered_slots = [
                slot for slot in slots 
                if (slot.end_time - slot.start_time).total_seconds() >= slot_duration * 60
            ]
            availability_map[email] = filtered_slots
        
        return availability_map
    
    async def suggest_optimal_slots(self, participants: List[InterviewParticipant],
                                  preferred_date_range: Tuple[datetime, datetime],
                                  duration_minutes: int = 60) -> List[TimeSlot]:
        """Sugiere los mejores slots basado en disponibilidad de todos."""
        
        start_date, end_date = preferred_date_range
        interviewer_emails = [p.email for p in participants if p.role == 'interviewer']
        
        # Obtener disponibilidad de todos
        availability_map = await self.get_interviewer_availability(
            interviewer_emails, start_date, end_date, duration_minutes
        )
        
        # Encontrar slots donde todos están disponibles
        common_slots = []
        
        if not availability_map:
            return common_slots
        
        # Tomar el primer entrevistador como base
        base_slots = list(availability_map.values())[0]
        
        for base_slot in base_slots:
            # Verificar si todos los otros entrevistadores están disponibles
            available_for_all = True
            
            for email, slots in availability_map.items():
                if email == interviewer_emails[0]:
                    continue
                
                # Buscar overlap
                has_overlap = any(
                    slot.start_time <= base_slot.start_time < slot.end_time and
                    slot.start_time < base_slot.end_time <= slot.end_time
                    for slot in slots
                )
                
                if not has_overlap:
                    available_for_all = False
                    break
            
            if available_for_all:
                common_slots.append(base_slot)
        
        # Ordenar por preferencia (ej: horarios de oficina primero)
        common_slots.sort(key=lambda s: self._calculate_slot_preference_score(s))
        
        return common_slots[:10]  # Top 10 suggestions
    
    def _calculate_slot_preference_score(self, slot: TimeSlot) -> float:
        """Calcula score de preferencia para un slot (mayor = mejor)."""
        hour = slot.start_time.hour
        day_of_week = slot.start_time.weekday()
        
        score = 0.0
        
        # Preferir horarios de oficina (9 AM - 5 PM)
        if 9 <= hour <= 17:
            score += 1.0
        else:
            score += 0.3
        
        # Preferir días laborables
        if day_of_week < 5:  # Lunes-Viernes
            score += 1.0
        else:
            score += 0.2
        
        # Preferir medio día
        if 10 <= hour <= 14:
            score += 0.5
        
        return score
    
    def get_cycle_statistics(self, cycle_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas detalladas de un ciclo."""
        
        if cycle_id not in self.active_cycles:
            return {}
        
        cycle = self.active_cycles[cycle_id]
        
        stats = {
            'cycle_id': cycle_id,
            'status': cycle.status.value,
            'progress': f"{len([i for i in cycle.interviews if i.status == InterviewStatus.COMPLETED])}/{cycle.total_stages}",
            'overall_score': cycle.overall_score,
            'recommendation': cycle.recommendation,
            'duration_days': (datetime.now() - cycle.created_at).days,
            'interviews': []
        }
        
        for interview in cycle.interviews:
            interview_stats = {
                'id': interview.id,
                'type': interview.interview_type.value,
                'status': interview.status.value,
                'score': interview.score,
                'decision': interview.decision,
                'duration_actual': None,
                'interviewer_count': len([p for p in interview.participants if p.role == 'interviewer'])
            }
            
            if interview.actual_start and interview.actual_end:
                interview_stats['duration_actual'] = (interview.actual_end - interview.actual_start).total_seconds() / 60
            
            stats['interviews'].append(interview_stats)
        
        return stats

# Funciones de utilidad
async def create_quick_interview(job_id: str, candidate_id: str, 
                               interviewer_email: str, interview_type: str,
                               date_time: datetime, duration: int = 60) -> Optional[str]:
    """Función de conveniencia para crear entrevistas rápidas."""
    
    scheduler = InterviewScheduler()
    
    # Crear ciclo simple
    cycle = await scheduler.create_interview_cycle(job_id, candidate_id, 'simple')
    
    # Crear participantes
    participants = [
        InterviewParticipant(
            id=str(uuid.uuid4()),
            name="Candidato",
            email=f"candidate_{candidate_id}@example.com",
            role="candidate"
        ),
        InterviewParticipant(
            id=str(uuid.uuid4()),
            name="Entrevistador",
            email=interviewer_email,
            role="interviewer"
        )
    ]
    
    # Crear slot
    slots = [TimeSlot(
        start_time=date_time,
        end_time=date_time + timedelta(minutes=duration),
        interviewer_id=interviewer_email
    )]
    
    # Programar entrevista
    interview = await scheduler.schedule_interview(
        cycle.id,
        InterviewType(interview_type),
        participants,
        slots,
        duration=duration
    )
    
    return interview.id if interview else None

# Exportaciones
__all__ = [
    'InterviewType', 'InterviewStatus', 'InterviewMode', 'CycleStatus',
    'TimeSlot', 'InterviewParticipant', 'Interview', 'InterviewCycle',
    'GoogleCalendarService', 'InterviewScheduler', 'create_quick_interview'
]