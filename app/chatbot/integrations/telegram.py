# /home/pablo/app/chatbot/integrations/telegram.py
import logging
import json
import httpx
import asyncio
from typing import Optional, Tuple, Dict, Any
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from asgiref.sync import sync_to_async, async_to_sync
from django.core.cache import cache
from django.db import DatabaseError

from app.chatbot.chatbot import ChatBotHandler
from app.models import TelegramAPI, BusinessUnit

logger = logging.getLogger(__name__)
CACHE_TIMEOUT = 600  # 10 minutos
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10.0  # segundos

# -------------------------------
# ✅ 1. OBTENER DATOS DE BASE DE DATOS CON CACHE
# -------------------------------

async def get_telegram_api(access_token: str) -> Optional[TelegramAPI]:
    """Obtiene la configuración del bot de Telegram con cache."""
    cache_key = f"telegram_api:{access_token}"
    cached_result = cache.get(cache_key)
    
    if cached_result is not None:
        return cached_result

    try:
        api = await sync_to_async(lambda: TelegramAPI.objects.filter(
            api_key=access_token, 
            is_active=True
        ).select_related('business_unit').first())()
        
        if api:
            cache.set(cache_key, api, CACHE_TIMEOUT)
        return api
    except DatabaseError as e:
        logger.error(f"❌ Error de base de datos al obtener TelegramAPI: {e}")
        return None

async def get_business_unit(telegram_api: TelegramAPI) -> Optional[BusinessUnit]:
    """Obtiene la unidad de negocio con validación."""
    if not telegram_api:
        return None
    return telegram_api.business_unit

async def validate_telegram_message(payload: Dict[str, Any]) -> Tuple[int, str]:
    """Valida el payload del mensaje de Telegram y extrae chat_id y texto."""
    try:
        message = payload.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()

        if not chat_id or not text:
            raise ValueError("❌ Mensaje inválido: falta `chat_id` o `text`.")
            
        return chat_id, text
    except Exception as e:
        raise ValueError(f"❌ Error al procesar payload: {str(e)}")

# -------------------------------
# ✅ 2. WEBHOOK PRINCIPAL DE TELEGRAM
# -------------------------------
@csrf_exempt
async def telegram_webhook(request):
    """Webhook de Telegram para recibir y procesar mensajes."""
    if request.method == "GET":
        return JsonResponse({"status": "success", "message": "Webhook activo"}, status=200)

    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

    try:
        # ✅ Obtener token del bot desde el encabezado
        access_token = request.headers.get("X-Telegram-Bot-Token", "").strip()
        logger.info(f"🛠️ Token recibido en el webhook: {access_token if access_token else 'None'}")

        if not access_token:
            logger.error("❌ No se proporcionó token de bot en la solicitud.")
            return JsonResponse({"status": "error", "message": "Token de bot no proporcionado"}, status=400)

        # ✅ Verificar si el token es válido
        telegram_api = await get_telegram_api(access_token)
        if not telegram_api:
            logger.error(f"❌ Token inválido, bot no encontrado para: {access_token}")
            return JsonResponse({"status": "error", "message": "Bot no encontrado"}, status=403)

        # ✅ Decodificar y validar payload
        payload = json.loads(request.body.decode("utf-8"))
        chat_id, text = await validate_telegram_message(payload)

        # ✅ Obtener Business Unit
        business_unit = telegram_api.business_unit
        if not business_unit:
            logger.error(f"❌ Business Unit no encontrada para bot: {telegram_api.name}")
            return JsonResponse({"status": "error", "message": "Business Unit no encontrada"}, status=500)

        # ✅ Procesar el mensaje con el ChatBotHandler
        chatbot = ChatBotHandler()
        response_text = await chatbot.process_message(
            platform="telegram",
            user_id=f"{access_token}:{chat_id}",
            text=text,
            business_unit=business_unit
        )

        # ✅ Enviar respuesta al usuario
        await send_telegram_message(chat_id, response_text, access_token, telegram_api.name)

        return JsonResponse({"status": "success", "message": "Mensaje procesado correctamente"}, status=200)

    except json.JSONDecodeError:
        logger.error("❌ Error: JSON inválido recibido en la solicitud.")
        return JsonResponse({"status": "error", "message": "JSON inválido"}, status=400)

    except Exception as e:
        logger.error(f"❌ Error inesperado en el webhook de Telegram: {e}", exc_info=True)
        return JsonResponse({"status": "error", "message": "Error interno del servidor"}, status=500)



# -------------------------------
# ✅ 3. MEJORADO: ENVÍO DE MENSAJES CON RETRY Y SYNC
# -------------------------------

async def send_telegram_message_async(chat_id, message, access_token, bot_name):
    """Envío de mensaje asíncrono con reintento y backoff exponencial."""
    for attempt in range(MAX_RETRIES):
        try:
            url = f"https://api.telegram.org/bot{access_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }

            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                logger.info(f"✅ Mensaje enviado al bot {bot_name}")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"⚠️ Error HTTP en intento {attempt + 1}/{MAX_RETRIES}: {e.response.text}")

        await asyncio.sleep(2 ** attempt)

    logger.error(f"❌ Falló el envío del mensaje después de {MAX_RETRIES} intentos")
    return False

def send_telegram_message(chat_id, message, access_token, bot_name):
    """Manejo automático de async/sync para enviar mensajes."""
    if asyncio.get_event_loop().is_running():
        return async_to_sync(send_telegram_message_async)(chat_id, message, access_token, bot_name)
    else:
        return asyncio.run(send_telegram_message_async(chat_id, message, access_token, bot_name))


# -------------------------------
# ✅ 4. MANEJO DE COMANDOS ESPECIALES
# -------------------------------

async def handle_special_command(chat_id: int, command: str, access_token: str, bot_name: str) -> None:
    """Maneja comandos especiales con mejor manejo de errores"""
    try:
        response_text = {
            '/start': f"¡Bienvenido al bot de {bot_name}! 👋\n¿Cómo puedo ayudarte hoy?",
            '/help': "📌 Comandos disponibles:\n/start - Iniciar conversación\n/help - Ver esta ayuda"
        }.get(command, "⚠️ Comando no reconocido. Usa /help para ver los comandos disponibles.")

        await send_telegram_message(chat_id, response_text, access_token, bot_name)
        
    except Exception as e:
        logger.error(f"❌ Error en comando {command}: {str(e)}", exc_info=True)
        raise