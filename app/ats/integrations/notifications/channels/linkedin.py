# app/ats/integrations/notifications/channels/linkedin.py
"""
Canal de notificaciones de LinkedIn para Grupo huntRED®.
"""
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.models import BusinessUnit, Person
from app.ats.integrations.notifications.channels.base import BaseNotificationChannel
from app.ats.integrations.channels.linkedin.messaging import LinkedInMessaging

logger = logging.getLogger('notifications')

class LinkedInNotificationChannel(BaseNotificationChannel):
    """Canal de notificaciones de LinkedIn."""
    
    def __init__(self, business_unit: BusinessUnit):
        super().__init__(business_unit)
        self.messaging = LinkedInMessaging(business_unit)
        
    async def send_notification(
        self,
        message: str,
        options: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Envía una notificación a través de LinkedIn.
        
        Args:
            message: Mensaje a enviar
            options: Opciones adicionales como recipient_id, template_data, etc.
            priority: Prioridad de la notificación
            
        Returns:
            Dict con el resultado de la operación
        """
        try:
            if not options or 'recipient_id' not in options:
                raise ValueError("Se requiere recipient_id en las opciones")
                
            recipient = Person.objects.get(id=options['recipient_id'])
            
            # Verificar si el destinatario es contacto de LinkedIn
            if not recipient.linkedin_connection_id:
                logger.warning(f"El destinatario {recipient.id} no es contacto de LinkedIn")
                return {
                    'success': False,
                    'error': 'Destinatario no es contacto de LinkedIn'
                }
            
            # Preparar el mensaje
            formatted_message = self._format_message(message, priority)
            
            # Enviar mensaje
            result = await self.messaging.send_message(
                connection_id=recipient.linkedin_connection_id,
                message=formatted_message,
                template_data=options.get('template_data', {})
            )
            
            # Registrar la notificación
            await self.log_notification(
                message=formatted_message,
                status='sent' if result.get('success') else 'failed',
                details={
                    'recipient_id': recipient.id,
                    'linkedin_connection_id': recipient.linkedin_connection_id,
                    'result': result
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error enviando notificación por LinkedIn: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def is_enabled(self) -> bool:
        """Verifica si el canal está habilitado."""
        return (
            super().is_enabled() and
            self.business_unit.linkedin_notifications_enabled and
            bool(self.business_unit.linkedin_api_key)
        )
        
    def get_channel_name(self) -> str:
        """Obtiene el nombre del canal."""
        return 'linkedin' 