"""
Canal de notificaciones para SMS.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.models import BusinessUnit
from app.ats.integrations.notifications.channels.base import RequireInitiationChannel
from app.ats.integrations.notifications.channels.whatsapp import WhatsAppNotificationChannel
from app.ats.integrations.notifications.channels.telegram import TelegramNotificationChannel

logger = logging.getLogger('chatbot')

class SMSNotificationChannel(RequireInitiationChannel):
    """Canal de notificaciones para SMS."""
    
    def __init__(self, business_unit: BusinessUnit):
        super().__init__(business_unit)
        self.client = Client(
            self.business_unit.twilio_account_sid,
            self.business_unit.twilio_auth_token
        )
        self.from_number = self.business_unit.twilio_phone_number
        # Canales alternativos para redirección
        self.whatsapp = WhatsAppNotificationChannel(business_unit)
        self.telegram = TelegramNotificationChannel(business_unit)
    
    def _get_initiation_message(self) -> str:
        """
        Obtiene el mensaje de iniciación para SMS.
        
        Returns:
            Mensaje de iniciación
        """
        return (
            f"¡Hola! Soy el asistente de {self.business_unit.name}. "
            "Para recibir notificaciones importantes, por favor responde a este mensaje. "
            "También puedes recibir las notificaciones por WhatsApp, Telegram, o incluso por LinkedIN."
        )
    
    async def _send_initiation(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Envía el mensaje de iniciación por SMS.
        
        Args:
            user_id: ID del usuario
            message: Mensaje a enviar
        
        Returns:
            Dict con el resultado de la operación
        """
        try:
            # Enviar SMS a través de Twilio
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=user_id
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
        Envía una notificación por SMS, con redirección a otros canales si es necesario.
        
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
            
            # Verificar si se puede enviar por SMS
            if not await self.can_send_notification(user_id):
                # Intentar enviar por canales alternativos
                if options and options.get('prefer_whatsapp'):
                    return await self.whatsapp.send_notification(message, options, priority)
                elif options and options.get('prefer_telegram'):
                    return await self.telegram.send_notification(message, options, priority)
                else:
                    return await self.send_initiation_message(user_id)
            
            # Formatear el mensaje según la prioridad
            formatted_message = self._format_message(message, priority)
            
            # Enviar el mensaje
            message = self.client.messages.create(
                body=formatted_message,
                from_=self.from_number,
                to=user_id
            )
            
            return {
                'success': True,
                'message_id': message.sid,
                'timestamp': datetime.now().isoformat()
            }
            
        except TwilioRestException as e:
            logger.error(f"Error de Twilio enviando notificación: {str(e)}")
            # Intentar con canales alternativos
            if options and options.get('prefer_whatsapp'):
                return await self.whatsapp.send_notification(message, options, priority)
            elif options and options.get('prefer_telegram'):
                return await self.telegram.send_notification(message, options, priority)
            else:
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
            return f"URGENTE: {message}"
        elif priority >= 2:
            return f"IMPORTANTE: {message}"
        else:
            return message 