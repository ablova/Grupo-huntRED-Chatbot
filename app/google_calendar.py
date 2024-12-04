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


# /home/amigro/app/google_calendar.py

import os
import aiohttp
import asyncio
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import logging

logger = logging.getLogger(__name__)

async def create_calendar_event(slot, user, job):
    """
    Crea un evento en Google Calendar para una entrevista.

    :param slot: Diccionario con fecha y hora del slot.
    :param user: Objeto usuario con información del candidato.
    :param job: Objeto job con información de la vacante.
    :return: Enlace al evento creado.
    """
    try:
        # Configurar las credenciales
        creds = Credentials.from_authorized_user_info({
            'token': os.environ['GOOGLE_TOKEN'],
            'refresh_token': os.environ['GOOGLE_REFRESH_TOKEN'],
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': os.environ['GOOGLE_CLIENT_ID'],
            'client_secret': os.environ['GOOGLE_CLIENT_SECRET'],
            'scopes': ['https://www.googleapis.com/auth/calendar']
        })

        # Construir el servicio de Google Calendar
        service = build('calendar', 'v3', credentials=creds)

        # Crear el evento
        event = {
            'summary': f'Entrevista con {user.name} para {job.name}',
            'start': {
                'dateTime': f"{slot['date']}T{slot['time']}:00",
                'timeZone': 'America/Mexico_City',
            },
            'end': {
                'dateTime': f"{slot['date']}T{slot['time']}:30",
                'timeZone': 'America/Mexico_City',
            },
            'attendees': [
                {'email': user.email},
            ],
        }

        # Crear el evento de forma asíncrona
        event = service.events().insert(calendarId='primary', body=event).execute()
        return event.get('htmlLink')

    except Exception as e:
        logger.error(f"Error al crear evento en Google Calendar: {e}", exc_info=True)
        return None