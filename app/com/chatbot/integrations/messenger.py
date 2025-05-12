# /home/pablo/app/com/chatbot/integrations/messenger.py
#
# Módulo para manejar la integración con Facebook Messenger.
# Procesa mensajes entrantes, envía respuestas, y gestiona interacciones como botones.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

import json
import logging
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from asgiref.sync import sync_to_async
from tenacity import retry, stop_after_attempt, wait_exponential
from app.models import Person, BusinessUnit, MessengerAPI
from app.com.chatbot.chat_state_manager import ChatStateManager
from app.com.chatbot.intents_handler import IntentProcessor

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
            # Obtener configuración de MessengerAPI
            cache_key = f"messenger_api:{self.page_id}"
            self.messenger_api = cache.get(cache_key)
            if not self.messenger_api:
                self.messenger_api = await MessengerAPI.objects.filter(
                    page_id=self.page_id, is_active=True
                ).afirst()
                if self.messenger_api:
                    cache.set(cache_key, self.messenger_api, CACHE_TIMEOUT)
            if not self.messenger_api:
                raise ValueError(f"No se encontró MessengerAPI para page_id: {self.page_id}")

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
            if intent.get('smart_options'):
                await self.send_messenger_buttons(
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
        """Genera una respuesta basada en el intent detectado."""
        return intent

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
    async def _send_response(self, user_id: str, response: Dict[str, Any]) -> bool:
        """Envía la respuesta al usuario en Messenger."""
        try:
            url = "https://graph.facebook.com/v22.0/me/messages"
            headers = {
                "Authorization": f"Bearer {self.messenger_api.page_access_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "recipient": {"id": user_id},
                "message": {"text": response.get('response', '')}
            }
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
            logger.info(f"✅ Mensaje enviado a {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje a Messenger: {str(e)}")
            return False

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