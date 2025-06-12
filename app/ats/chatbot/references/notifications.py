"""
Módulo para manejar notificaciones relacionadas con referencias.

Este módulo utiliza el servicio unificado de notificaciones para enviar
comunicaciones a través de múltiples canales de manera consistente.
"""

from typing import Dict, Optional, List, Any
from django.utils import timezone
from datetime import timedelta
from asgiref.sync import sync_to_async
from app.models import BusinessUnit, Reference, Person
from app.ats.integrations.notifications import notification_service
from app.ats.chatbot.nlp.nlp import NLPProcessor
from app.ats.chatbot.workflow.business_units.reference_config import get_reference_config

class ReferenceNotificationManager:
    """
    Gestiona notificaciones de referencias usando el servicio unificado.
    
    Esta clase se encarga de enviar notificaciones relacionadas con referencias
    utilizando el sistema centralizado de notificaciones, lo que permite un
    manejo consistente a través de múltiples canales.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el gestor de notificaciones de referencias.
        
        Args:
            business_unit: Unidad de negocio para la configuración
        """
        self.business_unit = business_unit
        self.nlp = NLPProcessor()
        self.config = get_reference_config(business_unit.code)
        self.logger = logging.getLogger(__name__)
    
    async def send_reference_request(self, reference: Reference) -> bool:
        """
        Envía una solicitud de referencia de manera asíncrona.
        
        Args:
            reference: Referencia a contactar
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Preparar datos para la plantilla
            template_data = await self._prepare_template_data(reference)
            
            # Determinar canales a utilizar
            channels = ['email']
            if reference.phone and self.business_unit.whatsapp_enabled:
                channels.append('whatsapp')
            
            # Enviar notificación usando el servicio unificado
            success = await notification_service.send_template_notification(
                recipient=reference.candidate,  # Asumiendo que reference tiene relación con candidate
                template_name='reference_request',
                context={
                    **template_data,
                    'subject': f'Solicitud de referencia - {self.business_unit.name}'
                },
                channels=channels,
                business_unit=self.business_unit
            )
            
            if success:
                await self._update_reference_metadata(reference, channels)
            
            return success
            
        except Exception as e:
            self.logger.error(
                f"Error enviando solicitud de referencia {reference.id}: {str(e)}",
                exc_info=True
            )
            return False
    
    async def send_reminder(self, reference: Reference) -> bool:
        """
        Envía un recordatorio a una referencia pendiente de manera asíncrona.
        
        Args:
            reference: Referencia a recordar
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Verificar límite de recordatorios
            if not await sync_to_async(self._check_reminder_limit)(reference):
                self.logger.warning(f"Límite de recordatorios alcanzado para referencia {reference.id}")
                return False
            
            # Calcular días restantes
            days_remaining = await sync_to_async(self._calculate_days_remaining)(reference)
            
            # Preparar datos para la plantilla
            template_data = await self._prepare_template_data(reference)
            template_data.update({
                'days_remaining': days_remaining,
                'subject': f'Recordatorio: Solicitud de referencia - {self.business_unit.name}'
            })
            
            # Enviar por email
            self.notification_manager.send_email(
                to_email=reference.email,
                template_name='references/email/reference_reminder.html',
                template_data=template_data,
                business_unit=self.business_unit
            )
            
            # Enviar por WhatsApp si está habilitado
            if reference.phone and self.business_unit.whatsapp_enabled:
                self.notification_manager.send_whatsapp(
                    to_phone=reference.phone,
                    template_name='references/whatsapp/reference_reminder.txt',
                    template_data=template_data,
                    business_unit=self.business_unit
                )
            
            # Actualizar metadata
            if 'notifications' not in reference.metadata:
                reference.metadata['notifications'] = {}
            
            if 'reminders' not in reference.metadata['notifications']:
                reference.metadata['notifications']['reminders'] = []
            
            reference.metadata['notifications']['reminders'].append({
                'sent_at': timezone.now().isoformat(),
                'channels': ['email'] + (['whatsapp'] if reference.phone else []),
                'days_remaining': days_remaining
            })
            reference.save()
            
            return True
            
        except Exception as e:
            print(f"Error enviando recordatorio: {e}")
            return False
    
    def send_welcome_to_candidate(self, reference: Reference) -> bool:
        """
        Envía mensaje de bienvenida al candidato convertido.
        
        Args:
            reference: Reference - Referencia convertida
            
        Returns:
            bool - True si se envió correctamente
        """
        try:
            # Preparar datos para la plantilla
            template_data = {
                'candidate_name': reference.name,
                'business_unit': self.business_unit,
                'profile_link': self._generate_profile_link(reference),
                'current_year': timezone.now().year
            }
            
            # Enviar por email
            self.notification_manager.send_email(
                to_email=reference.email,
                template_name='references/email/welcome_converted_reference.html',
                template_data=template_data,
                business_unit=self.business_unit
            )
            
            # Enviar por WhatsApp si está habilitado
            if reference.phone and self.business_unit.whatsapp_enabled:
                self.notification_manager.send_whatsapp(
                    to_phone=reference.phone,
                    template_name='references/whatsapp/welcome_converted_reference.txt',
                    template_data=template_data,
                    business_unit=self.business_unit
                )
            
            return True
            
        except Exception as e:
            print(f"Error enviando bienvenida: {e}")
            return False
    
    def send_thank_you(self, reference: Reference) -> bool:
        """
        Envía agradecimiento después de proporcionar la referencia.
        
        Args:
            reference: Reference - Referencia que respondió
            
        Returns:
            bool - True si se envió correctamente
        """
        try:
            # Preparar datos para la plantilla
            template_data = {
                'reference_name': reference.name,
                'candidate_name': reference.candidate.get_full_name(),
                'business_unit': self.business_unit,
                'current_year': timezone.now().year
            }
            
            # Enviar por email
            self.notification_manager.send_email(
                to_email=reference.email,
                template_name='references/email/reference_thank_you.html',
                template_data=template_data,
                business_unit=self.business_unit
            )
            
            # Enviar por WhatsApp si está habilitado
            if reference.phone and self.business_unit.whatsapp_enabled:
                self.notification_manager.send_whatsapp(
                    to_phone=reference.phone,
                    template_name='references/whatsapp/reference_thank_you.txt',
                    template_data=template_data,
                    business_unit=self.business_unit
                )
            
            return True
            
        except Exception as e:
            print(f"Error enviando agradecimiento: {e}")
            return False
    
    def send_expiration_notice(self, reference: Reference) -> bool:
        """
        Envía aviso de expiración de la referencia.
        
        Args:
            reference: Reference - Referencia por expirar
            
        Returns:
            bool - True si se envió correctamente
        """
        try:
            # Preparar datos para la plantilla
            template_data = {
                'reference_name': reference.name,
                'candidate_name': reference.candidate.get_full_name(),
                'business_unit': self.business_unit,
                'feedback_link': self._generate_feedback_link(reference),
                'current_year': timezone.now().year
            }
            
            # Enviar por email
            self.notification_manager.send_email(
                to_email=reference.email,
                template_name='references/email/reference_expiration.html',
                template_data=template_data,
                business_unit=self.business_unit
            )
            
            # Enviar por WhatsApp si está habilitado
            if reference.phone and self.business_unit.whatsapp_enabled:
                self.notification_manager.send_whatsapp(
                    to_phone=reference.phone,
                    template_name='references/whatsapp/reference_expiration.txt',
                    template_data=template_data,
                    business_unit=self.business_unit
                )
            
            return True
            
        except Exception as e:
            print(f"Error enviando aviso de expiración: {e}")
            return False
    
    async def _prepare_template_data(self, reference: Reference) -> Dict[str, Any]:
        """
        Prepara los datos comunes para las plantillas de notificación.
        
        Args:
            reference: Referencia para la que preparar los datos
            
        Returns:
            Dict con los datos de la plantilla
        """
        return {
            'reference_name': reference.name,
            'candidate_name': await sync_to_async(lambda: reference.candidate.get_full_name())(),
            'business_unit': self.business_unit.name,
            'feedback_link': self._generate_feedback_link(reference),
            'consent_link': self._generate_consent_link(reference),
            'current_year': timezone.now().year
        }
    
    async def _update_reference_metadata(self, reference: Reference, channels: List[str]) -> None:
        """
        Actualiza los metadatos de la referencia con información de notificación.
        
        Args:
            reference: Referencia a actualizar
            channels: Canales utilizados para la notificación
        """
        metadata = reference.metadata or {}
        notifications = metadata.get('notifications', {})
        
        notifications.update({
            'last_notification': timezone.now().isoformat(),
            'channels': channels,
            'attempts': notifications.get('attempts', 0) + 1
        })
        
        metadata['notifications'] = notifications
        reference.metadata = metadata
        await sync_to_async(reference.save)()
    
    def _generate_feedback_link(self, reference: Reference) -> str:
        """
        Genera un enlace único para feedback.
        
        Args:
            reference: Referencia para la que generar el enlace
            
        Returns:
            str: URL completa para feedback
        """
        return f"{settings.BASE_URL}/references/feedback/{reference.uuid}"
    
    def _generate_consent_link(self, reference: Reference) -> str:
        """
        Genera un enlace único para consentimiento.
        
        Args:
            reference: Referencia para la que generar el enlace
            
        Returns:
            str: URL completa para consentimiento
        """
        return f"{settings.BASE_URL}/references/consent/{reference.uuid}"
    
    def _generate_profile_link(self, reference: Reference) -> str:
        """Genera enlace al perfil del candidato."""
        return f"{self.business_unit.domain}/candidates/{reference.converted_to.id}"
    
    def _check_reminder_limit(self, reference: Reference) -> bool:
        """Verifica si se puede enviar más recordatorios."""
        if 'notifications' not in reference.metadata:
            return True
            
        reminders = reference.metadata['notifications'].get('reminders', [])
        if len(reminders) >= 3:  # Máximo 3 recordatorios
            return False
            
        # Verificar tiempo desde último recordatorio
        if reminders:
            last_reminder = timezone.datetime.fromisoformat(reminders[-1]['sent_at'])
            if timezone.now() - last_reminder < timedelta(days=2):
                return False
                
        return True
    
    def _calculate_days_remaining(self, reference: Reference) -> int:
        """Calcula días restantes para responder."""
        expiration_date = reference.created_at + timedelta(days=self.config['response_days'])
        return (expiration_date - timezone.now()).days 