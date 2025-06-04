"""
Módulo para manejar notificaciones relacionadas con referencias.
"""

from typing import Dict, Optional, List
from django.utils import timezone
from datetime import timedelta
from app.models import BusinessUnit, Reference, Person
from app.ats.chatbot.core.notifications import NotificationManager
from app.ats.chatbot.nlp.nlp import NLPProcessor
from app.ats.chatbot.workflow.business_units.reference_config import get_reference_config

class ReferenceNotificationManager:
    """Clase para gestionar notificaciones de referencias."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.notification_manager = NotificationManager()
        self.nlp = NLPProcessor()
        self.config = get_reference_config(business_unit.code)
    
    def send_reference_request(self, reference: Reference) -> bool:
        """
        Envía solicitud de referencia.
        
        Args:
            reference: Reference - Referencia a contactar
            
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
                'consent_link': self._generate_consent_link(reference),
                'current_year': timezone.now().year
            }
            
            # Enviar por email
            self.notification_manager.send_email(
                to_email=reference.email,
                template_name='reference_request',
                template_data=template_data,
                business_unit=self.business_unit
            )
            
            # Enviar por WhatsApp si está habilitado
            if reference.phone and self.business_unit.whatsapp_enabled:
                self.notification_manager.send_whatsapp(
                    to_phone=reference.phone,
                    template_name='reference_request',
                    template_data=template_data,
                    business_unit=self.business_unit
                )
            
            # Actualizar metadata
            reference.metadata['notifications'] = {
                'request_sent': timezone.now().isoformat(),
                'channels': ['email'] + (['whatsapp'] if reference.phone else [])
            }
            reference.save()
            
            return True
            
        except Exception as e:
            print(f"Error enviando solicitud de referencia: {e}")
            return False
    
    def send_reminder(self, reference: Reference) -> bool:
        """
        Envía recordatorio a una referencia pendiente.
        
        Args:
            reference: Reference - Referencia a recordar
            
        Returns:
            bool - True si se envió correctamente
        """
        try:
            # Verificar límite de recordatorios
            if not self._check_reminder_limit(reference):
                return False
            
            # Calcular días restantes
            days_remaining = self._calculate_days_remaining(reference)
            
            # Preparar datos para la plantilla
            template_data = {
                'reference_name': reference.name,
                'candidate_name': reference.candidate.get_full_name(),
                'business_unit': self.business_unit,
                'feedback_link': self._generate_feedback_link(reference),
                'days_remaining': days_remaining,
                'current_year': timezone.now().year
            }
            
            # Enviar por email
            self.notification_manager.send_email(
                to_email=reference.email,
                template_name='reference_reminder',
                template_data=template_data,
                business_unit=self.business_unit
            )
            
            # Enviar por WhatsApp si está habilitado
            if reference.phone and self.business_unit.whatsapp_enabled:
                self.notification_manager.send_whatsapp(
                    to_phone=reference.phone,
                    template_name='reference_reminder',
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
                template_name='welcome_candidate',
                template_data=template_data,
                business_unit=self.business_unit
            )
            
            # Enviar por WhatsApp si está habilitado
            if reference.phone and self.business_unit.whatsapp_enabled:
                self.notification_manager.send_whatsapp(
                    to_phone=reference.phone,
                    template_name='welcome_candidate',
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
                template_name='reference_thank_you',
                template_data=template_data,
                business_unit=self.business_unit
            )
            
            # Enviar por WhatsApp si está habilitado
            if reference.phone and self.business_unit.whatsapp_enabled:
                self.notification_manager.send_whatsapp(
                    to_phone=reference.phone,
                    template_name='reference_thank_you',
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
                template_name='reference_expiration',
                template_data=template_data,
                business_unit=self.business_unit
            )
            
            # Enviar por WhatsApp si está habilitado
            if reference.phone and self.business_unit.whatsapp_enabled:
                self.notification_manager.send_whatsapp(
                    to_phone=reference.phone,
                    template_name='reference_expiration',
                    template_data=template_data,
                    business_unit=self.business_unit
                )
            
            return True
            
        except Exception as e:
            print(f"Error enviando aviso de expiración: {e}")
            return False
    
    def _generate_feedback_link(self, reference: Reference) -> str:
        """Genera enlace para proporcionar feedback."""
        return f"{self.business_unit.domain}/references/{reference.id}/feedback"
    
    def _generate_consent_link(self, reference: Reference) -> str:
        """Genera enlace para dar consentimiento."""
        return f"{self.business_unit.domain}/references/{reference.id}/consent"
    
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