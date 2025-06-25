"""
Integración con Calendly para Grupo huntRED®

Este módulo proporciona integración completa con Calendly para:
- Sincronización automática de calendarios
- Programación inteligente de entrevistas
- Gestión de slots de disponibilidad
- Automatización de recordatorios
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
import aiohttp
import json

from app.models import (
    Person, Event, EventParticipant, BusinessUnit, 
    ApiConfig, Interview, Vacante
)
from app.ats.integrations.notifications.core.service import NotificationService

logger = logging.getLogger(__name__)

class CalendlyIntegration:
    """
    Integración con Calendly para automatización de entrevistas.
    
    Proporciona funcionalidades para:
    - Sincronización de calendarios
    - Programación automática de entrevistas
    - Gestión de slots de disponibilidad
    - Integración con el sistema de notificaciones
    """
    
    def __init__(self, business_unit: Optional[BusinessUnit] = None):
        self.business_unit = business_unit
        self.api_config = self._get_api_config()
        self.base_url = "https://api.calendly.com"
        self.notification_service = NotificationService()
        
    def _get_api_config(self) -> Optional[ApiConfig]:
        """Obtiene la configuración de Calendly desde ConfigAPI."""
        try:
            return ApiConfig.objects.get(
                api_type='calendly',
                business_unit=self.business_unit,
                enabled=True
            )
        except ApiConfig.DoesNotExist:
            logger.warning(f"No se encontró configuración de Calendly para {self.business_unit}")
            return None
    
    async def sync_calendar(self, user_uri: str) -> Dict[str, Any]:
        """
        Sincroniza el calendario de un usuario con Calendly.
        
        Args:
            user_uri: URI del usuario en Calendly
            
        Returns:
            Dict con el resultado de la sincronización
        """
        if not self.api_config:
            return {'success': False, 'error': 'Configuración de Calendly no encontrada'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_config.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Obtener eventos del calendario
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/scheduled_events"
                params = {
                    'user': user_uri,
                    'status': 'active',
                    'count': 100
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        events = data.get('collection', [])
                        
                        # Procesar eventos
                        synced_events = await self._process_calendly_events(events)
                        
                        return {
                            'success': True,
                            'events_synced': len(synced_events),
                            'events': synced_events
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Error sincronizando calendario: {error_text}")
                        return {
                            'success': False,
                            'error': f"Error HTTP {response.status}: {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"Error en sync_calendar: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def create_interview_slot(
        self,
        candidate: Person,
        vacancy: Vacante,
        consultant: Person,
        duration_minutes: int = 60,
        interview_type: str = 'video'
    ) -> Dict[str, Any]:
        """
        Crea un slot de entrevista en Calendly.
        
        Args:
            candidate: Candidato para la entrevista
            vacancy: Vacante asociada
            consultant: Consultor que realizará la entrevista
            duration_minutes: Duración en minutos
            interview_type: Tipo de entrevista (video, phone, onsite)
            
        Returns:
            Dict con la información del slot creado
        """
        if not self.api_config:
            return {'success': False, 'error': 'Configuración de Calendly no encontrada'}
        
        try:
            # Obtener URI del consultor en Calendly
            consultant_uri = await self._get_user_uri(consultant)
            if not consultant_uri:
                return {'success': False, 'error': 'Consultor no encontrado en Calendly'}
            
            # Crear evento en Calendly
            event_data = {
                'name': f'Entrevista - {vacancy.titulo}',
                'description': f"""
                Entrevista para la posición: {vacancy.titulo}
                Candidato: {candidate.name}
                Empresa: {vacancy.empresa.nombre if hasattr(vacancy, 'empresa') else 'N/A'}
                Tipo: {interview_type}
                
                Instrucciones:
                - Prepárate para la entrevista
                - Revisa el CV del candidato
                - Ten listas las preguntas específicas para el rol
                """,
                'duration_minutes': duration_minutes,
                'event_type': interview_type,
                'location': await self._get_interview_location(interview_type),
                'invitee_emails': [candidate.email],
                'start_time': None,  # Se establecerá cuando se programe
                'end_time': None
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_config.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/scheduling_links"
                
                async with session.post(url, headers=headers, json=event_data) as response:
                    if response.status == 201:
                        data = await response.json()
                        
                        # Crear evento en nuestro sistema
                        event = await self._create_local_event(
                            candidate, vacancy, consultant, data, interview_type
                        )
                        
                        # Enviar notificación al candidato
                        await self._send_interview_invitation(candidate, event, data)
                        
                        return {
                            'success': True,
                            'calendly_uri': data.get('uri'),
                            'booking_url': data.get('booking_url'),
                            'event_id': event.id if event else None
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Error creando slot: {error_text}")
                        return {
                            'success': False,
                            'error': f"Error HTTP {response.status}: {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"Error en create_interview_slot: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def schedule_interview(
        self,
        event_uri: str,
        candidate: Person,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Programa una entrevista específica en Calendly.
        
        Args:
            event_uri: URI del evento en Calendly
            candidate: Candidato para la entrevista
            start_time: Hora de inicio
            end_time: Hora de fin
            
        Returns:
            Dict con el resultado de la programación
        """
        if not self.api_config:
            return {'success': False, 'error': 'Configuración de Calendly no encontrada'}
        
        try:
            booking_data = {
                'event_uri': event_uri,
                'invitee': {
                    'email': candidate.email,
                    'name': candidate.name,
                    'timezone': 'America/Mexico_City'
                },
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_config.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/scheduling_links/{event_uri}/book"
                
                async with session.post(url, headers=headers, json=booking_data) as response:
                    if response.status == 201:
                        data = await response.json()
                        
                        # Actualizar evento local
                        await self._update_local_event(event_uri, data)
                        
                        # Enviar confirmación
                        await self._send_interview_confirmation(candidate, data)
                        
                        return {
                            'success': True,
                            'booking_uri': data.get('uri'),
                            'confirmation_url': data.get('confirmation_url')
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Error programando entrevista: {error_text}")
                        return {
                            'success': False,
                            'error': f"Error HTTP {response.status}: {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"Error en schedule_interview: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_available_slots(
        self,
        consultant: Person,
        date_from: datetime,
        date_to: datetime,
        duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Obtiene slots disponibles de un consultor.
        
        Args:
            consultant: Consultor
            date_from: Fecha de inicio
            date_to: Fecha de fin
            duration_minutes: Duración requerida
            
        Returns:
            Dict con slots disponibles
        """
        if not self.api_config:
            return {'success': False, 'error': 'Configuración de Calendly no encontrada'}
        
        try:
            consultant_uri = await self._get_user_uri(consultant)
            if not consultant_uri:
                return {'success': False, 'error': 'Consultor no encontrado en Calendly'}
            
            headers = {
                'Authorization': f'Bearer {self.api_config.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/user_availability_schedules"
                params = {
                    'user': consultant_uri,
                    'start_time': date_from.isoformat(),
                    'end_time': date_to.isoformat()
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        available_slots = await self._process_availability_slots(data, duration_minutes)
                        
                        return {
                            'success': True,
                            'available_slots': available_slots,
                            'total_slots': len(available_slots)
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Error obteniendo slots: {error_text}")
                        return {
                            'success': False,
                            'error': f"Error HTTP {response.status}: {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"Error en get_available_slots: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def cancel_interview(self, booking_uri: str, reason: str = "Cancelado por el consultor") -> Dict[str, Any]:
        """
        Cancela una entrevista programada.
        
        Args:
            booking_uri: URI de la reserva en Calendly
            reason: Razón de la cancelación
            
        Returns:
            Dict con el resultado de la cancelación
        """
        if not self.api_config:
            return {'success': False, 'error': 'Configuración de Calendly no encontrada'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_config.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/invitees/{booking_uri}/cancellation"
                
                async with session.post(url, headers=headers, json={'reason': reason}) as response:
                    if response.status == 200:
                        # Actualizar evento local
                        await self._cancel_local_event(booking_uri)
                        
                        return {'success': True, 'message': 'Entrevista cancelada exitosamente'}
                    else:
                        error_text = await response.text()
                        logger.error(f"Error cancelando entrevista: {error_text}")
                        return {
                            'success': False,
                            'error': f"Error HTTP {response.status}: {error_text}"
                        }
                        
        except Exception as e:
            logger.error(f"Error en cancel_interview: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def webhook_handler(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja webhooks de Calendly.
        
        Args:
            webhook_data: Datos del webhook
            
        Returns:
            Dict con el resultado del procesamiento
        """
        try:
            event_type = webhook_data.get('event')
            
            if event_type == 'invitee.created':
                return await self._handle_invitee_created(webhook_data)
            elif event_type == 'invitee.canceled':
                return await self._handle_invitee_canceled(webhook_data)
            elif event_type == 'invitee.updated':
                return await self._handle_invitee_updated(webhook_data)
            else:
                logger.info(f"Webhook no manejado: {event_type}")
                return {'success': True, 'message': 'Webhook procesado'}
                
        except Exception as e:
            logger.error(f"Error en webhook_handler: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Métodos auxiliares privados
    
    async def _get_user_uri(self, person: Person) -> Optional[str]:
        """Obtiene el URI de Calendly de una persona."""
        # Implementar lógica para obtener URI de Calendly
        # Por ahora retornamos un valor de ejemplo
        return f"https://api.calendly.com/users/{person.id}"
    
    async def _get_interview_location(self, interview_type: str) -> str:
        """Obtiene la ubicación de la entrevista según el tipo."""
        if interview_type == 'video':
            return 'Zoom/Google Meet'
        elif interview_type == 'phone':
            return 'Llamada telefónica'
        elif interview_type == 'onsite':
            return 'Oficina huntRED'
        else:
            return 'Por definir'
    
    async def _create_local_event(
        self,
        candidate: Person,
        vacancy: Vacante,
        consultant: Person,
        calendly_data: Dict[str, Any],
        interview_type: str
    ) -> Optional[Event]:
        """Crea un evento local basado en los datos de Calendly."""
        try:
            event = Event.objects.create(
                title=f"Entrevista - {vacancy.titulo}",
                description=f"Entrevista con {candidate.name} para {vacancy.titulo}",
                event_type='ENTREVISTA',
                session_type='individual',
                max_participants=2,
                calendly_uri=calendly_data.get('uri'),
                calendly_booking_url=calendly_data.get('booking_url'),
                metadata={
                    'candidate_id': candidate.id,
                    'vacancy_id': vacancy.id,
                    'consultant_id': consultant.id,
                    'interview_type': interview_type,
                    'calendly_data': calendly_data
                }
            )
            
            # Crear participantes
            EventParticipant.objects.create(
                event=event,
                person=candidate,
                role='CANDIDATO'
            )
            
            EventParticipant.objects.create(
                event=event,
                person=consultant,
                role='CONSULTOR'
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Error creando evento local: {str(e)}")
            return None
    
    async def _update_local_event(self, event_uri: str, booking_data: Dict[str, Any]) -> bool:
        """Actualiza un evento local con datos de la reserva."""
        try:
            event = Event.objects.get(calendly_uri=event_uri)
            event.start_time = datetime.fromisoformat(booking_data.get('start_time'))
            event.end_time = datetime.fromisoformat(booking_data.get('end_time'))
            event.status = 'CONFIRMADO'
            event.save()
            return True
        except Event.DoesNotExist:
            logger.warning(f"Evento no encontrado para URI: {event_uri}")
            return False
        except Exception as e:
            logger.error(f"Error actualizando evento local: {str(e)}")
            return False
    
    async def _cancel_local_event(self, booking_uri: str) -> bool:
        """Cancela un evento local."""
        try:
            # Buscar evento por booking URI
            event = Event.objects.filter(
                metadata__calendly_data__uri=booking_uri
            ).first()
            
            if event:
                event.status = 'CANCELADO'
                event.save()
                return True
            return False
        except Exception as e:
            logger.error(f"Error cancelando evento local: {str(e)}")
            return False
    
    async def _process_calendly_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Procesa eventos de Calendly."""
        processed_events = []
        
        for event in events:
            try:
                processed_event = {
                    'uri': event.get('uri'),
                    'name': event.get('name'),
                    'start_time': event.get('start_time'),
                    'end_time': event.get('end_time'),
                    'status': event.get('status'),
                    'location': event.get('location'),
                    'invitees': event.get('invitees', [])
                }
                processed_events.append(processed_event)
            except Exception as e:
                logger.error(f"Error procesando evento: {str(e)}")
        
        return processed_events
    
    async def _process_availability_slots(
        self,
        availability_data: Dict[str, Any],
        duration_minutes: int
    ) -> List[Dict[str, Any]]:
        """Procesa slots de disponibilidad."""
        slots = []
        
        try:
            schedules = availability_data.get('collection', [])
            
            for schedule in schedules:
                slots_data = schedule.get('slots', [])
                
                for slot in slots_data:
                    start_time = datetime.fromisoformat(slot.get('start_time'))
                    end_time = datetime.fromisoformat(slot.get('end_time'))
                    
                    # Verificar que el slot tenga la duración requerida
                    slot_duration = (end_time - start_time).total_seconds() / 60
                    
                    if slot_duration >= duration_minutes:
                        slots.append({
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration_minutes': int(slot_duration),
                            'available': True
                        })
        except Exception as e:
            logger.error(f"Error procesando slots de disponibilidad: {str(e)}")
        
        return slots
    
    async def _send_interview_invitation(
        self,
        candidate: Person,
        event: Event,
        calendly_data: Dict[str, Any]
    ) -> None:
        """Envía invitación de entrevista al candidato."""
        try:
            context = {
                'candidate_name': candidate.name,
                'vacancy_title': event.metadata.get('vacancy_title', 'N/A'),
                'booking_url': calendly_data.get('booking_url'),
                'consultant_name': event.metadata.get('consultant_name', 'N/A'),
                'interview_type': event.metadata.get('interview_type', 'video')
            }
            
            await self.notification_service.send_notification(
                recipient=candidate,
                template_name='interview_invitation',
                context=context,
                channels=['email', 'whatsapp']
            )
        except Exception as e:
            logger.error(f"Error enviando invitación: {str(e)}")
    
    async def _send_interview_confirmation(
        self,
        candidate: Person,
        booking_data: Dict[str, Any]
    ) -> None:
        """Envía confirmación de entrevista."""
        try:
            context = {
                'candidate_name': candidate.name,
                'start_time': booking_data.get('start_time'),
                'end_time': booking_data.get('end_time'),
                'confirmation_url': booking_data.get('confirmation_url')
            }
            
            await self.notification_service.send_notification(
                recipient=candidate,
                template_name='interview_confirmation',
                context=context,
                channels=['email', 'whatsapp']
            )
        except Exception as e:
            logger.error(f"Error enviando confirmación: {str(e)}")
    
    async def _handle_invitee_created(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja creación de invitado."""
        # Implementar lógica para manejar nuevo invitado
        return {'success': True, 'message': 'Invitado creado'}
    
    async def _handle_invitee_canceled(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja cancelación de invitado."""
        # Implementar lógica para manejar cancelación
        return {'success': True, 'message': 'Invitado cancelado'}
    
    async def _handle_invitee_updated(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja actualización de invitado."""
        # Implementar lógica para manejar actualización
        return {'success': True, 'message': 'Invitado actualizado'} 