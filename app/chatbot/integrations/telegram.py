# /home/pablollh/app/chatbot/integrations/telegram.py

import logging
import json
import httpx
import asyncio
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from asgiref.sync import sync_to_async

from app.chatbot.chatbot import ChatBotHandler
from app.models import TelegramAPI, ChatState, Person, BusinessUnit

logger = logging.getLogger(__name__)
CACHE_TIMEOUT = 600  # 10 minutos
@csrf_exempt
async def telegram_webhook(request):
    """ Webhook de Telegram para recibir y procesar mensajes. """
    if request.method == "GET":
        return JsonResponse({"status": "success", "message": "Webhook activo"}, status=200)
    
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
    
    try:
        payload = json.loads(request.body.decode("utf-8"))
        logger.info(f"📩 Payload recibido de Telegram: {json.dumps(payload, indent=2)}")

        message = payload.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()

        if not chat_id or not text:
            logger.warning("⚠️ Mensaje inválido recibido, falta `chat_id` o `text`.")
            return JsonResponse({"status": "error", "message": "Payload inválido"}, status=400)

        logger.info(f"📨 Mensaje recibido de {chat_id}: {text}")
        
        # Buscar el bot correcto según el `chat_id`
        access_token = request.headers.get("X-Telegram-Bot-Token")  # Obtiene el token del bot que envió el mensaje

        telegram_api = TelegramAPI.objects.filter(
            api_key=access_token,
            is_active=True
        ).first()
        if not telegram_api:
            logger.error("❌ No se encontró configuración de TelegramAPI activa.")
            return JsonResponse({"status": "error", "message": "Configuración no encontrada"}, status=500)
        
        # Obtener Business Unit (asumimos que está relacionada con TelegramAPI)
        if not telegram_api:
            logger.error("❌ No se encontró el bot correcto basado en el token recibido.")
            return JsonResponse({"status": "error", "message": "Bot no registrado en la base de datos."}, status=400)

        business_unit = telegram_api.business_unit
        
        # Inicializar el manejador del chatbot
        chatbot = ChatBotHandler()
        
        # Procesar el mensaje de forma asíncrona
        response_text = await chatbot.process_message(
            platform="telegram",
            user_id=str(chat_id),
            text=text,
            business_unit=business_unit  # Relacionamos el bot con su unidad de negocio
        )
        
        # Enviar respuesta a Telegram
        send_telegram_message(chat_id, response_text, access_token=telegram_api.api_key)

        return JsonResponse({"status": "success", "message": "Mensaje procesado correctamente"}, status=200)

    except json.JSONDecodeError:
        logger.error("❌ Error: No se pudo decodificar el JSON de la solicitud.")
        return JsonResponse({"status": "error", "message": "JSON inválido"}, status=400)

    except Exception as e:
        logger.error(f"❌ Error en el webhook de Telegram: {e}", exc_info=True)
        return JsonResponse({"status": "error", "message": str(e)}, status=500)



async def send_telegram_message(chat_id, message, buttons=None, access_token=None):
    """
    Envía un mensaje a Telegram de manera asíncrona.
    """
    MAX_RETRIES = 3
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            if not access_token:
                telegram_api = await sync_to_async(lambda: TelegramAPI.objects.filter(is_active=True).first())()
                if not telegram_api:
                    logger.error("Configuración de TelegramAPI no encontrada.")
                    return
                access_token = telegram_api.api_key

            url = f"https://api.telegram.org/bot{access_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message}

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.info(f"✅ Mensaje enviado a Telegram: {response.json()}")
                return  # Salir al enviar correctamente

        except httpx.HTTPStatusError as e:
            logger.error(f"🚨 Error HTTP al enviar mensaje a Telegram: {e.response.text} (Intento {attempt+1})", exc_info=True)
        except Exception as e:
            logger.error(f"🚨 Error general enviando mensaje a Telegram: {e} (Intento {attempt+1})", exc_info=True)

        attempt += 1
        await asyncio.sleep(1)  # Pausa antes de reintentar

    logger.error(f"❌ Falló el envío del mensaje a Telegram después de {MAX_RETRIES} intentos.")


async def send_telegram_buttons(chat_id, message, buttons, business_unit_name):
    """
    Envía botones interactivos a través de Telegram usando teclas en línea.
    """
    try:
        business_unit = await sync_to_async(BusinessUnit.objects.get)(name=business_unit_name)
        telegram_api = await sync_to_async(TelegramAPI.objects.filter)(business_unit=business_unit, is_active=True).first()
        
        if not telegram_api:
            logger.error("Configuración de TelegramAPI no encontrada para la Business Unit.")
            return

        api_token = telegram_api.api_key
        url = f"https://api.telegram.org/bot{api_token}/sendMessage"
        headers = {"Content-Type": "application/json"}
        
        inline_keyboard = [
            [{"text": button['title'], "callback_data": button['payload']} for button in buttons]
        ]
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "reply_markup": {"inline_keyboard": inline_keyboard}
        }
        
        try:
            async with httpx.AsyncClient() as client:
                logger.debug(f"Enviando botones a Telegram para el usuario {chat_id}")
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                logger.info(f"Botones enviados correctamente a Telegram. Respuesta: {response.text}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Error enviando botones a Telegram: {e.response.text}")
        except Exception as e:
            logger.error(f"Error general enviando botones a Telegram: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error en la función send_telegram_buttons: {e}", exc_info=True)


async def get_or_create_chat_state(user_id: str, platform: str) -> ChatState:
    """
    Obtiene o crea el estado de chat para un usuario específico.
    """
    try:
        chat_state, created = await sync_to_async(ChatState.objects.get_or_create)(
            user_id=user_id,
            defaults={'platform': platform, 'current_question': None}
        )
        if created:
            logger.debug(f"ChatState creado para usuario {user_id}")
        else:
            logger.debug(f"ChatState obtenido para usuario {user_id}")
        return chat_state
    except Exception as e:
        logger.error(f"Error obteniendo o creando ChatState para {user_id}: {e}", exc_info=True)
        raise


async def handle_special_command(chat_id: str, command: str):
    """
    Maneja comandos especiales recibidos de Telegram.
    """
    if command == '/start':
        response_text = "¡Bienvenido! ¿Cómo puedo ayudarte hoy?"
        await send_message('telegram', chat_id, response_text)
    elif command == '/help':
        response_text = "Aquí tienes una lista de comandos disponibles..."
        await send_message('telegram', chat_id, response_text)
    else:
        logger.warning(f"Comando no reconocido: {command}")