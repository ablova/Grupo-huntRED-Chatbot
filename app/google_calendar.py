# /home/amigro/app/google_calendar.py

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import logging

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

def create_calendar_event(slot, user, job):
    # Configurar las credenciales
    creds = Credentials.from_authorized_user_file('path/to/credentials.json', ['https://www.googleapis.com/auth/calendar'])
    service = build('calendar', 'v3', credentials=creds)
    
    # Crear el evento
    event = {
        'summary': f'Entrevista con {user.name} para {job.name}',
        'start': {
            'dateTime': f"{slot['date']}T{slot['time']}:00",
            'timeZone': 'America/Mexico_City',
        },
        'end': {
            'dateTime': f"{slot['date']}T{slot['time']}:30",  # Duración de 30 minutos
            'timeZone': 'America/Mexico_City',
        },
        'attendees': [
            {'email': user.email},
        ],
    }
    
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event.get('htmlLink')

def get_google_credentials():
    """
    Carga las credenciales de Google desde variables de entorno o archivo.
    """
    creds = Credentials.from_authorized_user_file(
        os.getenv('GOOGLE_CREDENTIALS_PATH', 'path/to/credentials.json'),
        ['https://www.googleapis.com/auth/calendar']
    )
    return creds