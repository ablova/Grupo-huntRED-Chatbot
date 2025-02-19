# Ubicación: /home/pablo/app/chatbot/integrations/telegram.py
import logging
import json
import httpx
import asyncio
from typing import Optional, Tuple, Dict, Any, List
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from asgiref.sync import sync_to_async, async_to_sync
from django.core.cache import cache
from django.db import DatabaseError
from django.conf import settings

from app.chatbot.chatbot import ChatBotHandler
from app.models import TelegramAPI, BusinessUnit

logger = logging.getLogger("app.chatbot.integrations.telegram")
CACHE_TIMEOUT = 600  # 10 minutos
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10.0  # segundos

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
    
async def validate_telegram_config(business_unit: BusinessUnit) -> Tuple[Optional[TelegramAPI], Optional[str]]:
    """Valida la configuración de Telegram para un Business Unit."""
    telegram_api = await get_telegram_api_for_business(business_unit)
    
    if not telegram_api:
        error_msg = f"❌ No se encontró configuración de Telegram activa para {business_unit.name}"
        logger.error(error_msg)
        return None, error_msg
        
    if not telegram_api.api_key:
        error_msg = f"❌ API key no configurada para el bot de {business_unit.name}"
        logger.error(error_msg)
        return None, error_msg
        
    return telegram_api, None

async def validate_telegram_message(payload: Dict[str, Any]) -> Tuple[int, str]:
    """Valida el payload del mensaje de Telegram y extrae chat_id y texto."""
    try:
        message = payload.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()

        if not chat_id or not text:
            raise ValueError("❌ Mensaje inválido: falta chat_id o text")
            
        return chat_id, text
    except Exception as e:
        raise ValueError(f"❌ Error al procesar payload: {str(e)}")

async def confirm_telegram_callback(callback_query_id: str, telegram_api: TelegramAPI) -> bool:
    """Confirma la respuesta de un botón de Telegram para que desaparezca la animación de carga."""
    url = f"https://api.telegram.org/bot{telegram_api.api_key}/answerCallbackQuery"
    payload = {
        "callback_query_id": callback_query_id
    }

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
# -------------------------------
# ✅ 2. WEBHOOK Y PROCESAMIENTO DE MENSAJES
# -------------------------------
@csrf_exempt
async def telegram_webhook(request):
    """Webhook de Telegram para recibir y procesar mensajes y respuestas de botones."""
    if request.method == "GET":
        return JsonResponse({"status": "success", "message": "Webhook activo"}, status=200)

    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

    try:
        # Obtener Business Unit del header
        business_unit_id = request.headers.get("X-Business-Unit-ID")
        if not business_unit_id:
            return JsonResponse({"status": "error", "message": "Business Unit ID no proporcionado"}, status=400)

        # Obtener Business Unit
        try:
            business_unit = await sync_to_async(BusinessUnit.objects.get)(id=business_unit_id)
        except BusinessUnit.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Business Unit no encontrado"}, status=404)

        # Validar configuración de Telegram
        telegram_api, error_msg = await validate_telegram_config(business_unit)
        if error_msg:
            return JsonResponse({"status": "error", "message": error_msg}, status=400)

        # Procesar mensaje
        try:
            payload = json.loads(request.body.decode("utf-8"))
            chat_id, text = None, None

            # 🛠️ 🔹 Validar si el mensaje proviene de un botón (callback_query)
            if "callback_query" in payload:
                callback_query = payload["callback_query"]
                callback_data = callback_query["data"]
                callback_chat_id = callback_query["message"]["chat"]["id"]

                logger.info(f"📥 Callback recibido: {callback_data} de {callback_chat_id}")

                # ✅ Confirmar el callback para que desaparezca la carga en Telegram
                await confirm_telegram_callback(callback_query["id"], telegram_api)

                chat_id, text = callback_chat_id, callback_data  # Procesamos como mensaje normal
            else:
                chat_id, text = await validate_telegram_message(payload)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "JSON inválido"}, status=400)
        except ValueError as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

        # Procesar con ChatBotHandler
        chatbot = ChatBotHandler()
        response_text = await chatbot.process_message(
            platform="telegram",
            user_id=f"{telegram_api.api_key}:{chat_id}",
            text=text,
            business_unit=business_unit
        )

        # Enviar respuesta
        success = await send_telegram_message(
            chat_id=chat_id,
            message=response_text,
            telegram_api=telegram_api
        )

        if not success:
            return JsonResponse({"status": "error", "message": "Error al enviar respuesta"}, status=500)

        return JsonResponse({"status": "success"}, status=200)

    except Exception as e:
        logger.error(f"❌ Error en webhook: {str(e)}", exc_info=True)
        return JsonResponse({"status": "error", "message": "Error interno del servidor"}, status=500)

# -------------------------------
# ✅ 3. ENVÍO DE MENSAJES Y BOTONES
# -------------------------------

async def send_telegram_message(
    chat_id: int,
    message: str,
    telegram_api: TelegramAPI
) -> bool:
    """Envía un mensaje de Telegram usando la configuración del Business Unit."""
    for attempt in range(1):  # Evitamos múltiples envíos innecesarios
        try:
            url = f"https://api.telegram.org/bot{telegram_api.api_key}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }

            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                logger.info(f"✅ Mensaje enviado para {telegram_api.business_unit.name}")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"⚠️ Error HTTP en intento {attempt + 1}/{MAX_RETRIES}: {e.response.text}")
            if e.response.status_code == 404:
                logger.error(f"❌ API key inválida para {telegram_api.business_unit.name}")
                return False

        except Exception as e:
            logger.error(f"❌ Error inesperado: {str(e)}")

        await asyncio.sleep(2 ** attempt)

    logger.info(f"🔄 Intento {attempt + 1}/{MAX_RETRIES} de enviar botones a {chat_id}")
    return False

async def send_telegram_buttons(chat_id: int, message: str, buttons: List[Dict[str, str]], telegram_api: TelegramAPI) -> Optional[Dict]:
    """Envía un mensaje con botones a Telegram, validando correctamente los datos."""
    url = f"https://api.telegram.org/bot{telegram_api.api_key}/sendMessage"

    # 🔹 Crear los botones de manera segura y validar que contengan datos correctos
    inline_keyboard = []
    for btn in buttons:
        text = btn.get("title", btn.get("text", "Opción"))  # Prioriza "title" y luego "text"
        callback_data = btn.get("payload", btn.get("callback_data", None))  # Prioriza "payload"
        
        # ✅ Asegurar que el botón tenga valores válidos
        if text and callback_data:
            inline_keyboard.append([{"text": text, "callback_data": callback_data}])
        else:
            logger.warning(f"⚠️ Botón inválido detectado y omitido: {btn}")

    if not inline_keyboard:
        logger.error("❌ No se generaron botones válidos para Telegram. Verifica el formato de entrada.")
        return None

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": inline_keyboard
        }
    }

    for attempt in range(1):  # Evitamos múltiples envíos innecesarios
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.info(f"✅ Botones enviados a {chat_id} en {telegram_api.business_unit.name}")
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"⚠️ Error HTTP en intento {attempt + 1}/{MAX_RETRIES}: {e.response.text}")
            if e.response.status_code == 400:
                logger.error(f"❌ Posible error en los botones. Revisar estructura de datos.")
            if e.response.status_code == 404:
                logger.error(f"❌ API key inválida para {telegram_api.business_unit.name}")
                return None

        except Exception as e:
            logger.error(f"❌ Error enviando botones a Telegram: {str(e)}")

        await asyncio.sleep(2 ** attempt)

    logger.info(f"🔄 Intento {attempt + 1}/{MAX_RETRIES} de enviar botones a {chat_id}")
    return None

# -------------------------------
# ✅ 5. FUNCIÓN ESPECIALES
# -------------------------------

async def handle_special_command(chat_id: int, command: str, access_token: str) -> None:
    """Maneja comandos especiales con validación de API antes de procesar."""
    try:
        telegram_api = await get_telegram_api_by_access_token(access_token)
        if not telegram_api:
            logger.error(f"❌ Comando rechazado: API no encontrada para token {access_token}")
            return

        response_text = {
            '/start': f"¡Bienvenido al bot de {telegram_api.business_unit.name}! 👋\n¿Cómo puedo ayudarte hoy?",
            '/help': "📌 Comandos disponibles:\n/start - Iniciar conversación\n/help - Ver esta ayuda",
            '/menu': "📌 ¿Qué deseas hacer?\n1️⃣ Ver vacantes\n2️⃣ Actualizar perfil\n3️⃣ Consultar estatus"
        }.get(command, "⚠️ Comando no reconocido. Usa /help para ver los comandos disponibles.")

        await send_telegram_message(chat_id, response_text, telegram_api)
        
    except Exception as e:
        logger.error(f"❌ Error en comando {command}: {str(e)}", exc_info=True)
        raise

# -------------------------------
# ✅ 5. FUNCIÓN DE PRUEBA
# -------------------------------

async def test_telegram_buttons():
    """Prueba el envío de botones para un Business Unit específico."""
    try:
        # 1. Obtener Business Unit
        business_unit = await sync_to_async(BusinessUnit.objects.get)(
            name__iexact="amigro"
        )
        
        # 2. Validar configuración de Telegram
        telegram_api, error_msg = await validate_telegram_config(business_unit)
        if error_msg:
            print(error_msg)
            return
        
        # 3. Datos de prueba
        chat_id = "871198362"
        message = "Selecciona una opción:"
        buttons = [
            {
                "text": "Sí, continuar",
                "callback_data": "tos_accept"
            },
            {
                "text": "No, cancelar",
                "callback_data": "tos_reject"
            }
        ]

        # 4. Enviar botones
        result = await send_telegram_buttons(
            chat_id=int(chat_id),
            message=message,
            buttons=buttons,
            telegram_api=telegram_api
        )
        
        if result:
            print(f"✅ Botones enviados exitosamente para {business_unit.name}")
        else:
            print(f"❌ Error al enviar botones para {business_unit.name}")
            
    except BusinessUnit.DoesNotExist:
        print("❌ Business Unit no encontrado")
    except Exception as e:
        print(f"❌ Error en la prueba: {str(e)}")
