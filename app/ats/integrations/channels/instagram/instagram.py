# /home/pablo/app/com/chatbot/integrations/instagram.py
#
# Módulo para manejar la integración con Instagram Messaging API.
# Procesa mensajes entrantes, envía respuestas, y gestiona interacciones como botones.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

import json
import logging
import httpx
import asyncio
from typing import Optional, Dict, Any, List, Callable
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from asgiref.sync import sync_to_async
from tenacity import retry, stop_after_attempt, wait_exponential
from app.models import Person, BusinessUnit, InstagramAPI
from app.ats.chatbot.components.chat_state_manager import ChatStateManager
from app.ats.chatbot.components.rate_limiter import RateLimiter
from app.ats.integrations.services.message import (
    send_message, 
    send_options, 
    send_smart_options,
    send_image
)

logger = logging.getLogger('chatbot')

# Configuraciones globales
REQUEST_TIMEOUT = 10.0
MAX_RETRIES = 3
CACHE_TIMEOUT = 600

async def fetch_instagram_user_data(user_id: str, api_instance: InstagramAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Obtiene datos del usuario desde la API de Instagram."""
    try:
        if not isinstance(api_instance, InstagramAPI) or not api_instance.access_token:
            logger.error(f"api_instance no es válido: {type(api_instance)}")
            return {}

        url = f"https://graph.instagram.com/{user_id}"
        params = {
            "fields": "username,full_name",
            "access_token": api_instance.access_token
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                nombre = data.get('full_name', '').split(' ')[0]
                apellido = ' '.join(data.get('full_name', '').split(' ')[1:]) if len(data.get('full_name', '').split(' ')) > 1 else ''
                return {
                    'nombre': nombre,
                    'apellido_paterno': apellido,
                    'metadata': {'username': data.get('username', '')},
                    'preferred_language': 'es_MX'
                }
            else:
                logger.error(f"Error fetching Instagram user data: {response.text}")
                return {}
    except Exception as e:
        logger.error(f"Error en fetch_instagram_user_data: {str(e)}")
        return {}

class InstagramHandler:
    """Manejador de interacciones de Instagram para el chatbot."""

    def __init__(self, user_id: str, phone_id: str, business_unit: BusinessUnit):
        self.user_id = user_id
        self.phone_id = phone_id
        self.business_unit = business_unit
        self.user: Optional[Person] = None
        self.chat_manager: Optional[ChatStateManager] = None
        self.intent_processor: Optional[IntentProcessor] = None
        self.instagram_api: Optional[InstagramAPI] = None
        self.user_data: Dict[str, Any] = {}

    async def initialize(self) -> bool:
        """Inicializa el manejador de Instagram."""
        try:
            # Obtener configuración de InstagramAPI
            cache_key = f"instagram_api:{self.phone_id}"
            self.instagram_api = cache.get(cache_key)
            if not self.instagram_api:
                self.instagram_api = await InstagramAPI.objects.filter(
                    phoneID=self.phone_id, is_active=True
                ).afirst()
                if self.instagram_api:
                    cache.set(cache_key, self.instagram_api, CACHE_TIMEOUT)
            if not self.instagram_api:
                raise ValueError(f"No se encontró InstagramAPI para phoneID: {self.phone_id}")

            # Obtener o crear usuario y extraer datos
            self.user = await self._get_or_create_user()
            self.user_data = await fetch_instagram_user_data(self.user_id, self.instagram_api)
            await self._update_user_profile()

            # Inicializar manejador de estados y procesador de intents
            self.chat_manager = ChatStateManager(self.user, self.business_unit)
            await self.chat_manager.initialize()
            self.intent_processor = IntentProcessor(self.user, self.business_unit)
            return True
        except Exception as e:
            logger.error(f"Error inicializando InstagramHandler: {str(e)}")
            raise

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un mensaje de Instagram y genera una respuesta."""
        try:
            # Extraer texto o contenido de archivo
            text = message.get('text', '').strip()
            if await self._is_spam_message(text):
                return {'response': "Por favor, no envíes mensajes repetidos o spam."}

            # Actualizar estado del chat
            await self.chat_manager.update_state('PROCESSING')

            # Procesar intent
            intent = await self.intent_processor.process(text)

            # Generar y enviar respuesta
            response = await self._generate_response(intent)
            if intent.get('smart_options'):
                await self.send_instagram_buttons(
                    self.user_id,
                    response.get('response', ''),
                    intent['smart_options']
                )
            else:
                await self._send_response(self.user_id, response)

            # Actualizar estado del chat
            await self.chat_manager.update_state('IDLE')
            return response
        except Exception as e:
            logger.error(f"Error procesando mensaje en Instagram: {str(e)}")
            return {'response': "Lo siento, hubo un error procesando tu mensaje."}

    async def _get_or_create_user(self) -> Person:
        """Obtiene o crea un usuario en la base de datos."""
        user, created = await Person.objects.aget_or_create(
            instagram_user_id=self.user_id,
            defaults={'business_unit': self.business_unit, 'nombre': 'Nuevo Usuario'}
        )
        return user

    async def _update_user_profile(self) -> None:
        """Actualiza el perfil del usuario con datos extraídos."""
        if self.user_data.get('nombre') and not self.user.nombre:
            self.user.nombre = self.user_data['nombre']
        if self.user_data.get('apellido_paterno') and not self.user.apellido_paterno:
            self.user.apellido_paterno = self.user_data['apellido_paterno']
        if self.user_data.get('metadata'):
            self.user.metadata.update(self.user_data['metadata'])
        if self.user_data.get('preferred_language'):
            self.user.metadata['preferred_language'] = self.user_data['preferred_language']
        await self.user.asave()

    async def _is_spam_message(self, message: str) -> bool:
        """Verifica si un mensaje es spam (implementación pendiente)."""
        return False

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

    async def _send_response(self, user_id: str, response: Dict[str, Any]) -> bool:
        """
        Envía la respuesta al usuario en Instagram.
        
        Args:
            user_id (str): ID del usuario en Instagram
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
                    platform='instagram',
                    user_id=user_id,
                    message=response['response'],
                    options=response['options'],
                    business_unit=self.business_unit
                )
            elif response.get('type') == 'image':
                # Usar el message_sender para enviar imágenes
                await send_image(
                    platform='instagram',
                    user_id=user_id,
                    image_url=response.get('image_url', ''),
                    caption=response.get('response', ''),
                    business_unit=self.business_unit
                )
            else:
                # Envío de mensaje de texto simple
                await send_message(
                    platform='instagram',
                    user_id=user_id,
                    message=response.get('response', 'Sin contenido'),
                    business_unit=self.business_unit
                )
                
            # Manejo de metadata adicional si es necesario
            if 'metadata' in response and response['metadata'].get('requires_follow_up'):
                await self._schedule_follow_up(user_id, response['metadata'])
                
            return True
                
        except Exception as e:
            logger.error(f"Error al enviar respuesta a Instagram: {str(e)}", exc_info=True)
            # Intentar notificar al usuario del error
            try:
                await send_message(
                    platform='instagram',
                    user_id=user_id,
                    message="Lo siento, ha ocurrido un error al procesar tu solicitud. Por favor, inténtalo de nuevo más tarde.",
                    business_unit=self.business_unit
                )
            except Exception as inner_e:
                logger.error(f"Error al notificar al usuario sobre el error: {str(inner_e)}", exc_info=True)
            return False
            
    async def _schedule_follow_up(self, user_id: str, metadata: Dict[str, Any]) -> None:
        """
        Programa un seguimiento basado en los metadatos.
        
        Args:
            user_id (str): ID del usuario en Instagram
            metadata (Dict): Metadatos para el seguimiento
        """
        try:
            follow_up_time = metadata.get('follow_up_time', 3600)  # 1 hora por defecto
            follow_up_message = metadata.get('follow_up_message', '')
            
            if follow_up_message and follow_up_time > 0:
                await asyncio.sleep(follow_up_time)
                await send_message(
                    platform='instagram',
                    user_id=user_id,
                    message=follow_up_message,
                    business_unit=self.business_unit
                )
        except Exception as e:
            logger.error(f"Error al programar seguimiento en Instagram: {str(e)}", exc_info=True)

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
    async def send_instagram_buttons(self, user_id: str, message: str, buttons: List[Dict]) -> bool:
        """Envía un mensaje con quick replies."""
        try:
            url = "https://graph.facebook.com/v22.0/me/messages"
            headers = {
                "Authorization": f"Bearer {self.instagram_api.access_token}",
                "Content-Type": "application/json"
            }
            quick_replies = [
                {"content_type": "text", "title": btn["title"], "payload": btn["payload"] or "no_payload"}
                for btn in buttons[:10]
            ]
            payload = {
                "recipient": {"id": user_id},
                "message": {
                    "text": message,
                    "quick_replies": quick_replies
                }
            }
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
            logger.info(f"✅ Quick replies enviados a {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error enviando quick replies a Instagram: {str(e)}")
            return False

@csrf_exempt
async def instagram_webhook(request):
    """Webhook para procesar mensajes entrantes de Instagram."""
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body.decode("utf-8"))
        entry = payload.get("entry", [{}])[0]
        messaging = entry.get("messaging", [{}])[0]
        user_id = messaging.get("sender", {}).get("id")
        message = messaging.get("message", {})
        phone_id = await sync_to_async(lambda: InstagramAPI.objects.filter(
            is_active=True
        ).first().phoneID)()
        business_unit = await sync_to_async(lambda: InstagramAPI.objects.filter(
            is_active=True
        ).first().business_unit)()

        handler = InstagramHandler(user_id, phone_id, business_unit)
        await handler.initialize()
        response = await handler.handle_message(message)
        return JsonResponse({"status": "success", "response": response}, status=200)
    except Exception as e:
        logger.error(f"Error en instagram_webhook: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

async def verify_instagram_token(request):
    """Verifica el token de Instagram durante la configuración del webhook."""
    try:
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        phone_id = request.GET.get('phoneID')
        instagram_api = await InstagramAPI.objects.filter(phoneID=phone_id, is_active=True).afirst()
        if not instagram_api:
            return HttpResponse('Configuración no encontrada', status=404)
        meta_api = await MetaAPI.objects.filter(business_unit=instagram_api.business_unit).afirst()
        if verify_token == meta_api.verify_token:
            logger.info(f"Token de verificación correcto para phoneID: {phone_id}")
            return HttpResponse(challenge)
        return HttpResponse('Token de verificación inválido', status=403)
    except Exception as e:
        logger.error(f"Error verificando token de Instagram: {str(e)}")
        return HttpResponse('Error interno', status=500)