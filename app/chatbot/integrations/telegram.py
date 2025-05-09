# /home/pablo/app/chatbot/integrations/telegram.py
#
# Módulo para manejar la integración con Telegram Bot API.
# Procesa mensajes entrantes, envía respuestas, y gestiona interacciones como botones.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

import json
import logging
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.cache import cache
from asgiref.sync import sync_to_async
from tenacity import retry, stop_after_attempt, wait_exponential
from app.models import Person, BusinessUnit, TelegramAPI
from app.chatbot.chat_state_manager import ChatStateManager
from app.chatbot.intents_handler import IntentProcessor

logger = logging.getLogger('chatbot')

# Configuraciones globales
REQUEST_TIMEOUT = 10.0
MAX_RETRIES = 3
CACHE_TIMEOUT = 600

async def fetch_telegram_user_data(user_id: str, api_instance: TelegramAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Obtiene datos del usuario desde la API de Telegram."""
    try:
        if not isinstance(api_instance, TelegramAPI) or not api_instance.api_key:
            logger.error(f"api_instance no es válido: {type(api_instance)}")
            return {}

        url = f"https://api.telegram.org/bot{api_instance.api_key}/getChat"
        params = {"chat_id": user_id}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json().get('result', {})
                return {
                    'nombre': data.get('first_name', ''),
                    'apellido_paterno': data.get('last_name', ''),
                    'metadata': {
                        'username': data.get('username', ''),
                        'bio': data.get('bio', '')
                    },
                    'preferred_language': data.get('language_code', 'es')
                }
            else:
                logger.error(f"Error fetching Telegram user data: {response.text}")
                return {}
    except Exception as e:
        logger.error(f"Error en fetch_telegram_user_data: {str(e)}")
        return {}

class TelegramHandler:
    """Manejador de interacciones de Telegram para el chatbot."""

    def __init__(self, user_id: str, bot_name: str, business_unit: BusinessUnit):
        self.user_id = user_id
        self.bot_name = bot_name
        self.business_unit = business_unit
        self.user: Optional[Person] = None
        self.chat_manager: Optional[ChatStateManager] = None
        self.intent_processor: Optional[IntentProcessor] = None
        self.telegram_api: Optional[TelegramAPI] = None
        self.user_data: Dict[str, Any] = {}

    async def initialize(self) -> bool:
        """Inicializa el manejador de Telegram."""
        try:
            # Obtener configuración de TelegramAPI
            cache_key = f"telegram_api:{self.bot_name}"
            self.telegram_api = cache.get(cache_key)
            if not self.telegram_api:
                self.telegram_api = await TelegramAPI.objects.filter(
                    bot_name=self.bot_name, is_active=True
                ).afirst()
                if self.telegram_api:
                    cache.set(cache_key, self.telegram_api, CACHE_TIMEOUT)
            if not self.telegram_api:
                raise ValueError(f"No se encontró TelegramAPI para bot_name: {self.bot_name}")

            # Obtener o crear usuario y extraer datos
            self.user = await self._get_or_create_user()
            self.user_data = await fetch_telegram_user_data(self.user_id, self.telegram_api)
            await self._update_user_profile()

            # Inicializar manejador de estados y procesador de intents
            self.chat_manager = ChatStateManager(self.user, self.business_unit)
            await self.chat_manager.initialize()
            self.intent_processor = IntentProcessor(self.user, self.business_unit)
            return True
        except Exception as e:
            logger.error(f"Error inicializando TelegramHandler: {str(e)}")
            raise

    async def handle_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un mensaje de Telegram y genera una respuesta."""
        try:
            # Extraer chat_id y texto
            chat_id, text = await self._extract_message_content(payload)
            if await self._is_spam_message(text):
                return {'response': "Por favor, no envíes mensajes repetidos o spam."}

            # Actualizar estado del chat
            await self.chat_manager.update_state('PROCESSING')

            # Procesar intent
            intent = await self.intent_processor.process(text)

            # Generar y enviar respuesta
            response = await self._generate_response(intent)
            if intent.get('smart_options'):
                await self.send_telegram_buttons(
                    chat_id,
                    response.get('response', ''),
                    intent['smart_options']
                )
            else:
                await self._send_response(chat_id, response)

            # Actualizar estado del chat
            await self.chat_manager.update_state('IDLE')
            return response
        except Exception as e:
            logger.error(f"Error procesando mensaje en Telegram: {str(e)}")
            return {'response': "Lo siento, hubo un error procesando tu mensaje."}

    async def _get_or_create_user(self) -> Person:
        """Obtiene o crea un usuario en la base de datos."""
        user, created = await Person.objects.aget_or_create(
            telegram_user_id=self.user_id,
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

    async def _extract_message_content(self, payload: Dict[str, Any]) -> tuple[int, str]:
        """Extrae el chat_id y el contenido del mensaje."""
        if "callback_query" in payload:
            callback_query = payload["callback_query"]
            chat_id = int(callback_query["message"]["chat"]["id"])
            text = callback_query.get("data", "").strip()
            callback_query_id = callback_query.get("id", "")
            if callback_query_id:
                await self._confirm_callback(callback_query_id)
        else:
            message = payload.get("message", {})
            chat_id = int(message.get("chat", {}).get("id"))
            text = message.get("text", "").strip()
        return chat_id, text

    async def _confirm_callback(self, callback_query_id: str) -> bool:
        """Confirma la respuesta de un botón de Telegram."""
        url = f"https://api.telegram.org/bot{self.telegram_api.api_key}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"❌ Error confirmando callback: {str(e)}")
            return False

    async def _is_spam_message(self, message: str) -> bool:
        """Verifica si un mensaje es spam (implementación pendiente)."""
        return False

    async def _generate_response(self, intent: Dict) -> Dict[str, Any]:
        """Genera una respuesta basada en el intent detectado."""
        return intent

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
    async def _send_response(self, chat_id: int, response: Dict[str, Any]) -> bool:
        """Envía la respuesta al usuario en Telegram."""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_api.api_key}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": response.get('response', ''),
                "parse_mode": "HTML"
            }
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
            logger.info(f"✅ Mensaje enviado a {chat_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje a Telegram: {str(e)}")
            return False

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
    async def send_telegram_buttons(self, chat_id: int, message: str, buttons: List[Dict]) -> bool:
        """Envía un mensaje con inline keyboard."""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_api.api_key}/sendMessage"
            inline_keyboard = [
                [{"text": btn["title"], "callback_data": btn["payload"] or "no_data"}]
                for btn in buttons
            ]
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": inline_keyboard}
            }
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
            logger.info(f"✅ Inline keyboard enviado a {chat_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error enviando inline keyboard a Telegram: {str(e)}")
            return False

@csrf_exempt
async def telegram_webhook(request, bot_name: str):
    """Webhook para procesar mensajes entrantes de Telegram."""
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body.decode("utf-8"))
        user_id = str(payload.get("message", {}).get("chat", {}).get("id", payload.get("callback_query", {}).get("from", {}).get("id")))
        business_unit = await sync_to_async(lambda: TelegramAPI.objects.filter(
            bot_name=bot_name, is_active=True
        ).first().business_unit)()

        handler = TelegramHandler(user_id, bot_name, business_unit)
        await handler.initialize()
        response = await handler.handle_message(payload)
        return JsonResponse({"status": "success", "response": response}, status=200)
    except Exception as e:
        logger.error(f"Error en telegram_webhook: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)