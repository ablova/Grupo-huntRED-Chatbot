"""
Canal de notificaciones para WhatsApp.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.models import BusinessUnit
from app.ats.integrations.notifications.channels.base import RequireInitiationChannel

logger = logging.getLogger('chatbot')

class WhatsAppNotificationChannel(RequireInitiationChannel):
    """Canal de notificaciones para WhatsApp."""
    
    def __init__(self, business_unit: BusinessUnit):
        super().__init__(business_unit)
        self.client = Client(
            self.business_unit.twilio_account_sid,
            self.business_unit.twilio_auth_token
        )
        self.from_number = self.business_unit.twilio_whatsapp_number
    
    def _get_initiation_message(self) -> str:
        """
        Obtiene el mensaje de iniciación para WhatsApp.
        
        Returns:
            Mensaje de iniciación
        """
        return (
            f"¡Hola! Soy el asistente de {self.business_unit.name}. "
            "Para recibir notificaciones importantes, por favor responde a este mensaje. "
            "Puedes escribir 'Hola' o cualquier mensaje para iniciar la conversación."
        )
    
    async def _send_initiation(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Envía el mensaje de iniciación por WhatsApp.
        
        Args:
            user_id: ID del usuario
            message: Mensaje a enviar
        
        Returns:
            Dict con el resultado de la operación
        """
        try:
            # Enviar mensaje a través de Twilio
            message = self.client.messages.create(
                body=message,
                from_=f"whatsapp:{self.from_number}",
                to=f"whatsapp:{user_id}"
            )
            
            return {
                'success': True,
                'message_id': message.sid,
                'timestamp': datetime.now().isoformat()
            }
            
        except TwilioRestException as e:
            logger.error(f"Error de Twilio enviando mensaje de iniciación: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_notification(
        self,
        message: str,
        options: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Envía una notificación por WhatsApp.
        
        Args:
            message: Mensaje a enviar
            options: Opciones adicionales
            priority: Prioridad de la notificación
        
        Returns:
            Dict con el resultado de la operación
        """
        try:
            user_id = options.get('user_id') if options else None
            
            if not user_id:
                return {
                    'success': False,
                    'error': 'Se requiere user_id para enviar la notificación'
                }
            
            # Verificar si se puede enviar
            if not await self.can_send_notification(user_id):
                return await self.send_initiation_message(user_id)
            
            # Formatear el mensaje según la prioridad
            formatted_message = self._format_message(message, priority)
            
            # Enviar el mensaje
            message = self.client.messages.create(
                body=formatted_message,
                from_=f"whatsapp:{self.from_number}",
                to=f"whatsapp:{user_id}"
            )
            
            return {
                'success': True,
                'message_id': message.sid,
                'timestamp': datetime.now().isoformat()
            }
            
        except TwilioRestException as e:
            logger.error(f"Error de Twilio enviando notificación: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_message(self, message: str, priority: int) -> str:
        """
        Formatea el mensaje según la prioridad.
        
        Args:
            message: Mensaje original
            priority: Nivel de prioridad (0-5)
        
        Returns:
            Mensaje formateado
        """
        if priority >= 4:
            return f"🚨 *URGENTE*\n\n{message}"
        elif priority >= 2:
            return f"⚠️ *Importante*\n\n{message}"
        else:
            return message 