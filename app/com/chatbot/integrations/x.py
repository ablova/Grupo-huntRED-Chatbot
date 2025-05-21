# /home/pablo/app/com/chatbot/integrations/x.py
"""
Módulo para manejar la integración con la API de X (Twitter).
Procesa mensajes directos, menciones y publicaciones, y envía respuestas.
Optimizado para bajo uso de CPU, escalabilidad y robustez frente a fallos.
"""

import logging
import json
import httpx
import asyncio
from typing import Dict, Any, List, Optional
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from asgiref.sync import sync_to_async
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models import XAPI, BusinessUnit, Person
from app.com.chatbot.chatbot import ChatBotHandler
from app.com.chatbot.chat_state_manager import ChatStateManager
from app.com.chatbot.components.rate_limiter import RateLimiter
from app.com.chatbot.integrations.message_sender import (
    send_message, 
    send_options, 
    send_smart_options,
    send_image
)

logger = logging.getLogger('chatbot')

# Constantes
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10.0

class XHandler:
    """
    Manejador de interacciones con la API de X (Twitter).
    Se encarga de procesar mensajes directos, menciones y publicaciones.
    """
    
    def __init__(self, user_id: str, business_unit: BusinessUnit):
        """
        Inicializa el manejador de X.
        
        Args:
            user_id (str): ID del usuario en X
            business_unit (BusinessUnit): Unidad de negocio asociada
        """
        self.user_id = user_id
        self.business_unit = business_unit
        self.x_api = None
        self.chat_state_manager = ChatStateManager()
        self.rate_limiter = RateLimiter()
    
    async def initialize(self) -> bool:
        """Inicializa la conexión con la API de X."""
        try:
            self.x_api = await sync_to_async(XAPI.objects.filter(
                is_active=True, 
                business_unit=self.business_unit
            ).first)()
            
            if not self.x_api:
                logger.error(f"No se encontró configuración de XAPI activa para la unidad de negocio {self.business_unit.name}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error inicializando XHandler: {str(e)}", exc_info=True)
            return False
    
    async def handle_direct_message(self, payload: Dict[str, Any]) -> bool:
        """
        Procesa un mensaje directo entrante de X.
        
        Args:
            payload (Dict): Datos del mensaje directo recibido de X
            
        Returns:
            bool: True si el mensaje se procesó correctamente, False en caso contrario
        """
        try:
            if not await self.initialize():
                return False
                
            # Actualizar o crear el perfil del usuario
            await self._update_user_profile(payload)
            
            # Procesar el mensaje
            message_data = payload.get('direct_message_events', [{}])[0]
            message_text = message_data.get('message_create', {}).get('message_data', {}).get('text', '')
            sender_id = message_data.get('message_create', {}).get('sender_id', '')
            
            # Ignorar mensajes del propio bot
            if sender_id == self.x_api.bot_user_id:
                return True
            
            # Crear diccionario de mensaje para el chatbot
            message_dict = {
                "messages": [{"id": message_data.get('id', ''), "text": {"body": message_text}}],
                "chat": {"id": sender_id}
            }
            
            # Procesar el mensaje con el chatbot
            chatbot = ChatBotHandler()
            response = await chatbot.process_message(
                platform="x",
                user_id=sender_id,
                message=message_dict,
                business_unit=self.business_unit,
                payload=payload
            )
            
            # Enviar respuesta al usuario
            if response and 'response' in response:
                await self._send_direct_message(sender_id, response)
                
            return True
            
        except Exception as e:
            logger.error(f"Error procesando mensaje directo de X: {str(e)}", exc_info=True)
            return False
    
    async def handle_mention(self, payload: Dict[str, Any]) -> bool:
        """
        Procesa una mención en X.
        
        Args:
            payload (Dict): Datos de la mención recibida de X
            
        Returns:
            bool: True si la mención se procesó correctamente, False en caso contrario
        """
        try:
            if not await self.initialize():
                return False
                
            # Actualizar o crear el perfil del usuario
            await self._update_user_profile(payload)
            
            # Procesar la mención
            tweet_data = payload.get('tweet_create_events', [{}])[0]
            tweet_text = tweet_data.get('text', '')
            user_id = tweet_data.get('user', {}).get('id_str', '')
            tweet_id = tweet_data.get('id_str', '')
            
            # Ignorar menciones del propio bot
            if user_id == self.x_api.bot_user_id:
                return True
            
            # Crear diccionario de mensaje para el chatbot
            message_dict = {
                "messages": [{"id": tweet_id, "text": {"body": tweet_text}}],
                "chat": {"id": tweet_id}  # Usamos el ID del tweet como ID de chat
            }
            
            # Procesar la mención con el chatbot
            chatbot = ChatBotHandler()
            response = await chatbot.process_message(
                platform="x_mention",
                user_id=user_id,
                message=message_dict,
                business_unit=self.business_unit,
                payload=payload
            )
            
            # Responder a la mención
            if response and 'response' in response:
                await self._reply_to_tweet(tweet_id, response)
                
            return True
            
        except Exception as e:
            logger.error(f"Error procesando mención en X: {str(e)}", exc_info=True)
            return False
    
    async def _update_user_profile(self, payload: Dict[str, Any]) -> None:
        """Actualiza la información del perfil del usuario en la base de datos."""
        try:
            user_data = payload.get('users', {}).get(self.user_id, {})
            if user_data:
                await sync_to_async(Person.objects.update_or_create)(
                    user_id=self.user_id,
                    defaults={
                        'first_name': user_data.get('name', '').split(' ')[0],
                        'last_name': ' '.join(user_data.get('name', '').split(' ')[1:]),
                        'email': '',  # X no proporciona email por defecto
                        'metadata': {
                            'screen_name': user_data.get('screen_name', ''),
                            'profile_image_url': user_data.get('profile_image_url_https', '')
                        }
                    }
                )
        except Exception as e:
            logger.error(f"Error actualizando perfil de usuario de X: {str(e)}", exc_info=True)
    
    async def _generate_response(self, intent: Dict) -> Dict[str, Any]:
        """
        Genera una respuesta basada en el intent detectado.
        
        Args:
            intent (Dict): Diccionario con la información del intent
            
        Returns:
            Dict: Respuesta formateada para el canal
        """
        return {
            'response': intent.get('response', 'Gracias por tu mensaje. ¿En qué más puedo ayudarte?'),
            'options': intent.get('options', []),
            'type': 'text',
            'metadata': intent.get('metadata', {})
        }
    
    async def _send_direct_message(self, recipient_id: str, response: Dict[str, Any]) -> bool:
        """
        Envía un mensaje directo a un usuario en X.
        
        Args:
            recipient_id (str): ID del usuario destinatario
            response (Dict): Respuesta a enviar
            
        Returns:
            bool: True si el mensaje se envió correctamente, False en caso contrario
        """
        try:
            if not response:
                logger.warning("Respuesta vacía, no se enviará ningún mensaje directo")
                return False
                
            message = response.get('response', '')
            
            # Usar el message_sender para enviar el mensaje
            await send_message(
                platform='x_dm',
                user_id=recipient_id,
                message=message,
                business_unit=self.business_unit
            )
                
            # Manejo de metadata adicional si es necesario
            if 'metadata' in response and response['metadata'].get('requires_follow_up'):
                await self._schedule_follow_up(recipient_id, response['metadata'], is_dm=True)
                
            return True
                
        except Exception as e:
            logger.error(f"Error al enviar mensaje directo en X: {str(e)}", exc_info=True)
            return False
    
    async def _reply_to_tweet(self, tweet_id: str, response: Dict[str, Any]) -> bool:
        """
        Responde a un tweet con una mención.
        
        Args:
            tweet_id (str): ID del tweet al que se responde
            response (Dict): Respuesta a enviar
            
        Returns:
            bool: True si la respuesta se envió correctamente, False en caso contrario
        """
        try:
            if not response:
                logger.warning("Respuesta vacía, no se publicará ninguna respuesta")
                return False
                
            message = response.get('response', '')
            
            # Usar el message_sender para publicar la respuesta
            await send_message(
                platform='x_tweet',
                user_id=tweet_id,  # Usamos el ID del tweet como user_id para el message_sender
                message=message,
                business_unit=self.business_unit,
                in_reply_to_status_id=tweet_id
            )
                
            # Manejo de metadata adicional si es necesario
            if 'metadata' in response and response['metadata'].get('requires_follow_up'):
                await self._schedule_follow_up(tweet_id, response['metadata'], is_dm=False)
                
            return True
                
        except Exception as e:
            logger.error(f"Error al responder a tweet en X: {str(e)}", exc_info=True)
            return False
    
    async def _schedule_follow_up(self, target_id: str, metadata: Dict[str, Any], is_dm: bool = True) -> None:
        """
        Programa un seguimiento basado en los metadatos.
        
        Args:
            target_id (str): ID del objetivo (usuario para DM o tweet para respuesta)
            metadata (Dict): Metadatos para el seguimiento
            is_dm (bool): Indica si es un mensaje directo (True) o respuesta a tweet (False)
        """
        try:
            follow_up_time = metadata.get('follow_up_time', 3600)  # 1 hora por defecto
            follow_up_message = metadata.get('follow_up_message', '')
            
            if follow_up_message and follow_up_time > 0:
                await asyncio.sleep(follow_up_time)
                
                if is_dm:
                    await send_message(
                        platform='x_dm',
                        user_id=target_id,
                        message=follow_up_message,
                        business_unit=self.business_unit
                    )
                else:
                    await send_message(
                        platform='x_tweet',
                        user_id=target_id,  # Usamos el ID del tweet como user_id
                        message=follow_up_message,
                        business_unit=self.business_unit
                    )
        except Exception as e:
            logger.error(f"Error al programar seguimiento en X: {str(e)}", exc_info=True)

@csrf_exempt
async def x_webhook(request):
    """
    Endpoint webhook para recibir eventos de X (Twitter).
    
    Args:
        request: Objeto de solicitud HTTP
        
    Returns:
        JsonResponse: Respuesta para X
    """
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
        
        # Verificar el token de verificación de X (para el reto de CRC)
        if request.GET.get('crc_token'):
            # Implementar lógica de verificación CRC aquí
            return JsonResponse({
                "response_token": f"sha256={_generate_crc_response(request.GET['crc_token'])}"
            })
            
        payload = json.loads(request.body.decode("utf-8"))
        
        # Procesar el evento según su tipo
        if 'direct_message_events' in payload:
            # Es un mensaje directo
            handler = XHandler(
                user_id=payload.get('for_user_id', ''),
                business_unit=await _get_business_unit()
            )
            await handler.handle_direct_message(payload)
            
        elif 'tweet_create_events' in payload:
            # Es una mención o respuesta
            handler = XHandler(
                user_id=payload.get('for_user_id', ''),
                business_unit=await _get_business_unit()
            )
            await handler.handle_mention(payload)
        
        return JsonResponse({"status": "success"}, status=200)
        
    except json.JSONDecodeError:
        logger.error("Error al decodificar el cuerpo de la solicitud JSON")
        return JsonResponse({"status": "error", "message": "Cuerpo de solicitud JSON no válido"}, status=400)
    except Exception as e:
        logger.error(f"Error en x_webhook: {str(e)}", exc_info=True)
        return JsonResponse({"status": "error", "message": "Error interno del servidor"}, status=500)

async def _get_business_unit():
    """Obtiene la unidad de negocio predeterminada para X."""
    try:
        x_api = await sync_to_async(XAPI.objects.filter(is_active=True).first)()
        if x_api:
            return await sync_to_async(lambda: x_api.business_unit)()
        return None
    except Exception as e:
        logger.error(f"Error obteniendo unidad de negocio para X: {str(e)}", exc_info=True)
        return None

def _generate_crc_response(crc_token: str) -> str:
    """
    Genera una respuesta de verificación CRC para X.
    
    Args:
        crc_token (str): Token de verificación de X
        
    Returns:
        str: Token de respuesta firmado con HMAC-SHA256
    """
    import hmac
    import hashlib
    import base64
    import os
    
    # Obtener el consumer secret de las variables de entorno
    consumer_secret = os.getenv('X_API_SECRET', '').encode('utf-8')
    
    # Generar la firma
    signature = hmac.new(
        consumer_secret,
        msg=crc_token.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    
    # Codificar en base64
    return base64.b64encode(signature).decode('utf-8')

# Funciones de utilidad para compatibilidad con el código existente

async def send_x_direct_message(recipient_id: str, message: str, api_instance: XAPI) -> bool:
    """
    Envía un mensaje directo a un usuario en X.
    
    Args:
        recipient_id (str): ID del usuario destinatario
        message (str): Mensaje a enviar
        api_instance (XAPI): Instancia de la API de X
        
    Returns:
        bool: True si el mensaje se envió correctamente, False en caso contrario
    """
    try:
        handler = XHandler(user_id=recipient_id, business_unit=api_instance.business_unit)
        await handler.initialize()
        await handler._send_direct_message(recipient_id, {'response': message})
        return True
    except Exception as e:
        logger.error(f"Error enviando mensaje directo en X: {str(e)}", exc_info=True)
        return False

async def send_x_tweet(message: str, api_instance: XAPI, in_reply_to: str = None) -> bool:
    """
    Publica un tweet o responde a uno existente.
    
    Args:
        message (str): Contenido del tweet
        api_instance (XAPI): Instancia de la API de X
        in_reply_to (str, opcional): ID del tweet al que se responde
        
    Returns:
        bool: True si el tweet se publicó correctamente, False en caso contrario
    """
    try:
        # Esta es una implementación simplificada
        # En una implementación real, usarías la API de X para publicar el tweet
        logger.info(f"Publicando en X: {message}" + (f" (en respuesta a {in_reply_to})" if in_reply_to else ""))
        return True
    except Exception as e:
        logger.error(f"Error publicando en X: {str(e)}", exc_info=True)
        return False
