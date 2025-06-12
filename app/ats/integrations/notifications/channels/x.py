"""
Canal de notificaciones para X (Twitter).
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from django.conf import settings
import tweepy

from app.models import BusinessUnit
from app.ats.integrations.notifications.channels.base import RequireInitiationChannel
from app.ats.integrations.notifications.channels.whatsapp import WhatsAppNotificationChannel
from app.ats.integrations.notifications.channels.telegram import TelegramNotificationChannel

logger = logging.getLogger('chatbot')

class XNotificationChannel(RequireInitiationChannel):
    """Canal de notificaciones para X (Twitter)."""
    
    def __init__(self, business_unit: BusinessUnit):
        super().__init__(business_unit)
        self.client = tweepy.Client(
            bearer_token=self.business_unit.twitter_bearer_token,
            consumer_key=self.business_unit.twitter_api_key,
            consumer_secret=self.business_unit.twitter_api_secret,
            access_token=self.business_unit.twitter_access_token,
            access_token_secret=self.business_unit.twitter_access_token_secret
        )
        # Canales alternativos para redirección
        self.whatsapp = WhatsAppNotificationChannel(business_unit)
        self.telegram = TelegramNotificationChannel(business_unit)
    
    def _get_initiation_message(self) -> str:
        """
        Obtiene el mensaje de iniciación para X.
        
        Returns:
            Mensaje de iniciación
        """
        return (
            f"¡Hola! Soy el asistente de {self.business_unit.name}. "
            "Para recibir notificaciones importantes, por favor inicia una conversación. "
            "También puedes recibir las notificaciones por WhatsApp o Telegram."
        )
    
    async def _send_initiation(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Envía el mensaje de iniciación por X.
        
        Args:
            user_id: ID del usuario
            message: Mensaje a enviar
        
        Returns:
            Dict con el resultado de la operación
        """
        try:
            # Enviar mensaje directo
            response = self.client.send_direct_message(
                recipient_id=user_id,
                text=message
            )
            
            if response and response.data:
                return {
                    'success': True,
                    'message_id': response.data['id'],
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'No se pudo enviar el mensaje'
                }
            
        except Exception as e:
            logger.error(f"Error enviando mensaje de iniciación a X: {str(e)}")
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
        Envía una notificación por X, con redirección a otros canales si es necesario.
        
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
            
            # Verificar si se puede enviar por X
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
            response = self.client.send_direct_message(
                recipient_id=user_id,
                text=formatted_message
            )
            
            if response and response.data:
                return {
                    'success': True,
                    'message_id': response.data['id'],
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # Si falla X, intentar con canales alternativos
                if options and options.get('prefer_whatsapp'):
                    return await self.whatsapp.send_notification(message, options, priority)
                elif options and options.get('prefer_telegram'):
                    return await self.telegram.send_notification(message, options, priority)
                else:
                    return {
                        'success': False,
                        'error': 'No se pudo enviar el mensaje'
                    }
            
        except Exception as e:
            logger.error(f"Error enviando notificación a X: {str(e)}")
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
            return f"🚨 URGENTE\n\n{message}"
        elif priority >= 2:
            return f"⚠️ Importante\n\n{message}"
        else:
            return message 