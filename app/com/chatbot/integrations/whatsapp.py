# /home/pablo/app/com/chatbot/integrations/whatsapp.py
#
# Módulo para manejar la integración con WhatsApp Business API.
# Procesa mensajes entrantes, envía respuestas, y gestiona interacciones como botones y listas.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

import json
import logging
import asyncio
import httpx
from typing import Optional, Dict, Any, List
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from asgiref.sync import sync_to_async
from tenacity import retry, stop_after_attempt, wait_exponential
from app.models import Person, BusinessUnit, WhatsAppAPI, ChatState
from app.com.chatbot.import_config import (
    get_chat_state_manager,
    get_intent_processor
)
from app.com.chatbot.integrations.whatsapp.rate_limiter import RateLimiter

logger = logging.getLogger('chatbot')

# Configuraciones globales
REQUEST_TIMEOUT = 10.0
MAX_RETRIES = 3
CACHE_TIMEOUT = 600  # 10 minutos
whatsapp_semaphore = asyncio.Semaphore(10)

class WhatsAppHandler:
    """Handler for WhatsApp channel interactions with rate limiting and error handling."""
    def __init__(self, user_id: str, phone_number_id: str, business_unit: BusinessUnit):
        self.user_id = user_id
        self.phone_number_id = phone_number_id
        self.business_unit = business_unit
        self.user: Optional[Person] = None
        self.chat_manager = get_chat_state_manager()
        self.intent_processor = get_intent_processor()
        self.whatsapp_api: Optional[WhatsAppAPI] = None
        self.user_data: Dict[str, Any] = {}
        self.api_base_url = settings.WHATSAPP_API_URL
        self.api_token = settings.WHATSAPP_API_TOKEN
        self.rate_limiter = RateLimiter(requests_per_minute=settings.WHATSAPP_RATE_LIMIT)
        self.session = None
        logger.info("WhatsAppHandler initialized")

    async def initialize(self):
        """Initialize the aiohttp session for WhatsApp API calls."""
        if self.session is None:
            self.session = aiohttp.ClientSession(headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            })
            logger.info("WhatsAppHandler session initialized")
        return self.session

    async def fetch_whatsapp_user_data(self, user_id: str, api_instance: WhatsAppAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Obtiene datos del usuario desde el payload de WhatsApp."""
        try:
            if not isinstance(api_instance, WhatsAppAPI) or not api_instance.api_token:
                logger.error(f"api_instance no es válido: {type(api_instance)}")
                return {'nombre': '', 'apellido_paterno': '', 'metadata': {}, 'preferred_language': 'es_MX'}

            if not payload or 'entry' not in payload:
                logger.warning(f"Payload inválido para user_id: {user_id}")
                return {'nombre': '', 'apellido_paterno': '', 'metadata': {}, 'preferred_language': 'es_MX'}

            contacts = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("contacts", [])
            if not contacts:
                return {'nombre': '', 'apellido_paterno': '', 'metadata': {}, 'preferred_language': 'es_MX'}

            profile_name = contacts[0].get("profile", {}).get("name", "")
            nombre = profile_name.split(" ")[0] if profile_name else ""
            apellido = " ".join(profile_name.split(" ")[1:]) if len(profile_name.split(" ")) > 1 else ""
            return {
                'nombre': nombre,
                'apellido_paterno': apellido,
                'metadata': {'wa_id': user_id},
                'preferred_language': 'es_MX'
            }
        except Exception as e:
            logger.error(f"Error en fetch_whatsapp_user_data: {str(e)}")
            return {'nombre': '', 'apellido_paterno': '', 'metadata': {}, 'preferred_language': 'es_MX'}

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un mensaje de WhatsApp y genera una respuesta."""
        try:
            async with whatsapp_semaphore:
                # Extraer texto o contenido interactivo
                text = await self._extract_message_content(message)
                if await self._is_spam_message(text):
                    return {'response': "Por favor, no envíes mensajes repetidos o spam."}

                # Actualizar estado del chat
                await self.chat_manager.update_state('PROCESSING')

                # Procesar intent
                intent = await self.intent_processor.process(text)

                # Generar y enviar respuesta
                response = await self._generate_response(intent)
                if intent.get('smart_options'):
                    await self.send_whatsapp_buttons(
                        message.get('from', self.user_id),
                        response.get('response', ''),
                        intent['smart_options']
                    )
                elif intent.get('template_messages') and 'list' in intent['template_messages'][0].get('template_type', '').lower():
                    await self.send_whatsapp_list(
                        message.get('from', self.user_id),
                        response.get('response', ''),
                        intent['template_messages'][0].get('options', [])
                    )
                else:
                    await self._send_response(message.get('from', self.user_id), response)

                # Actualizar estado del chat
                await self.chat_manager.update_state('IDLE')
                return response
        except Exception as e:
            logger.error(f"Error procesando mensaje en WhatsApp: {str(e)}")
            return {'response': "Lo siento, hubo un error procesando tu mensaje."}

    async def _get_or_create_user(self) -> Person:
        """Obtiene o crea un usuario en la base de datos."""
        user, created = await Person.objects.aget_or_create(
            phone=self.user_id,
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

    async def _extract_message_content(self, message: Dict[str, Any]) -> str:
        """Extrae el contenido del mensaje (texto o interactivo)."""
        text = message.get('text', {}).get('body', '').strip()
        if message.get('type') == 'interactive':
            interactive = message.get('interactive', {})
            if interactive.get('type') == 'button_reply':
                text = interactive.get('button_reply', {}).get('id', '')
            elif interactive.get('type') == 'list_reply':
                text = interactive.get('list_reply', {}).get('id', '')
        return text

    async def _is_spam_message(self, message: str) -> bool:
        """Verifica si un mensaje es spam (implementación pendiente)."""
        return False

    async def _generate_response(self, intent: Dict) -> Dict[str, Any]:
        """Genera una respuesta basada en el intent detectado."""
        return intent  # IntentProcessor ya devuelve response, smart_options, etc.

    async def _send_response(self, recipient_id: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message via WhatsApp with rate limiting."""
        try:
            await self.rate_limiter.acquire()
            await self.initialize()
            payload = {
                "to": recipient_id,
                "type": "text",
                "text": {
                    "body": response.get('response', '')
                }
            }
            async with self.session.post(f"{self.api_base_url}/messages", json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info(f"WhatsApp message sent to {recipient_id}")
                    return result
                else:
                    error_text = await resp.text()
                    logger.error(f"Failed to send WhatsApp message to {recipient_id}: {resp.status} - {error_text}")
                    return {"error": f"HTTP {resp.status}", "details": error_text}
        except Exception as e:
            logger.error(f"Error sending WhatsApp message to {recipient_id}: {str(e)}", exc_info=True)
            return {"error": str(e)}
        finally:
            await self.rate_limiter.release()

    async def send_whatsapp_buttons(self, user_id: str, message: str, buttons: List[Dict]) -> bool:
        """Envía un mensaje con botones interactivos (máximo 3)."""
        try:
            await self.rate_limiter.acquire()
            await self.initialize()
            formatted_buttons = [
                {"type": "reply", "reply": {"id": btn["payload"], "title": btn["title"][:20]}}
                for btn in buttons[:3]
            ]
            payload = {
                "to": user_id,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": message},
                    "action": {"buttons": formatted_buttons}
                }
            }
            async with self.session.post(f"{self.api_base_url}/messages", json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info(f"WhatsApp buttons sent to {user_id}")
                    return True
                else:
                    error_text = await resp.text()
                    logger.error(f"Failed to send WhatsApp buttons to {user_id}: {resp.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp buttons to {user_id}: {str(e)}", exc_info=True)
            return False
        finally:
            await self.rate_limiter.release()

    async def send_whatsapp_list(self, user_id: str, message: str, options: List[Dict]) -> bool:
        """Envía una lista interactiva (hasta 10 opciones)."""
        try:
            await self.rate_limiter.acquire()
            await self.initialize()
            sections = [{
                "title": "Opciones",
                "rows": [
                    {"id": opt["payload"], "title": opt["title"][:24]}
                    for opt in options[:10]
                ]
            }]
            payload = {
                "to": user_id,
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "header": {"type": "text", "text": "Menú Principal"},
                    "body": {"text": message},
                    "footer": {"text": "Selecciona una opción"},
                    "action": {
                        "button": "Seleccionar",
                        "sections": sections
                    }
                }
            }
            async with self.session.post(f"{self.api_base_url}/messages", json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info(f"WhatsApp list sent to {user_id}")
                    return True
                else:
                    error_text = await resp.text()
                    logger.error(f"Failed to send WhatsApp list to {user_id}: {resp.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending WhatsApp list to {user_id}: {str(e)}", exc_info=True)
            return False
        finally:
            await self.rate_limiter.release()

@csrf_exempt
async def whatsapp_webhook(request):
    """Webhook para procesar mensajes entrantes de WhatsApp."""
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body.decode("utf-8"))
        entry = payload.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        if not messages:
            return JsonResponse({"status": "success", "message": "No messages to process"}, status=200)

        message = messages[0]
        user_id = message.get('from')
        phone_number_id = value.get('metadata', {}).get('phone_number_id')
        business_unit = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
            phoneID=phone_number_id, is_active=True
        ).first().business_unit)()

        handler = WhatsAppHandler(user_id, phone_number_id, business_unit)
        await handler.initialize()
        response = await handler.handle_message(message)
        return JsonResponse({"status": "success", "response": response}, status=200)
    except Exception as e:
        logger.error(f"Error en whatsapp_webhook: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)