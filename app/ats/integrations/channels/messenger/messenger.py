# /home/pablo/app/com/chatbot/integrations/messenger.py
#
# Módulo para manejar la integración con Facebook Messenger.
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
from app.models import Person, BusinessUnit, MessengerAPI, MetaAPI
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

async def fetch_messenger_user_data(user_id: str, api_instance: MessengerAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Obtiene datos del usuario desde la API de Messenger."""
    try:
        if not isinstance(api_instance, MessengerAPI) or not api_instance.page_access_token:
            logger.error(f"api_instance no es válido: {type(api_instance)}")
            return {}

        url = f"https://graph.facebook.com/v13.0/{user_id}"
        params = {
            "fields": "first_name,last_name,email,locale",
            "access_token": api_instance.page_access_token
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return {
                    'nombre': data.get('first_name', ''),
                    'apellido_paterno': data.get('last_name', ''),
                    'email': data.get('email', ''),
                    'preferred_language': data.get('locale', 'es_MX').replace('_', '_'),
                    'metadata': {}
                }
            else:
                logger.error(f"Error fetching Messenger user data: {response.text}")
                return {}
    except Exception as e:
        logger.error(f"Error en fetch_messenger_user_data: {str(e)}")
        return {}

class MessengerHandler:
    """Manejador de interacciones de Messenger para el chatbot."""

    def __init__(self, user_id: str, page_id: str, business_unit: BusinessUnit):
        self.user_id = user_id
        self.page_id = page_id
        self.business_unit = business_unit
        self.user: Optional[Person] = None
        self.chat_manager: Optional[ChatStateManager] = None
        self.intent_processor: Optional[IntentProcessor] = None
        self.messenger_api: Optional[MessengerAPI] = None
        self.user_data: Dict[str, Any] = {}

    async def initialize(self) -> bool:
        """Inicializa el manejador de Messenger."""
        try:
            # Obtener configuración de MessengerAPI y MetaAPI
            cache_key_messenger = f"messenger_api:{self.page_id}"
            cache_key_meta = f"meta_api:{self.business_unit.id}"
            
            self.messenger_api = cache.get(cache_key_messenger)
            if not self.messenger_api:
                self.messenger_api = await MessengerAPI.objects.filter(
                    page_id=self.page_id, 
                    is_active=True
                ).afirst()
                if self.messenger_api:
                    cache.set(cache_key_messenger, self.messenger_api, CACHE_TIMEOUT)
                    
            meta_api = cache.get(cache_key_meta)
            if not meta_api:
                meta_api = await MetaAPI.objects.filter(
                    business_unit=self.business_unit,
                    is_active=True
                ).afirst()
                if meta_api:
                    cache.set(cache_key_meta, meta_api, CACHE_TIMEOUT)
                    
            if not self.messenger_api or not meta_api:
                raise ValueError(f"No se encontró configuración de MessengerAPI o MetaAPI para page_id: {self.page_id}")

            # Obtener o crear usuario y extraer datos
            self.user = await self._get_or_create_user()
            self.user_data = await fetch_messenger_user_data(self.user_id, self.messenger_api)
            await self._update_user_profile()

            # Inicializar manejador de estados y procesador de intents
            self.chat_manager = ChatStateManager(self.user, self.business_unit)
            await self.chat_manager.initialize()
            self.intent_processor = IntentProcessor(self.user, self.business_unit)
            return True
        except Exception as e:
            logger.error(f"Error inicializando MessengerHandler: {str(e)}")
            raise

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un mensaje de Messenger y genera una respuesta."""
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
            if response.get('type') == 'text' and response.get('options'):
                await self._send_response(self.user_id, response)
            elif response.get('type') == 'image':
                await send_image(
                    platform='messenger',
                    user_id=self.user_id,
                    image_url=response.get('image_url', ''),
                    caption=response.get('response', ''),
                    business_unit=self.business_unit
                )
            else:
                await self._send_response(self.user_id, response)

            # Actualizar estado del chat
            await self.chat_manager.update_state('IDLE')
            return response
        except Exception as e:
            logger.error(f"Error procesando mensaje en Messenger: {str(e)}")
            return {'response': "Lo siento, hubo un error procesando tu mensaje."}

    async def _get_or_create_user(self) -> Person:
        """Obtiene o crea un usuario en la base de datos."""
        user, created = await Person.objects.aget_or_create(
            messenger_user_id=self.user_id,
            defaults={'business_unit': self.business_unit, 'nombre': 'Nuevo Usuario'}
        )
        return user

    async def _update_user_profile(self) -> None:
        """Actualiza el perfil del usuario con datos extraídos."""
        if self.user_data.get('nombre') and not self.user.nombre:
            self.user.nombre = self.user_data['nombre']
        if self.user_data.get('apellido_paterno') and not self.user.apellido_paterno:
            self.user.apellido_paterno = self.user_data['apellido_paterno']
        if self.user_data.get('email') and not self.user.email:
            self.user.email = self.user_data['email']
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
        Envía la respuesta al usuario en Messenger.
        
        Args:
            user_id (str): ID del usuario en Messenger
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
                    platform='messenger',
                    user_id=user_id,
                    message=response['response'],
                    options=response['options'],
                    business_unit=self.business_unit
                )
            else:
                # Envío de mensaje de texto simple
                await send_message(
                    platform='messenger',
                    user_id=user_id,
                    message=response.get('response', 'Sin contenido'),
                    business_unit=self.business_unit
                )
                
            # Manejo de metadata adicional si es necesario
            if 'metadata' in response and response['metadata'].get('requires_follow_up'):
                await self._schedule_follow_up(user_id, response['metadata'])
                
            return True
                
        except Exception as e:
            logger.error(f"Error al enviar respuesta a Messenger: {str(e)}", exc_info=True)
            # Intentar notificar al usuario del error
            try:
                await send_message(
                    platform='messenger',
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
            user_id (str): ID del usuario en Messenger
            metadata (Dict): Metadatos para el seguimiento
        """
        try:
            follow_up_time = metadata.get('follow_up_time', 3600)  # 1 hora por defecto
            follow_up_message = metadata.get('follow_up_message', '')
            
            if follow_up_message and follow_up_time > 0:
                await asyncio.sleep(follow_up_time)
                await send_message(
                    platform='messenger',
                    user_id=user_id,
                    message=follow_up_message,
                    business_unit=self.business_unit
                )
        except Exception as e:
            logger.error(f"Error al programar seguimiento en Messenger: {str(e)}", exc_info=True)

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
    async def send_messenger_buttons(self, user_id: str, message: str, buttons: List[Dict]) -> bool:
        """Envía un mensaje con quick replies."""
        try:
            url = "https://graph.facebook.com/v22.0/me/messages"
            headers = {
                "Authorization": f"Bearer {self.messenger_api.page_access_token}",
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
            logger.error(f"❌ Error enviando quick replies a Messenger: {str(e)}")
            return False

@csrf_exempt
async def messenger_webhook(request):
    """Webhook para procesar mensajes entrantes de Messenger."""
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body.decode("utf-8"))
        entry = payload.get("entry", [{}])[0]
        messaging = entry.get("messaging", [{}])[0]
        user_id = messaging.get("sender", {}).get("id")
        message = messaging.get("message", {})
        page_id = await sync_to_async(lambda: MessengerAPI.objects.filter(
            is_active=True
        ).first().page_id)()
        business_unit = await sync_to_async(lambda: MessengerAPI.objects.filter(
            is_active=True
        ).first().business_unit)()

        handler = MessengerHandler(user_id, page_id, business_unit)
        await handler.initialize()
        response = await handler.handle_message(message)
        return JsonResponse({"status": "success", "response": response}, status=200)
    except Exception as e:
        logger.error(f"Error en messenger_webhook: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

async def verify_messenger_token(request, page_id: str):
    """Verifica el token de Messenger durante la configuración del webhook."""
    try:
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        messenger_api = await MessengerAPI.objects.filter(page_id=page_id, is_active=True).afirst()
        if not messenger_api:
            return HttpResponse('Configuración no encontrada', status=404)
        if verify_token == messenger_api.meta_api.verify_token:
            logger.info(f"Token de verificación correcto para page_id: {page_id}")
            return HttpResponse(challenge)
        return HttpResponse('Token de verificación inválido', status=403)
    except Exception as e:
        logger.error(f"Error verificando token de Messenger: {str(e)}")
        return HttpResponse('Error interno', status=500)