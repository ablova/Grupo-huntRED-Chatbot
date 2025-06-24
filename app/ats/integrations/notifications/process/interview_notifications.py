"""
Módulo de notificaciones específicas para el proceso de entrevistas.
Maneja todas las notificaciones relacionadas con la programación y seguimiento de entrevistas.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import Person, Vacante, BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import (
    NotificationType,
    NotificationSeverity
)
from app.ats.integrations.notifications.recipients.client import ClientRecipient
from app.ats.integrations.notifications.recipients.candidate import CandidateRecipient

logger = logging.getLogger(__name__)

class InterviewNotificationService(BaseNotificationService):
    """
    Servicio de notificaciones para el proceso de entrevistas.
    Extiende el servicio base con funcionalidad específica para entrevistas.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el servicio de notificaciones de entrevistas.
        
        Args:
            business_unit: Unidad de negocio requerida para las notificaciones
        """
        if not business_unit:
            raise ValueError("Se requiere especificar una unidad de negocio")
            
        super().__init__(business_unit)
        
    async def notify_interview_scheduled(
        self,
        person: Person,
        vacancy: Vacante,
        interview_date: datetime,
        interview_type: str,
        location: Optional[Dict[str, Any]] = None,
        additional_notes: str = '',
        event_mode: str = 'virtual',
        meeting_link: str = None,
        interview_id: str = None
    ) -> bool:
        """
        Notifica sobre una entrevista programada.
        Personaliza la sección de transporte público según la business unit.
        El feedback para el cliente se solicita solo después de la entrevista.
        """
        try:
            bu_name = self.business_unit.name.lower()
            prioridad_publico = bu_name in ("huntu", "amigro")
            # Construir sección de transporte público solo si aplica
            if prioridad_publico:
                transporte_publico_section = (
                    "\U0001F687 *En transporte público:* {commute_time_public} - Ruta: {public_transport_route}\n"
                )
            else:
                transporte_publico_section = ''
            # Preparar contexto
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'interview_date': interview_date.strftime('%d/%m/%Y %H:%M'),
                'interview_type': interview_type,
                'location': location.get('name') if location else 'No especificada',
                'additional_notes': additional_notes,
                'business_unit': self.business_unit.name,
                'event_mode': event_mode,
                'meeting_link': meeting_link or '',
                'interview_id': interview_id or '',
                'commute_time_car': location.get('commute_time_car', '') if location else '',
                'traffic_level': location.get('traffic_level', '') if location else '',
                'commute_time_public': location.get('commute_time_public', '') if location else '',
                'public_transport_route': location.get('public_transport_route', '') if location else '',
                'prioridad_publico': prioridad_publico,
                'transporte_publico_section': transporte_publico_section.format(
                    commute_time_public=location.get('commute_time_public', '') if location else '',
                    public_transport_route=location.get('public_transport_route', '') if location else ''
                ),
            }
            # Modalidad y link
            if event_mode == 'virtual' and meeting_link:
                context['modalidad'] = 'Virtual (Google Meet)'
                context['meeting_link_text'] = f'\n🔗 Enlace: {meeting_link}'
            elif event_mode == 'hibrido' and meeting_link:
                context['modalidad'] = 'Híbrido (Google Meet disponible)'
                context['meeting_link_text'] = f'\n🔗 Enlace: {meeting_link}'
            elif event_mode == 'presencial':
                context['modalidad'] = 'Presencial'
                context['meeting_link_text'] = ''
            else:
                context['modalidad'] = event_mode.capitalize()
                context['meeting_link_text'] = ''
            # Botón/link para reagendar
            if interview_id:
                context['reagendar_link'] = f'https://tusistema.com/reagendar/{interview_id}'
                context['reagendar_text'] = '\n🔄 ¿No puedes asistir? [Haz clic aquí para reagendar]({reagendar_link})'.format(**context)
            else:
                context['reagendar_link'] = ''
                context['reagendar_text'] = ''
            if location:
                context.update({
                    'location_name': location.get('name', ''),
                    'address': location.get('address', ''),
                })
            # Notificar al candidato
            candidate_recipient = CandidateRecipient(person)
            await self.send_notification(
                recipient=candidate_recipient,
                template='interview_scheduled_candidate',
                context=context,
                channels=['email', 'whatsapp']
            )
            # Notificar al cliente
            client_recipient = ClientRecipient(vacancy.company)
            await self.send_notification(
                recipient=client_recipient,
                template='interview_scheduled_client',
                context=context,
                channels=['email', 'telegram']
            )
            return True
        except Exception as e:
            logger.error(f"Error notificando entrevista programada: {str(e)}", exc_info=True)
            return False
            
    async def send_interview_reminder(
        self,
        person: Person,
        vacancy: Vacante,
        interview_date: datetime,
        interview_type: str,
        hours_before: int = 24
    ) -> bool:
        """
        Envía un recordatorio de entrevista.
        
        Args:
            person: Candidato a entrevistar
            vacancy: Vacante relacionada
            interview_date: Fecha y hora de la entrevista
            interview_type: Tipo de entrevista
            hours_before: Horas antes de la entrevista para enviar el recordatorio
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'interview_date': interview_date.strftime('%d/%m/%Y %H:%M'),
                'interview_type': interview_type,
                'hours_before': hours_before,
                'business_unit': self.business_unit.name
            }
            
            await self.send_notification(
                notification_type=NotificationType.REMINDER.value,
                message=self._get_interview_reminder_template(),
                context=context,
                channels=['whatsapp', 'email']
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error enviando recordatorio de entrevista: {str(e)}", exc_info=True)
            return False
            
    async def notify_interview_cancelled(
        self,
        person: Person,
        vacancy: Vacante,
        interview_date: datetime,
        reason: str,
        cancelled_by: str
    ) -> bool:
        """
        Notifica sobre la cancelación de una entrevista.
        
        Args:
            person: Candidato afectado
            vacancy: Vacante relacionada
            interview_date: Fecha y hora de la entrevista cancelada
            reason: Razón de la cancelación
            cancelled_by: Quién canceló la entrevista
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'interview_date': interview_date.strftime('%d/%m/%Y %H:%M'),
                'reason': reason,
                'cancelled_by': cancelled_by,
                'business_unit': self.business_unit.name
            }
            
            # Notificar al candidato
            candidate_recipient = CandidateRecipient(person)
            await self.send_notification(
                recipient=candidate_recipient,
                template='interview_cancelled_candidate',
                context=context,
                channels=['email', 'whatsapp']
            )
            
            # Notificar al cliente
            client_recipient = ClientRecipient(vacancy.company)
            await self.send_notification(
                recipient=client_recipient,
                template='interview_cancelled_client',
                context=context,
                channels=['email', 'telegram']
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error notificando cancelación de entrevista: {str(e)}", exc_info=True)
            return False
            
    async def notify_candidate_location_update(
        self,
        person: Person,
        vacancy: Vacante,
        interview_date: datetime,
        location: Dict[str, Any],
        status: str,
        estimated_arrival: Optional[datetime] = None
    ) -> bool:
        """
        Notifica actualización de ubicación del candidato.
        
        Args:
            person: Candidato en tránsito
            vacancy: Vacante relacionada
            interview_date: Fecha y hora de la entrevista
            location: Información de ubicación actual
            status: Estado del candidato ('en_traslado', 'llegando_tarde', 'cerca')
            estimated_arrival: Tiempo estimado de llegada
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'interview_date': interview_date.strftime('%d/%m/%Y %H:%M'),
                'current_location': location.get('name', ''),
                'distance': location.get('distance', ''),
                'estimated_arrival': estimated_arrival.strftime('%H:%M') if estimated_arrival else 'N/A',
                'status': status,
                'business_unit': self.business_unit.name
            }
            
            # Notificar al cliente
            client_recipient = ClientRecipient(vacancy.company)
            await self.send_notification(
                recipient=client_recipient,
                template='candidate_location_update',
                context=context,
                channels=['telegram']
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error notificando actualización de ubicación: {str(e)}", exc_info=True)
            return False

    async def notify_interview_delay(
        self,
        person: Person,
        vacancy: Vacante,
        interview_date: datetime,
        delay_minutes: int,
        reason: str
    ) -> bool:
        """
        Notifica retraso en la entrevista.
        
        Args:
            person: Candidato retrasado
            vacancy: Vacante relacionada
            interview_date: Fecha y hora original de la entrevista
            delay_minutes: Minutos de retraso
            reason: Razón del retraso
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'interview_date': interview_date.strftime('%d/%m/%Y %H:%M'),
                'delay_minutes': delay_minutes,
                'reason': reason,
                'business_unit': self.business_unit.name
            }
            
            # Notificar al cliente
            client_recipient = ClientRecipient(vacancy.company)
            await self.send_notification(
                recipient=client_recipient,
                template='interview_delay',
                context=context,
                channels=['telegram']
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error notificando retraso: {str(e)}", exc_info=True)
            return False

    def _get_interview_scheduled_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'candidate': (
                "\U0001F4C5 *Entrevista Programada*\n\n"
                "\U0001F44B *{candidate_name}*\n\n"
                "Has sido programado para una entrevista {interview_type} para la posición de {position} en {company}.\n\n"
                "\U0001F4C5 *Fecha:* {interview_date}\n"
                "\U0001F4CD *Modalidad:* {modalidad}{meeting_link_text}\n"
                "\U0001F3E2 *Dirección:* {address}\n"
                "{reagendar_text}\n"
                "\U0001F698 *En auto:* {commute_time_car} ({traffic_level})\n"
                # Solo mostrar transporte público si prioridad_publico es True
                "{transporte_publico_section}"
                "{additional_notes}"
            ),
            'consultant': (
                "\U0001F4C5 *Nueva Entrevista Programada*\n\n"
                "\U0001F464 *Candidato:* {candidate_name}\n"
                "\U0001F4BC *Posición:* {position}\n"
                "\U0001F3E2 *Empresa:* {company}\n"
                "\U0001F4DD *Tipo:* {interview_type}\n"
                "\U0001F4C5 *Fecha:* {interview_date}\n"
                "\U0001F4CD *Modalidad:* {modalidad}{meeting_link_text}\n"
                "\U0001F3E2 *Dirección:* {address}\n"
                "{reagendar_text}\n"
                "\U0001F698 *En auto:* {commute_time_car} ({traffic_level})\n"
                # Solo mostrar transporte público si prioridad_publico es True
                "{transporte_publico_section}"
                "{additional_notes}"
                "\n\n*Recuerda que podrás brindar feedback sobre el candidato después de la entrevista. ¡Gracias por tu colaboración!*"
            )
        }
        return templates.get(recipient_type, templates['candidate'])
        
    def _get_interview_reminder_template(self) -> str:
        """Obtiene la plantilla para recordatorio de entrevista."""
        return (
            "⏰ *Recordatorio de Entrevista*\n\n"
            "👋 *{candidate_name}*\n\n"
            "Te recordamos que tienes una entrevista {interview_type} para {position} en {company} en {hours_before} horas.\n\n"
            "📅 *Fecha:* {interview_date}\n\n"
            "¡Te deseamos mucho éxito!"
        )
        
    def _get_interview_cancelled_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'candidate': (
                "❌ *Entrevista Cancelada*\n\n"
                "👋 *{candidate_name}*\n\n"
                "La entrevista programada para {position} en {company} ha sido cancelada.\n\n"
                "📅 *Fecha original:* {interview_date}\n"
                "📝 *Razón:* {reason}\n"
                "👤 *Cancelada por:* {cancelled_by}"
            ),
            'consultant': (
                "❌ *Entrevista Cancelada*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📅 *Fecha original:* {interview_date}\n"
                "📝 *Razón:* {reason}\n"
                "👤 *Cancelada por:* {cancelled_by}"
            )
        }
        return templates.get(recipient_type, templates['candidate'])

    def _get_location_update_template(self, status: str) -> str:
        """Obtiene la plantilla según el estado de ubicación."""
        templates = {
            'en_traslado': (
                "🚗 *Actualización de Ubicación*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📍 *Ubicación actual:* {current_location}\n"
                "📏 *Distancia:* {distance}\n"
                "⏰ *Llegada estimada:* {estimated_arrival}\n\n"
                "El candidato está en camino a la entrevista."
            ),
            'llegando_tarde': (
                "⚠️ *Retraso en Llegada*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📍 *Ubicación actual:* {current_location}\n"
                "⏰ *Llegada estimada:* {estimated_arrival}\n\n"
                "El candidato llegará tarde a la entrevista."
            ),
            'cerca': (
                "🎯 *Candidato Cerca*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📍 *Ubicación actual:* {current_location}\n"
                "⏰ *Llegada estimada:* {estimated_arrival}\n\n"
                "El candidato está cerca del lugar de la entrevista."
            )
        }
        return templates.get(status, templates['en_traslado'])

    def _get_delay_template(self) -> str:
        """Obtiene la plantilla para notificación de retraso."""
        return (
            "⏰ *Retraso en Entrevista*\n\n"
            "👤 *Candidato:* {candidate_name}\n"
            "💼 *Posición:* {position}\n"
            "🏢 *Empresa:* {company}\n"
            "📅 *Fecha original:* {interview_date}\n"
            "⏱️ *Retraso:* {delay_minutes} minutos\n"
            "📝 *Razón:* {reason}\n\n"
            "Por favor, tenga en cuenta este retraso."
        ) 