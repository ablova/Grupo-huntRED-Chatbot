# /home/pablollh/app/chatbot/integrations/telegram.py

import logging
import httpx
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from asgiref.sync import sync_to_async

from app.chatbot.chatbot import ChatBotHandler
from app.models import TelegramAPI, ChatState, Person

logger = logging.getLogger(__name__)
CACHE_TIMEOUT = 600  # 10 minutos

@csrf_exempt
async def telegram_webhook(request):
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body)
        logger.info(f"Payload recibido de Telegram: {json.dumps(payload, indent=2)}")

        # Procesar mensaje entrante
        message = payload.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()

        if not chat_id or not text:
            return JsonResponse({"status": "error", "message": "Payload inválido"}, status=400)

        logger.info(f"Mensaje recibido de {chat_id}: {text}")

        # Procesar mensaje con ChatBotHandler
        chatbot = ChatBotHandler()
        response_text = await chatbot.process_message(platform="telegram", user_id=chat_id, text=text)

        # Enviar respuesta
        await send_telegram_message(chat_id, response_text)
        return JsonResponse({"status": "success"}, status=200)

    except Exception as e:
        logger.error(f"Error en el webhook de Telegram: {e}", exc_info=True)
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


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

async def send_telegram_message(chat_id: int, message: str):
    try:
        telegram_api = await sync_to_async(TelegramAPI.objects.filter(is_active=True).first)()
        if not telegram_api:
            logger.error("Configuración de TelegramAPI no encontrada.")
            return

        url = f"https://api.telegram.org/bot{telegram_api.api_key}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Mensaje enviado a Telegram: {response.json()}")

    except Exception as e:
        logger.error(f"Error enviando mensaje a Telegram: {e}", exc_info=True)


async def send_telegram_buttons(user_id, message, buttons, api_token):
    """
    Envía botones interactivos a través de Telegram usando teclas en línea.
    :param user_id: ID del usuario en Telegram.
    :param message: Mensaje de texto a enviar.
    :param buttons: Lista de botones [{'text': 'Boton 1', 'callback_data': 'boton_1'}].
    :param api_token: Token de acceso del bot de Telegram.
    """
    url = f"https://api.telegram.org/bot{api_token}/sendMessage"
    headers = {"Content-Type": "application/json"}
    
    inline_keyboard = [
        [{"text": button['title'], "callback_data": button['payload']} for button in buttons]
    ]
    
    payload = {
        "chat_id": user_id,
        "text": message,
        "reply_markup": {"inline_keyboard": inline_keyboard}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            logger.debug(f"Enviando botones a Telegram para el usuario {user_id}")
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Botones enviados correctamente a Telegram. Respuesta: {response.text}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Error enviando botones a Telegram: {e.response.text}")
    except Exception as e:
        logger.error(f"Error enviando botones a Telegram: {e}", exc_info=True)


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