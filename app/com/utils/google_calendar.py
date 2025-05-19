# /home/pablo/app/com/utils/google_calendar.py

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import asyncio
from django.conf import settings

logger = logging.getLogger(__name__)


async def get_available_slots(job_title: str, start_time: str, end_time: str, calendar_id: str) -> list:
    """
    Obtiene los eventos de tipo "Available Slot" en Google Calendar entre start_time y end_time 
    que estén asociados a cierta vacante (por ej. filtrando en el summary).
    
    :param job_title: Título del puesto para filtrar los eventos.
    :param start_time: Fecha/hora de inicio en formato RFC3339, ej: "2024-12-10T00:00:00Z"
    :param end_time: Fecha/hora fin.
    :param calendar_id: ID del calendario en el que se crearon los eventos.
    :return: Lista de dicts con {label, datetime}
    """
    creds = Credentials.from_authorized_user_file('path/to/credentials.json', ['https://www.googleapis.com/auth/calendar'])
    service = build('calendar', 'v3', credentials=creds)

    events_result = service.events().list(
        calendarId=calendar_id, 
        timeMin=start_time, 
        timeMax=end_time,
        singleEvents=True, 
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    slots = []
    for event in events:
        summary = event.get('summary', '')
        # Checamos si el evento contiene "Available Slot" y el título del job
        if 'Available Slot' in summary and job_title.lower() in summary.lower():
            start = event['start'].get('dateTime', event['start'].get('date'))
            # Crear un label descriptivo
            label = f"Disponibilidad: {start}"
            slots.append({'label': label, 'datetime': start})

    return slots

async def create_interview_slots_in_calendar(job_data: dict, calendar_id: str):
    """
    Crea eventos en Google Calendar para representar slots disponibles de entrevista para una vacante.
    Estos eventos llevarán en su 'summary' algo como "Available Slot para {job_title}".
    """
    creds = Credentials.from_authorized_user_file('path/to/credentials.json', ['https://www.googleapis.com/auth/calendar'])
    service = build('calendar', 'v3', credentials=creds)

    # Ejemplo: Crear 2 slots el mismo día
    slot_times = [
        ("2024-12-10T10:00:00-06:00", "2024-12-10T10:30:00-06:00"),
        ("2024-12-10T11:00:00-06:00", "2024-12-10T11:30:00-06:00"),
    ]

    for start, end in slot_times:
        event_body = {
            'summary': f"Available Slot para {job_data['job_title']}",
            'start': {'dateTime': start, 'timeZone': 'America/Mexico_City'},
            'end': {'dateTime': end, 'timeZone': 'America/Mexico_City'}
        }
        service.events().insert(calendarId=calendar_id, body=event_body).execute()
    logger.info(f"Slots de entrevista creados en Google Calendar para {job_data['job_title']}")

async def create_calendar_event(event_data: Dict, consultant_id: Optional[int] = None, calendar_id: str = 'primary'):
    """
    Crea un evento en Google Calendar con mayor flexibilidad para diferentes tipos de eventos.
    
    :param event_data: Diccionario con datos del evento (title, start_time, end_time, description, attendees, etc)
    :param consultant_id: ID del consultor para usar sus credenciales específicas
    :param calendar_id: ID del calendario donde crear el evento (default 'primary')
    :return: Dict con información del evento creado incluyendo htmlLink
    """
    # Obtener credenciales
    creds = get_google_credentials(consultant_id)
    if not creds:
        logger.error("No se pudieron obtener credenciales para crear evento")
        return {'success': False, 'error': 'No credentials available'}
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        # Construir cuerpo del evento
        event = {
            'summary': event_data.get('title', 'Evento huntRED'),
            'location': event_data.get('location', ''),
            'description': event_data.get('description', ''),
            'start': {
                'dateTime': event_data['start_time'],
                'timeZone': event_data.get('timezone', 'America/Mexico_City'),
            },
            'end': {
                'dateTime': event_data['end_time'],
                'timeZone': event_data.get('timezone', 'America/Mexico_City'),
            },
            'colorId': event_data.get('color_id', '1'),  # Color default
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': event_data.get('reminder_email_minutes', 60)},
                    {'method': 'popup', 'minutes': event_data.get('reminder_popup_minutes', 10)},
                ],
            },
        }
        
        # Añadir asistentes si se proporcionan
        if 'attendees' in event_data and event_data['attendees']:
            event['attendees'] = [{'email': email} for email in event_data['attendees']]
        
        # Añadir videoconferencia si se solicita
        if event_data.get('add_video_conference', False):
            event['conferenceData'] = {
                'createRequest': {
                    'requestId': f"huntred-{event_data.get('id', datetime.now().timestamp())}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
            conference_request = True
        else:
            conference_request = False
        
        # Crear el evento
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event,
            conferenceDataVersion=1 if conference_request else 0,
            sendUpdates=event_data.get('send_updates', 'all')
        ).execute()
        
        # Extraer datos relevantes del evento creado
        result = {
            'success': True,
            'event_id': created_event['id'],
            'html_link': created_event.get('htmlLink', ''),
            'created': created_event.get('created', ''),
            'status': created_event.get('status', '')
        }
        
        # Extraer link de videoconferencia si existe
        if conference_request and 'conferenceData' in created_event:
            for entry_point in created_event['conferenceData'].get('entryPoints', []):
                if entry_point.get('entryPointType') == 'video':
                    result['video_link'] = entry_point.get('uri', '')
                    break
        
        return result
        
    except Exception as e:
        logger.error(f"Error creando evento en Google Calendar: {e}")
        return {'success': False, 'error': str(e)}


async def create_onboarding_event(person_id: int, vacancy_id: int, event_type: str, 
                                  start_time: str, end_time: str,
                                  consultant_id: Optional[int] = None):
    """
    Crea un evento específico para el proceso de onboarding.
    
    :param person_id: ID de la persona (candidato contratado)
    :param vacancy_id: ID de la vacante
    :param event_type: Tipo de evento ('introduction', 'training', 'followup', etc)
    :param start_time: Hora de inicio (formato ISO)
    :param end_time: Hora de fin (formato ISO)
    :param consultant_id: ID del consultor responsable
    :return: Información del evento creado
    """
    from app.models import Person, Vacante, Consultant
    
    try:
        # Obtener datos necesarios
        person = Person.objects.get(id=person_id)
        vacancy = Vacante.objects.get(id=vacancy_id)
        
        # Determinar consultor si no se proporciona
        if not consultant_id and hasattr(vacancy, 'consultant') and vacancy.consultant:
            consultant_id = vacancy.consultant.id
            
        # Preparar datos según tipo de evento
        if event_type == 'introduction':
            title = f"Bienvenida - {person.first_name} {person.last_name} ({vacancy.title})"
            description = f"Sesión de bienvenida para {person.first_name} en su nuevo rol como {vacancy.title} en {vacancy.company.name}."
            color_id = '4'  # Verde
        elif event_type == 'training':
            title = f"Capacitación - {person.first_name} {person.last_name} ({vacancy.title})"
            description = f"Sesión de capacitación para el rol de {vacancy.title}."
            color_id = '6'  # Naranja
        elif event_type == 'followup':
            title = f"Seguimiento - {person.first_name} {person.last_name} ({vacancy.title})"
            description = f"Sesión de seguimiento para revisar progreso y resolver dudas."
            color_id = '1'  # Azul
        else:
            title = f"Onboarding - {person.first_name} {person.last_name} ({vacancy.title})"
            description = f"Sesión de onboarding para {vacancy.title}."
            color_id = '5'  # Amarillo
            
        # Preparar asistentes
        attendees = [person.email]
        
        # Añadir consultor si está disponible
        if consultant_id:
            try:
                consultant = Consultant.objects.get(id=consultant_id)
                if consultant.person and consultant.person.email:
                    attendees.append(consultant.person.email)
            except Exception as e:
                logger.warning(f"No se pudo añadir consultor {consultant_id} como asistente: {e}")
                
        # Añadir representante de empresa si está disponible
        if hasattr(vacancy, 'company_contact_email') and vacancy.company_contact_email:
            attendees.append(vacancy.company_contact_email)
        elif hasattr(vacancy.company, 'contact_email') and vacancy.company.contact_email:
            attendees.append(vacancy.company.contact_email)
            
        # Crear evento
        event_data = {
            'title': title,
            'description': description,
            'start_time': start_time,
            'end_time': end_time,
            'attendees': attendees,
            'color_id': color_id,
            'add_video_conference': True,
            'send_updates': 'all',
            'reminder_email_minutes': 24*60,  # Recordatorio por email 24h antes
            'reminder_popup_minutes': 30,     # Recordatorio popup 30min antes
            'id': f"onboarding-{person_id}-{vacancy_id}-{event_type}"
        }
        
        # Usar calendario del consultor si está disponible
        calendar_id = 'primary'
        if consultant_id:
            try:
                consultant = Consultant.objects.get(id=consultant_id)
                if consultant.google_calendar_id:
                    calendar_id = consultant.google_calendar_id
            except Exception:
                pass
                
        return await create_calendar_event(event_data, consultant_id, calendar_id)
        
    except (Person.DoesNotExist, Vacante.DoesNotExist) as e:
        logger.error(f"Error creando evento de onboarding: {e}")
        return {'success': False, 'error': str(e)}
    except Exception as e:
        logger.error(f"Error inesperado creando evento de onboarding: {e}")
        return {'success': False, 'error': str(e)}

def get_google_credentials(consultant_id: Optional[int] = None):
    """
    Carga las credenciales de Google desde variables de entorno, base de datos, o archivo.
    Si se proporciona consultant_id, intenta obtener credenciales específicas del consultor.
    """
    from app.models import Consultant
    
    # Scopes requeridos para calendario y eventos
    scopes = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']
    
    # Intentar obtener credenciales específicas del consultor
    if consultant_id:
        try:
            consultant = Consultant.objects.get(id=consultant_id)
            if consultant.google_credentials:
                creds_json = json.loads(consultant.google_credentials)
                return Credentials.from_authorized_user_info(info=creds_json, scopes=scopes)
        except Exception as e:
            logger.warning(f"Error obteniendo credenciales de consultor {consultant_id}: {e}")
    
    # Intentar obtener credenciales del sistema (settings)
    try:
        if hasattr(settings, 'GOOGLE_CREDENTIALS_JSON') and settings.GOOGLE_CREDENTIALS_JSON:
            creds_json = json.loads(settings.GOOGLE_CREDENTIALS_JSON)
            return Credentials.from_authorized_user_info(info=creds_json, scopes=scopes)
    except Exception as e:
        logger.warning(f"Error cargando credenciales desde settings: {e}")
    
    # Fallback a archivo
    try:
        creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 
                             os.path.join(settings.BASE_DIR, 'credentials/google_calendar.json'))
        if os.path.exists(creds_path):
            return Credentials.from_authorized_user_file(creds_path, scopes=scopes)
    except Exception as e:
        logger.warning(f"Error cargando credenciales desde archivo: {e}")
    
    logger.error("No se pudieron cargar credenciales de Google Calendar")
    return None