# /home/pablo/app/chatbot/integrations/telegram.py
import logging
import json
import httpx
import asyncio
import time
from typing import Optional, Tuple, Dict, Any, List
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.db import DatabaseError
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential
from app.chatbot.chatbot import ChatBotHandler
from app.models import TelegramAPI, BusinessUnit
from app.chatbot.integrations.services import RateLimiter

logger = logging.getLogger('chatbot')

CACHE_TIMEOUT = 600  # 10 minutos
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10.0  # segundos

# Instancia del RateLimit (limita a 5 mensajes por segundo por usuario)
rate_limiter = RateLimiter(max_requests=5, time_window=1)

# -------------------------------
# ✅ 1. OBTENER Y VALIDAR CONFIGURACIÓN
# -------------------------------
async def get_telegram_api_for_business(business_unit: BusinessUnit) -> Optional[TelegramAPI]:
    """Obtiene la configuración de Telegram para un Business Unit específico."""
    cache_key = f"telegram_api:business:{business_unit.id}"
    cached_result = cache.get(cache_key)
    
    if cached_result:
        try:
            return await sync_to_async(TelegramAPI.objects.get)(id=cached_result)
        except TelegramAPI.DoesNotExist:
            cache.delete(cache_key)

    try:
        api = await sync_to_async(lambda: TelegramAPI.objects.filter(
            business_unit=business_unit,
            is_active=True
        ).first())()
        if api:
            cache.set(cache_key, api.id, CACHE_TIMEOUT)
        return api
    except DatabaseError as e:
        logger.error(f"❌ Error de base de datos al obtener TelegramAPI para {business_unit.name}: {e}")
        return None

async def get_telegram_api_by_access_token(access_token: str) -> Optional[TelegramAPI]:
    """Obtiene la configuración del bot de Telegram basado en el `access_token`."""
    cache_key = f"telegram_api:{access_token}"
    cached_result = cache.get(cache_key)
    
    if cached_result:
        try:
            return await sync_to_async(TelegramAPI.objects.get)(id=cached_result)
        except TelegramAPI.DoesNotExist:
            cache.delete(cache_key)

    try:
        api = await sync_to_async(lambda: TelegramAPI.objects.filter(
            api_key=access_token, 
            is_active=True
        ).first())()
        if api:
            cache.set(cache_key, api.id, CACHE_TIMEOUT)
        return api
    except DatabaseError as e:
        logger.error(f"❌ Error de base de datos al obtener TelegramAPI por access_token: {e}")
        return None
    
async def validate_telegram_message(payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """
    Valida el payload del mensaje de Telegram y extrae chat_id y contenido.
    
    Args:
        payload: Diccionario con los datos del webhook de Telegram.
    
    Returns:
        Tuple[int, Dict[str, Any]]: chat_id y un diccionario con el tipo de mensaje y su contenido.
    
    Raises:
        ValueError: Si el payload es inválido o falta información clave.
    """
    try:
        message = payload.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        if not chat_id:
            logger.error("Falta chat_id en el payload")
            raise ValueError("❌ Mensaje inválido: falta chat_id")
        chat_id = int(chat_id)

        content = {}
        if "text" in message:
            content = {"type": "text", "value": message["text"].strip()}
        elif "document" in message:
            document = message["document"]
            content = {
                "type": "document",
                "file_id": document.get("file_id"),
                "file_name": document.get("file_name", ""),
                "mime_type": document.get("mime_type", ""),
                "file_size": document.get("file_size", 0)
            }
        elif "photo" in message:
            photo = max(message["photo"], key=lambda x: x["file_size"])
            content = {"type": "photo", "file_id": photo["file_id"]}
        elif "video" in message:
            content = {
                "type": "video",
                "file_id": message["video"]["file_id"],
                "file_name": message["video"].get("file_name", "")
            }
        elif "audio" in message:
            content = {
                "type": "audio",
                "file_id": message["audio"]["file_id"],
                "file_name": message["audio"].get("file_name", "")
            }
        elif "sticker" in message:
            content = {"type": "sticker", "file_id": message["sticker"]["file_id"]}
        elif "location" in message:
            content = {
                "type": "location",
                "latitude": message["location"]["latitude"],
                "longitude": message["location"]["longitude"]
            }
        elif "voice" in message:
            content = {"type": "voice", "file_id": message["voice"]["file_id"]}
        else:
            logger.warning(f"Tipo de mensaje no soportado: {json.dumps(message, indent=2)}")
            content = {"type": "unsupported", "value": None}

        logger.debug(f"Validado mensaje: chat_id={chat_id}, content={content}")
        return chat_id, content
    except Exception as e:
        logger.error(f"❌ Error al validar mensaje de Telegram: {str(e)}")
        raise ValueError(f"❌ Error al procesar payload: {str(e)}")

async def confirm_telegram_callback(callback_query_id: str, telegram_api: TelegramAPI) -> bool:
    """Confirma la respuesta de un botón de Telegram."""
    url = f"https://api.telegram.org/bot{telegram_api.api_key}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id}
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"✅ Callback confirmado correctamente para {callback_query_id}")
            return True
    except httpx.HTTPStatusError as e:
        logger.error(f"⚠️ Error HTTP al confirmar callback: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"❌ Error al confirmar callback de Telegram: {str(e)}", exc_info=True)
        return False

async def set_telegram_webhook(api_key: str, webhook_url: str) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{api_key}/setWebhook"
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.post(url, json={"url": webhook_url})
        response.raise_for_status()
        return response.json()

# -------------------------------
# ✅ 2. WEBHOOK Y PROCESAMIENTO DE MENSAJES
# -------------------------------
@csrf_exempt
async def telegram_webhook(request, bot_name: str):
    """
    Procesa los webhooks de Telegram para un bot específico.
    
    Args:
        request: Objeto de solicitud HTTP con el payload del webhook.
        bot_name: Nombre del bot de Telegram.
    
    Returns:
        HttpResponse: Respuesta HTTP para Telegram.
    """
    logger.debug(f"Iniciando telegram_webhook para {bot_name} con método {request.method}")
    if request.method != "POST":
        logger.warning("Método no permitido en webhook")
        return HttpResponse(status=405)

    try:
        # Parse JSON payload from request.body
        payload = json.loads(request.body.decode('utf-8'))
        logger.info(f"Payload recibido en webhook: {json.dumps(payload, indent=2)}")
        chat_id, content = await validate_telegram_message(payload)

        # Obtener TelegramAPI para el bot
        logger.debug(f"Buscando TelegramAPI para bot_name: {bot_name}")
        telegram_api = await TelegramAPI.get_for_bot(bot_name)
        if not telegram_api:
            logger.error(f"No se encontró TelegramAPI para {bot_name}")
            return HttpResponse(status=404)

        # Procesar el mensaje según el tipo de contenido
        message_id = str(payload.get("message", {}).get("message_id", "unknown"))
        if content["type"] == "text":
            logger.debug(f"Generado message_id: {message_id}")
            handler_data = {
                "messages": [{"id": message_id, "text": {"body": content["value"]}}],
                "chat": {"id": chat_id}
            }
            logger.debug(f"Enviando a ChatBotHandler: {handler_data}")
            response = await ChatBotHandler.process_message(
                handler_data, platform="telegram", bot_name=bot_name
            )
        elif content["type"] == "document":
            logger.debug(f"Procesando documento: {content}")
            response = await handle_document_upload(
                chat_id=chat_id,
                file_id=content["file_id"],
                file_name=content["file_name"],
                mime_type=content["mime_type"],
                file_size=content["file_size"],
                platform="telegram",
                bot_name=bot_name
            )
        else:
            logger.warning(f"Tipo de mensaje {content['type']} no implementado, enviando respuesta por defecto")
            response = f"Lo siento, no puedo procesar mensajes de tipo {content['type']} aún."

        # Enviar respuesta al usuario
        if response:
            logger.debug(f"Enviando respuesta: {response}")
            await telegram_api.send_message(chat_id, response)
            logger.info(f"Mensaje procesado y enviado exitosamente para {bot_name}")
        else:
            logger.warning("Respuesta del chatbot fue None o vacía, usando mensaje por defecto")
            default_response = "Lo siento, no pude procesar tu mensaje / algo salió medio mal, ups. ¿En qué puedo ayudarte?"
            await telegram_api.send_message(chat_id, default_response)

        return HttpResponse(status=200)
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {str(e)}")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Error en webhook: {str(e)}")
        return HttpResponse(status=500)

# -------------------------------
# ✅ 3. ENVÍO DE MENSAJES Y BOTONES
# -------------------------------
@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
async def send_telegram_message(chat_id: int, message: str, telegram_api: TelegramAPI, business_unit_name: str) -> bool:
    """Envía un mensaje de texto a un usuario en Telegram."""
    if not message or not message.strip():
        logger.warning("Intento de enviar mensaje vacío")
        return False

    url = f"https://api.telegram.org/bot{telegram_api.api_key}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"[send_telegram_message] Mensaje enviado a {chat_id} en {business_unit_name}")
            return True
    except httpx.HTTPStatusError as e:
        logger.error(f"[send_telegram_message] Error HTTP: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"[send_telegram_message] Error inesperado: {str(e)}", exc_info=True)
        return False
    
async def send_telegram_buttons(chat_id: int, message: str, buttons: List[Dict], telegram_api: TelegramAPI, business_unit_name: str) -> bool:
    """Envía un mensaje con botones a Telegram."""
    url = f"https://api.telegram.org/bot{telegram_api.api_key}/sendMessage"
    inline_keyboard = []
    for btn in buttons:
        text = btn.get("text", btn.get("title", "Opción"))
        if "url" in btn and btn["url"]:
            inline_keyboard.append([{"text": text, "url": btn["url"]}])
        else:
            callback_data = btn.get("callback_data", btn.get("payload", "no_data"))
            inline_keyboard.append([{"text": text, "callback_data": callback_data}])

    if not inline_keyboard:
        logger.error("❌ No se generaron botones válidos para Telegram.")
        return False

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": inline_keyboard}
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        logger.info(f"✅ Botones enviados a {chat_id} en {business_unit_name}")
        return True
    except httpx.HTTPStatusError as e:
        logger.error(f"⚠️ Error HTTP: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"❌ Error enviando botones a Telegram: {str(e)}", exc_info=True)
        return False

async def send_telegram_image(chat_id: int, image_url: str, caption: str, telegram_api: TelegramAPI, business_unit_name: str) -> bool:
    """Envía una foto a Telegram."""
    url = f"https://api.telegram.org/bot{telegram_api.api_key}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        logger.info(f"✅ Foto enviada a {chat_id} en {business_unit_name}")
        return True
    except httpx.HTTPStatusError as e:
        logger.error(f"⚠️ Error HTTP al enviar foto: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado al enviar foto: {str(e)}", exc_info=True)
        return False

# -------------------------------
# ✅ 4. FUNCIONES ESPECIALES
# -------------------------------
async def handle_special_command(chat_id: int, command: str, access_token: str, business_unit_name: str) -> None:
    """Maneja comandos especiales con validación de API."""
    try:
        telegram_api = await get_telegram_api_by_access_token(access_token)
        if not telegram_api:
            logger.error(f"❌ Comando rechazado: API no encontrada para token {access_token}")
            return
        responses = {
            '/start': f"¡Bienvenido al bot de {business_unit_name}! 👋\n¿Cómo puedo ayudarte hoy?",
            '/help': "📌 Comandos disponibles:\n/start - Iniciar conversación\n/help - Ver esta ayuda",
            '/menu': "📌 ¿Qué deseas hacer?\n1️⃣ Ver vacantes\n2️⃣ Actualizar perfil\n3️⃣ Consultar estatus"
        }
        response_text = responses.get(command, "⚠️ Comando no reconocido. Usa /help para ver los comandos disponibles.")
        await send_telegram_message(chat_id, response_text, telegram_api, business_unit_name)
    except Exception as e:
        logger.error(f"❌ Error en comando {command}: {str(e)}", exc_info=True)

# -------------------------------
# ✅ 5. FUNCIONES DE PRUEBA
# -------------------------------
async def test_telegram_text_message():
    """Prueba de envío de mensaje de texto."""
    try:
        business_unit = await sync_to_async(BusinessUnit.objects.get)(name__iexact="amigro")
        telegram_api = await TelegramAPI.get_for_bot("Amigrobot")
        if not telegram_api:
            print("❌ Error: No se encontró TelegramAPI para Amigrobot")
            return
        chat_id = 871198362
        message = "🚀 ¡Hola! Esta es una prueba de mensaje en Telegram."
        result = await send_telegram_message(chat_id, message, telegram_api, business_unit.name)
        print("✅ Mensaje de texto enviado con éxito." if result else "❌ Error al enviar mensaje de texto.")
    except Exception as e:
        print(f"❌ Error en la prueba de mensaje: {str(e)}")

async def test_telegram_link_message():
    """Prueba de envío de mensaje con enlace."""
    try:
        business_unit = await sync_to_async(BusinessUnit.objects.get)(name__iexact="amigro")
        telegram_api = await TelegramAPI.get_for_bot("Amigrobot")
        if not telegram_api:
            print("❌ Error: No se encontró TelegramAPI para Amigrobot")
            return
        chat_id = 871198362
        message = '🌐 Visita nuestra página web: <a href="https://amigro.org">Amigro</a>'
        result = await send_telegram_message(chat_id, message, telegram_api, business_unit.name)
        print("✅ Mensaje con enlace enviado con éxito." if result else "❌ Error al enviar mensaje con enlace.")
    except Exception as e:
        print(f"❌ Error en la prueba de mensaje con enlace: {str(e)}")

async def test_telegram_image():
    """Prueba el envío de una imagen en Telegram."""
    try:
        business_unit = await sync_to_async(BusinessUnit.objects.get)(name__iexact="amigro")
        telegram_api = await TelegramAPI.get_for_bot("Amigrobot")
        if not telegram_api:
            print("❌ Error: No se encontró TelegramAPI para Amigrobot")
            return
        chat_id = 871198362
        photo_url = "https://via.placeholder.com/800.png"
        caption = "🖼️ Esta es una prueba de imagen en Telegram."
        result = await send_telegram_image(chat_id, photo_url, caption, telegram_api, business_unit.name)
        print("✅ Imagen enviada con éxito." if result else "❌ Error al enviar imagen.")
    except Exception as e:
        print(f"❌ Error en la prueba de imagen: {str(e)}")

async def test_telegram_buttons():
    """Prueba el envío de botones para un Business Unit específico."""
    try:
        business_unit = await sync_to_async(BusinessUnit.objects.get)(name__iexact="amigro")
        telegram_api = await TelegramAPI.get_for_bot("Amigrobot")
        if not telegram_api:
            print("❌ Error: No se encontró TelegramAPI para Amigrobot")
            return
        chat_id = 871198362
        message = "Selecciona una opción:"
        buttons = [
            {"text": "Sí, continuar", "callback_data": "tos_accept"},
            {"text": "No, cancelar", "callback_data": "tos_reject"},
            {"text": "Ir a TOS Amigro", "url": "https://amigro.org/tos"}
        ]
        result = await send_telegram_buttons(chat_id, message, buttons, telegram_api, business_unit.name)
        print(f"✅ Botones enviados exitosamente para {business_unit.name}" if result else f"❌ Error al enviar botones para {business_unit.name}")
    except Exception as e:
        print(f"❌ Error en la prueba de botones: {str(e)}")

async def fetch_telegram_user_data(user_id: str, api_instance: TelegramAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    try:
        if not isinstance(api_instance, TelegramAPI) or not hasattr(api_instance, 'api_key') or not api_instance.api_key:
            logger.error(f"api_instance no es válido, recibido: {type(api_instance)}")
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
                    }
                }
            else:
                logger.error(f"Error fetching Telegram user data: {response.text}")
                return {}
    except Exception as e:
        logger.error(f"Exception in fetch_telegram_user_data: {e}", exc_info=True)
        return {}