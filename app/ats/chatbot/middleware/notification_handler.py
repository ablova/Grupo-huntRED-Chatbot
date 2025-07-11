# /home/pablo/app/ats/chatbot/middleware/notification_handler.py
"""
Middleware para manejar mensajes entrantes en relación con notificaciones de servicio.

Este módulo evita que las respuestas a notificaciones de servicio entren en el flujo 
normal del chatbot. Implementa un período de gracia durante el cual las respuestas
a notificaciones se manejan de forma especial.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from django.utils import timezone
from django.db.models import Q

from app.models import ChatState, Person, BusinessUnit
from app.ats.chatbot.core.chatbot import ChatBotHandler
from app.ats.integrations.services import MessageService

logger = logging.getLogger('middleware')

class NotificationMiddleware:
    """
    Middleware para interceptar y manejar respuestas a notificaciones de servicio.
    """
    
    @staticmethod
    def should_intercept(user_id: str, channel: str, message: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Determina si un mensaje debe ser interceptado por ser respuesta a una notificación.
        
        Args:
            user_id: ID del usuario (número de teléfono para WhatsApp)
            channel: Canal de comunicación ('whatsapp', 'email', etc.)
            message: Contenido del mensaje recibido
            
        Returns:
            Tupla (intercept, notification_data)
            - intercept: True si debe interceptarse, False si debe procesarse normalmente
            - notification_data: Datos de la notificación relacionada, o None si no aplica
        """
        try:
            # Solo aplica a ciertos canales (principalmente WhatsApp)
            if channel not in ['whatsapp', 'telegram']:
                return False, None
                
            # Buscamos si el usuario tiene un ChatState con estado de notificación
            chat_state = ChatState.objects.filter(
                user_id=user_id,
                channel=channel,
                state='service_notification'
            ).first()
            
            if not chat_state or not chat_state.metadata:
                return False, None
                
            # Obtenemos los datos de la notificación
            notification_data = chat_state.metadata.get('service_notification')
            if not notification_data:
                return False, None
                
            # Verificamos si estamos dentro del período de gracia
            sent_at_str = notification_data.get('sent_at')
            grace_period = notification_data.get('grace_period_seconds', 300)  # 5 minutos por defecto
            
            if not sent_at_str:
                return False, None
                
            # Convertimos la fecha a datetime
            try:
                sent_at = datetime.fromisoformat(sent_at_str)
                now = timezone.now()
                
                # Calculamos si estamos dentro del período de gracia
                grace_end = sent_at + timedelta(seconds=grace_period)
                
                if now <= grace_end:
                    logger.info(f"Interceptando respuesta a notificación para {user_id} (dentro del período de gracia)")
                    return True, notification_data
                    
                # Si pasó el período de gracia, restauramos el estado anterior
                previous_state = notification_data.get('previous_state')
                if previous_state:
                    chat_state.state = previous_state
                    
                    # Eliminamos los datos de notificación
                    metadata = chat_state.metadata
                    metadata.pop('service_notification', None)
                    chat_state.metadata = metadata
                    
                    chat_state.save(update_fields=['state', 'metadata'])
                    logger.info(f"Período de gracia finalizado, restaurando estado para {user_id}")
                    
                return False, None
                
            except (ValueError, TypeError):
                logger.error(f"Error al parsear fecha de notificación: {sent_at_str}")
                return False, None
                
        except Exception as e:
            logger.error(f"Error al verificar intercepción de notificación: {e}")
            return False, None
    
    @staticmethod
    async def handle_notification_response(user_id: str, channel: str, message: str, notification_data: Dict[str, Any]) -> str:
        """
        Maneja las respuestas a las notificaciones de servicio.
        
        Args:
            user_id: ID del usuario
            channel: Canal de comunicación
            message: Contenido del mensaje recibido
            notification_data: Datos de la notificación relacionada
            
        Returns:
            Respuesta automática a enviar al usuario
        """
        try:
            # Verificamos si el mensaje contiene alguna palabra clave
            message_lower = message.lower()
            
            # Palabras clave comunes que podrían indicar que el usuario quiere interactuar
            keywords = [
                'gracias', 'thanks', 'ok', 'entendido', 'recibido', 'confirmo',
                'bien', 'perfecto', 'de acuerdo', 'listo', 'confirmado', 'excelente'
            ]
            
            # Si el mensaje contiene alguna palabra clave positiva, enviamos un mensaje amigable
            if any(kw in message_lower for kw in keywords):
                return (
                    "Gracias por su confirmación. Este es un mensaje automático.\n\n"
                    "Si necesita ayuda o desea interactuar con el chatbot, por favor envíe un nuevo mensaje "
                    "en lugar de responder a esta notificación."
                )
            
            # Si no contiene palabras clave, explicamos que debe enviar un nuevo mensaje
            return (
                "Este mensaje es parte de una notificación informativa y no será procesado por el chatbot.\n\n"
                "Si desea consultar vacantes, actualizar su perfil o realizar cualquier otra acción, "
                "por favor envíe un nuevo mensaje en lugar de responder a esta notificación."
            )
            
        except Exception as e:
            logger.error(f"Error al manejar respuesta a notificación: {e}")
            return (
                "Lo siento, no puedo procesar su respuesta en este momento. "
                "Si necesita ayuda, por favor envíe un nuevo mensaje."
            )
