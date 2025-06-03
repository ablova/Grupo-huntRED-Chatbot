# /home/pablo/app/ats/chatbot/integrations/slack.py
#
# Módulo para manejar la integración con Slack API.
# Procesa mensajes entrantes, envía respuestas, y gestiona interacciones como botones y archivos.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

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
from app.models import SlackAPI, BusinessUnit, Person
from app.ats.chatbot.chatbot import ChatBotHandler
from app.ats.chatbot.components.chat_state_manager import ChatStateManager
from app.ats.chatbot.components.rate_limiter import RateLimiter
from app.ats.chatbot.integrations.message_sender import (
    send_message, 
    send_options, 
    send_smart_options,
    send_image
)

logger = logging.getLogger('chatbot')

# Constantes
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10.0

class SlackHandler:
    """
    Manejador de interacciones con la API de Slack.
    Se encarga de procesar mensajes entrantes y enviar respuestas.
    """
    
    def __init__(self, user_id: str, business_unit: BusinessUnit):
        """
        Inicializa el manejador de Slack.
        
        Args:
            user_id (str): ID del usuario en Slack
            business_unit (BusinessUnit): Unidad de negocio asociada
        """
        self.user_id = user_id
        self.business_unit = business_unit
        self.slack_api = None
        self.chat_state_manager = ChatStateManager()
        self.rate_limiter = RateLimiter()
    
    async def initialize(self):
        """Inicializa la conexión con la API de Slack."""
        try:
            self.slack_api = await sync_to_async(SlackAPI.objects.filter(
                is_active=True, 
                business_unit=self.business_unit
            ).first)()
            
            if not self.slack_api:
                logger.error(f"No se encontró configuración de SlackAPI activa para la unidad de negocio {self.business_unit.name}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error inicializando SlackHandler: {str(e)}", exc_info=True)
            return False
    
    async def handle_message(self, payload: Dict[str, Any]) -> bool:
        """
        Procesa un mensaje entrante de Slack.
        
        Args:
            payload (Dict): Datos del mensaje recibido de Slack
            
        Returns:
            bool: True si el mensaje se procesó correctamente, False en caso contrario
        """
        try:
            if not await self.initialize():
                return False
                
            event = payload.get('event', {})
            text = event.get('text', '').strip()
            channel = event.get('channel', '')
            files = event.get('files', [])
            
            # Actualizar o crear el perfil del usuario
            await self._update_user_profile()
            
            # Procesar el mensaje
            if files:
                file = files[0]
                message_dict = {
                    "messages": [{
                        "id": event.get('ts', ''),
                        "file_id": file.get('url_private', ''),
                        "file_name": file.get('name', ''),
                        "mime_type": file.get('mimetype', '')
                    }],
                    "chat": {"id": channel}
                }
            else:
                message_dict = {
                    "messages": [{"id": event.get('ts', ''), "text": {"body": text}}],
                    "chat": {"id": channel}
                }
            
            # Procesar el mensaje con el chatbot
            chatbot = ChatBotHandler()
            response = await chatbot.process_message(
                platform="slack",
                user_id=self.user_id,
                message=message_dict,
                business_unit=self.business_unit,
                payload=payload
            )
            
            # Enviar respuesta al usuario
            if response and 'response' in response:
                await self._send_response(channel, response)
                
            return True
            
        except Exception as e:
            logger.error(f"Error procesando mensaje de Slack: {str(e)}", exc_info=True)
            return False
    
    async def _update_user_profile(self) -> None:
        """Actualiza la información del perfil del usuario en la base de datos."""
        try:
            user_data = await fetch_slack_user_data(self.user_id, self.slack_api)
            if user_data:
                await sync_to_async(Person.objects.update_or_create)(
                    user_id=self.user_id,
                    defaults={
                        'first_name': user_data.get('nombre', ''),
                        'last_name': user_data.get('apellido_paterno', ''),
                        'email': user_data.get('metadata', {}).get('email', ''),
                        'metadata': user_data.get('metadata', {})
                    }
                )
        except Exception as e:
            logger.error(f"Error actualizando perfil de usuario: {str(e)}", exc_info=True)
    
    async def _generate_response(self, intent: Dict) -> Dict[str, Any]:
        """
        Genera una respuesta basada en el intent detectado.
        
        Args:
            intent (Dict): Diccionario con la información del intent
            
        Returns:
            Dict: Respuesta formateada para el canal
        """
        return {
            'response': intent.get('response', 'Lo siento, no puedo responder a eso en este momento.'),
            'options': intent.get('options', []),
            'type': 'text',
            'metadata': intent.get('metadata', {})
        }
    
    async def _send_response(self, channel_id: str, response: Dict[str, Any]) -> bool:
        """
        Envía una respuesta al usuario en Slack.
        
        Args:
            channel_id (str): ID del canal o usuario en Slack
            response (Dict): Respuesta a enviar
            
        Returns:
            bool: True si el mensaje se envió correctamente, False en caso contrario
        """
        try:
            if not response:
                logger.warning("Respuesta vacía, no se enviará ningún mensaje")
                return False
                
            if response.get('type') == 'text' and response.get('options'):
                # Usar el message_sender para enviar opciones
                await send_options(
                    platform='slack',
                    user_id=channel_id,
                    message=response['response'],
                    options=response['options'],
                    business_unit=self.business_unit
                )
            elif response.get('type') == 'image':
                # Usar el message_sender para enviar imágenes
                await send_image(
                    platform='slack',
                    user_id=channel_id,
                    image_url=response.get('image_url', ''),
                    caption=response.get('response', ''),
                    business_unit=self.business_unit
                )
            else:
                # Envío de mensaje de texto simple
                await send_message(
                    platform='slack',
                    user_id=channel_id,
                    message=response.get('response', 'Sin contenido'),
                    business_unit=self.business_unit
                )
                
            # Manejo de metadata adicional si es necesario
            if 'metadata' in response and response['metadata'].get('requires_follow_up'):
                await self._schedule_follow_up(channel_id, response['metadata'])
                
            return True
                
        except Exception as e:
            logger.error(f"Error al enviar respuesta a Slack: {str(e)}", exc_info=True)
            # Intentar notificar al usuario del error
            try:
                await send_message(
                    platform='slack',
                    user_id=channel_id,
                    message="Lo siento, ha ocurrido un error al procesar tu solicitud. Por favor, inténtalo de nuevo más tarde.",
                    business_unit=self.business_unit
                )
            except Exception as inner_e:
                logger.error(f"Error al notificar al usuario sobre el error: {str(inner_e)}", exc_info=True)
            return False
    
    async def _schedule_follow_up(self, channel_id: str, metadata: Dict[str, Any]) -> None:
        """
        Programa un seguimiento basado en los metadatos.
        
        Args:
            channel_id (str): ID del canal o usuario en Slack
            metadata (Dict): Metadatos para el seguimiento
        """
        try:
            follow_up_time = metadata.get('follow_up_time', 3600)  # 1 hora por defecto
            follow_up_message = metadata.get('follow_up_message', '')
            
            if follow_up_message and follow_up_time > 0:
                await asyncio.sleep(follow_up_time)
                await send_message(
                    platform='slack',
                    user_id=channel_id,
                    message=follow_up_message,
                    business_unit=self.business_unit
                )
        except Exception as e:
            logger.error(f"Error al programar seguimiento en Slack: {str(e)}", exc_info=True)

@csrf_exempt
async def slack_webhook(request):
    """
    Endpoint webhook para recibir eventos de Slack.
    
    Args:
        request: Objeto de solicitud HTTP
        
    Returns:
        JsonResponse: Respuesta para Slack
    """
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        # Verificar el token de verificación de Slack
        if request.GET.get('type') == 'url_verification':
            return JsonResponse({"challenge": request.GET.get('challenge')})
            
        payload = json.loads(request.body.decode("utf-8"))
        event = payload.get("event", {})
        
        # Ignorar mensajes del propio bot para evitar bucles
        if event.get('bot_id'):
            return JsonResponse({"status": "success"})
            
        user_id = event.get("user")
        if not user_id:
            logger.error("No se pudo obtener el user_id del evento de Slack")
            return JsonResponse({"status": "error", "message": "user_id no proporcionado"}, status=400)
            
        # Obtener la configuración de Slack
        slack_api = await sync_to_async(SlackAPI.objects.filter(is_active=True).first)()
        if not slack_api:
            logger.error("No se encontró configuración de SlackAPI activa")
            return JsonResponse({"status": "error", "message": "Configuración no encontrada"}, status=404)
            
        business_unit = await sync_to_async(lambda: slack_api.business_unit)()
        
        # Procesar el mensaje con el manejador
        handler = SlackHandler(user_id=user_id, business_unit=business_unit)
        await handler.handle_message(payload)
        
        return JsonResponse({"status": "success"}, status=200)
        
    except json.JSONDecodeError:
        logger.error("Error al decodificar el cuerpo de la solicitud JSON")
        return JsonResponse({"status": "error", "message": "Cuerpo de solicitud JSON no válido"}, status=400)
    except Exception as e:
        logger.error(f"Error en slack_webhook: {str(e)}", exc_info=True)
        return JsonResponse({"status": "error", "message": "Error interno del servidor"}, status=500)

async def send_slack_message(channel_id: str, message: str, bot_token: str) -> bool:
    """Envía un mensaje de texto a un canal de Slack con rate limiting."""
    rate_limiter = RateLimiter()
    await rate_limiter.wait_for_limit('slack')
    """Envía un mensaje de texto a un canal de Slack."""
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": channel_id,
        "text": message
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        logger.info(f"✅ Mensaje enviado a {channel_id} en Slack: {message}")
        return True
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Error HTTP {e.response.status_code}: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje a Slack: {e}", exc_info=True)
        return False

async def send_slack_message_with_buttons(channel_id: str, message: str, buttons: List[Dict], bot_token: str) -> bool:
    """Envía un mensaje con botones a Slack con rate limiting."""
    rate_limiter = RateLimiter()
    await rate_limiter.wait_for_limit('slack')
    """Envía un mensaje con botones a Slack."""
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json"
    }
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": btn["text"]["text"] if isinstance(btn.get("text"), dict) else btn["text"]
                    },
                    "value": btn["value"]
                } for btn in buttons
            ]
        }
    ]
    payload = {
        "channel": channel_id,
        "blocks": blocks
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        logger.info(f"✅ Mensaje con botones enviado a {channel_id} en Slack")
        return True
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Error HTTP {e.response.status_code}: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje con botones a Slack: {e}", exc_info=True)
        return False

async def send_slack_document(channel_id: str, file_url: str, caption: str, bot_token: str) -> bool:
    """Envía un documento a Slack con rate limiting."""
    rate_limiter = RateLimiter()
    await rate_limiter.wait_for_limit('slack')
    try:
        url = "https://slack.com/api/files.upload"
        headers = {"Authorization": f"Bearer {bot_token}"}
        payload = {
            "channels": channel_id,
            "content": caption,
            "file": file_url,
            "filename": "document"
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, data=payload)
            response.raise_for_status()
        logger.info(f"[send_slack_document] Documento enviado a {channel_id}")
        return True
    except Exception as e:
        logger.error(f"[send_slack_document] Error: {e}")
        return False

async def fetch_slack_user_data(user_id: str, api_instance: SlackAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    try:
        if not isinstance(api_instance, SlackAPI) or not hasattr(api_instance, 'bot_token') or not api_instance.bot_token:
            logger.error(f"api_instance no es válido, recibido: {type(api_instance)}")
            return {}
        url = "https://slack.com/api/users.info"
        headers = {"Authorization": f"Bearer {api_instance.bot_token}"}
        params = {"user": user_id}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json().get("user", {})
                nombre = data.get("real_name", "").split(" ")[0]
                apellido = " ".join(data.get("real_name", "").split(" ")[1:]) if len(data.get("real_name", "").split(" ")) > 1 else ""
                return {
                    'nombre': nombre,
                    'apellido_paterno': apellido,
                    'metadata': {
                        'username': data.get("name", ""),
                        'email': data.get("profile", {}).get("email", "")
                    }
                }
            else:
                logger.error(f"Error fetching Slack user data: {response.text}")
                return {}
    except Exception as e:
        logger.error(f"Exception in fetch_slack_user_data: {e}", exc_info=True)