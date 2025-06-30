"""
Integración con Google Calendar para calendarización de eventos de marketing.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import requests
from django.conf import settings
from django.utils import timezone
from app.ats.publish.models import GoogleCalendarIntegration, MarketingEvent
from app.ats.publish.integrations.base_integration import BaseIntegration

logger = logging.getLogger(__name__)

class GoogleCalendarIntegration(BaseIntegration):
    """
    Integración con Google Calendar para programación automática de eventos.
    """
    
    def __init__(self, calendar_integration: GoogleCalendarIntegration):
        """
        Inicializa la integración con Google Calendar.
        
        Args:
            calendar_integration: Configuración de la integración con Google Calendar.
        """
        self.calendar_integration = calendar_integration
        self.api_config = self._get_api_config()
        
    def _get_api_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración de API de Google Calendar.
        
        Returns:
            Configuración de API de Google Calendar.
        """
        return {
            'access_token': self.calendar_integration.access_token,
            'refresh_token': self.calendar_integration.refresh_token,
            'calendar_id': self.calendar_integration.calendar_id,
            'timezone': self.calendar_integration.timezone
        }
    
    def _refresh_token_if_needed(self):
        """
        Refresca el token de acceso si es necesario.
        """
        if self.calendar_integration.is_expired():
            # Implementar lógica de refresh token
            pass
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Obtiene los headers para las llamadas a la API.
        
        Returns:
            Headers para las llamadas a la API.
        """
        self._refresh_token_if_needed()
        return {
            'Authorization': f'Bearer {self.api_config["access_token"]}',
            'Content-Type': 'application/json'
        }
    
    async def create_event(self, marketing_event: MarketingEvent) -> Dict[str, Any]:
        """
        Crea un evento en Google Calendar.
        
        Args:
            marketing_event: Evento de marketing a crear.
            
        Returns:
            Resultado de la creación del evento.
        """
        try:
            event_data = {
                'summary': marketing_event.title,
                'description': marketing_event.description,
                'start': {
                    'dateTime': marketing_event.start_datetime.isoformat(),
                    'timeZone': self.api_config['timezone']
                },
                'end': {
                    'dateTime': marketing_event.end_datetime.isoformat(),
                    'timeZone': self.api_config['timezone']
                },
                'location': marketing_event.location if not marketing_event.is_virtual else None,
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"meet-{marketing_event.id}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                } if marketing_event.is_virtual else None,
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 día antes
                        {'method': 'popup', 'minutes': 30}  # 30 minutos antes
                    ]
                }
            }
            
            response = requests.post(
                f'https://www.googleapis.com/calendar/v3/calendars/{self.api_config["calendar_id"]}/events',
                headers=self._get_headers(),
                json=event_data
            )
            
            if response.status_code == 200:
                event_response = response.json()
                marketing_event.google_event_id = event_response['id']
                if marketing_event.is_virtual and 'conferenceData' in event_response:
                    marketing_event.meeting_url = event_response['conferenceData']['entryPoints'][0]['uri']
                marketing_event.save()
                
                return {
                    'success': True,
                    'event_id': event_response['id'],
                    'meeting_url': marketing_event.meeting_url
                }
            else:
                logger.error(f"Error al crear evento en Google Calendar: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en GoogleCalendarIntegration.create_event: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_event(self, marketing_event: MarketingEvent) -> Dict[str, Any]:
        """
        Actualiza un evento existente en Google Calendar.
        
        Args:
            marketing_event: Evento de marketing a actualizar.
            
        Returns:
            Resultado de la actualización del evento.
        """
        try:
            if not marketing_event.google_event_id:
                return await self.create_event(marketing_event)
            
            event_data = {
                'summary': marketing_event.title,
                'description': marketing_event.description,
                'start': {
                    'dateTime': marketing_event.start_datetime.isoformat(),
                    'timeZone': self.api_config['timezone']
                },
                'end': {
                    'dateTime': marketing_event.end_datetime.isoformat(),
                    'timeZone': self.api_config['timezone']
                },
                'location': marketing_event.location if not marketing_event.is_virtual else None
            }
            
            response = requests.patch(
                f'https://www.googleapis.com/calendar/v3/calendars/{self.api_config["calendar_id"]}/events/{marketing_event.google_event_id}',
                headers=self._get_headers(),
                json=event_data
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Evento actualizado exitosamente'
                }
            else:
                logger.error(f"Error al actualizar evento en Google Calendar: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en GoogleCalendarIntegration.update_event: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def delete_event(self, marketing_event: MarketingEvent) -> Dict[str, Any]:
        """
        Elimina un evento de Google Calendar.
        
        Args:
            marketing_event: Evento de marketing a eliminar.
            
        Returns:
            Resultado de la eliminación del evento.
        """
        try:
            if not marketing_event.google_event_id:
                return {
                    'success': True,
                    'message': 'Evento no existe en Google Calendar'
                }
            
            response = requests.delete(
                f'https://www.googleapis.com/calendar/v3/calendars/{self.api_config["calendar_id"]}/events/{marketing_event.google_event_id}',
                headers=self._get_headers()
            )
            
            if response.status_code == 204:
                marketing_event.google_event_id = ''
                marketing_event.save()
                return {
                    'success': True,
                    'message': 'Evento eliminado exitosamente'
                }
            else:
                logger.error(f"Error al eliminar evento en Google Calendar: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en GoogleCalendarIntegration.delete_event: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_events(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Obtiene eventos del calendario.
        
        Args:
            start_date: Fecha de inicio para filtrar eventos.
            end_date: Fecha de fin para filtrar eventos.
            
        Returns:
            Lista de eventos del calendario.
        """
        try:
            if not start_date:
                start_date = timezone.now()
            if not end_date:
                end_date = start_date + timedelta(days=30)
            
            params = {
                'timeMin': start_date.isoformat(),
                'timeMax': end_date.isoformat(),
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            
            response = requests.get(
                f'https://www.googleapis.com/calendar/v3/calendars/{self.api_config["calendar_id"]}/events',
                headers=self._get_headers(),
                params=params
            )
            
            if response.status_code == 200:
                return response.json().get('items', [])
            else:
                logger.error(f"Error al obtener eventos de Google Calendar: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error en GoogleCalendarIntegration.get_events: {str(e)}")
            return []
    
    async def check_availability(self, start_datetime: datetime, end_datetime: datetime) -> bool:
        """
        Verifica la disponibilidad en el calendario.
        
        Args:
            start_datetime: Fecha y hora de inicio.
            end_datetime: Fecha y hora de fin.
            
        Returns:
            True si hay disponibilidad, False en caso contrario.
        """
        try:
            events = await self.get_events(start_datetime, end_datetime)
            
            for event in events:
                event_start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                event_end = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
                
                # Verificar si hay conflicto
                if (start_datetime < event_end and end_datetime > event_start):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error en GoogleCalendarIntegration.check_availability: {str(e)}")
            return False
    
    async def suggest_time_slot(self, duration_minutes: int, preferred_start: datetime = None) -> datetime:
        """
        Sugiere un horario disponible para un evento.
        
        Args:
            duration_minutes: Duración del evento en minutos.
            preferred_start: Horario preferido de inicio.
            
        Returns:
            Horario sugerido para el evento.
        """
        try:
            if not preferred_start:
                preferred_start = timezone.now() + timedelta(hours=1)
            
            # Buscar en las próximas 2 semanas
            end_search = preferred_start + timedelta(days=14)
            
            # Horarios de trabajo (9 AM - 6 PM)
            work_start_hour = 9
            work_end_hour = 18
            
            current_time = preferred_start
            
            while current_time < end_search:
                # Verificar si es horario de trabajo
                if work_start_hour <= current_time.hour < work_end_hour:
                    end_time = current_time + timedelta(minutes=duration_minutes)
                    
                    if await self.check_availability(current_time, end_time):
                        return current_time
                
                # Avanzar 30 minutos
                current_time += timedelta(minutes=30)
            
            return None
            
        except Exception as e:
            logger.error(f"Error en GoogleCalendarIntegration.suggest_time_slot: {str(e)}")
            return None 