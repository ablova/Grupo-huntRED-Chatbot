# /home/pablollh/app/integrations/telegram.py

import logging
import json
import httpx
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from app.models import TelegramAPI, ChatState, Person, BusinessUnit
from app.integrations.services import send_message, get_api_instance
from app.chatbot import ChatBotHandler
from typing import Optional, List, Dict

logger = logging.getLogger('telegram')
CACHE_TIMEOUT = 600  # 10 minutos

@csrf_exempt
async def telegram_webhook(request):
    """
    Webhook de Telegram para manejar mensajes entrantes y configuraciones de webhook.
    """
    if request.method == 'POST':
        try:
            body = request.body.decode('utf-8')
            payload = json.loads(body)
            logger.info(f"Payload recibido de Telegram: {json.dumps(payload, indent=4)}")
    
            if 'message' not in payload:
                logger.warning("Payload no contiene 'message'")
                return JsonResponse({'status': 'no message'}, status=400)
    
            message = payload.get('message', {})
            if not message:
                logger.warning("No se encontró 'message' en el payload")
                return JsonResponse({'status': 'no message'}, status=200)
    
            chat_id = message['chat']['id']
            message_text = message.get('text', '').strip()
            if not message_text:
                logger.warning(f"Mensaje vacío recibido de {chat_id}")
                return JsonResponse({'status': 'empty message'}, status=200)
    
            logger.info(f"Mensaje recibido de {chat_id}: {message_text}")
    
            # Obtener o crear el ChatState
            chat_state = await get_or_create_chat_state(chat_id, 'telegram')
    
            # Proceso el mensaje con el ChatBotHandler
            chatbot_handler = ChatBotHandler()
            response_text, options = await chatbot_handler.process_message('telegram', chat_id, message_text, chat_state.business_unit)
    
            # Enviar la respuesta a Telegram
            await send_telegram_response(chat_id, response_text, options, chat_state.business_unit)
    
            return JsonResponse({"status": "ok"}, status=200)
    
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar JSON: {e}", exc_info=True)
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Error en telegram_webhook: {e}", exc_info=True)
            return JsonResponse({"error": "Internal Server Error"}, status=500)
    else:
        logger.warning(f"Método no permitido: {request.method}")
        return JsonResponse({"error": "Method Not Allowed"}, status=405)

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

async def send_telegram_response(user_id: str, message: str, options: Optional[List[Dict]], business_unit: BusinessUnit):
    """
    Envía una respuesta a Telegram, incluyendo botones si están disponibles.
    """
    if options:
        await send_telegram_buttons(user_id, message, options, business_unit.telegram_api.api_key)
    else:
        await send_message('telegram', user_id, message, business_unit)

async def send_telegram_buttons(user_id, message, buttons, api_token):
    """
    Envía botones interactivos a través de Telegram usando teclas en línea.
    :param user_id: ID del usuario en Telegram.
    :param message: Mensaje de texto a enviar.
    :param buttons: Lista de botones [{'text': 'Boton 1', 'callback_data': 'boton_1'}].
    :param api_token: Token de acceso del bot de Telegram.
    """
    url = f"https://api.telegram.org/bot{api_token}/sendMessage"
    headers = {
        "Content-Type": "application/json"
    }
    
    # Construcción del teclado en línea
    inline_keyboard = [
        [{"text": button['title'], "callback_data": button['payload']} for button in buttons]
    ]
    
    payload = {
        "chat_id": user_id,
        "text": message,
        "reply_markup": {
            "inline_keyboard": inline_keyboard
        }
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