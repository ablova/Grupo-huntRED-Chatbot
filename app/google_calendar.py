# /home/amigro/app/google_calendar.py

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

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
