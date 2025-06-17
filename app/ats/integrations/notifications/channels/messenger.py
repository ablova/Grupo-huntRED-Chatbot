# app/ats/integrations/notifications/channels/messenger.py
"""
Canal de notificaciones para Facebook Messenger.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from django.conf import settings
import aiohttp

from app.models import BusinessUnit
from app.ats.integrations.notifications.channels.base import RequireInitiationChannel

logger = logging.getLogger('chatbot')

class MessengerNotificationChannel(RequireInitiationChannel):
    """Canal de notificaciones para Facebook Messenger."""
    
    def __init__(self, business_unit: BusinessUnit):
        super().__init__(business_unit)
        self.page_token = self.business_unit.facebook_page_token
        self.api_version = 'v18.0'  # Versión actual de la API de Facebook
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
    
    def _get_initiation_message(self) -> str:
        """
        Obtiene el mensaje de iniciación para Messenger.
        
        Returns:
            Mensaje de iniciación
        """
        return (
            f"¡Hola! Soy el asistente de {self.business_unit.name}. "
            "Para recibir notificaciones importantes, por favor inicia una conversación. "
            "Puedes escribir 'Hola' o cualquier mensaje para comenzar."
        )
    
    async def _send_initiation(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Envía el mensaje de iniciación por Messenger.
        
        Args:
            user_id: ID del usuario
            message: Mensaje a enviar
        
        Returns:
            Dict con el resultado de la operación
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/me/messages"
                data = {
                    "recipient": {"id": user_id},
                    "message": {
                        "text": message,
                        "quick_replies": [
                            {
                                "content_type": "text",
                                "title": "Hola",
                                "payload": "INITIATION_HELLO"
                            }
                        ]
                    }
                }
                
                async with session.post(url, json=data, params={"access_token": self.page_token}) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get('message_id'):
                        return {
                            'success': True,
                            'message_id': result['message_id'],
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        error = result.get('error', {}).get('message', 'Error desconocido')
                        return {
                            'success': False,
                            'error': error
                        }
            
        except Exception as e:
            logger.error(f"Error enviando mensaje de iniciación a Messenger: {str(e)}")
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
        Envía una notificación por Messenger.
        
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
            
            # Preparar el mensaje
            message_data = {
                "recipient": {"id": user_id},
                "message": {"text": formatted_message}
            }
            
            # Añadir botones si se especifican
            if options and 'buttons' in options:
                message_data["message"]["quick_replies"] = [
                    {
                        "content_type": "text",
                        "title": button.get('title', ''),
                        "payload": button.get('payload', '')
                    }
                    for button in options['buttons']
                ]
            
            # Enviar el mensaje
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/me/messages"
                async with session.post(url, json=message_data, params={"access_token": self.page_token}) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get('message_id'):
                        return {
                            'success': True,
                            'message_id': result['message_id'],
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        error = result.get('error', {}).get('message', 'Error desconocido')
                        return {
                            'success': False,
                            'error': error
                        }
            
        except Exception as e:
            logger.error(f"Error enviando notificación a Messenger: {str(e)}")
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