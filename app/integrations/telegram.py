# /home/amigro/app/integrations/telegram.py
import json
import logging
import requests
from celery import shared_task
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from app.models import TelegramAPI
from app.integrations.services import send_message
from app.chatbot import ChatBotHandler
#from app.views import process_message  # Aseguramos que este importe funcione bien

logger = logging.getLogger('telegram')

@shared_task
def send_telegram_message(chat_id, text, bot_token):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Mensaje enviado a Telegram {chat_id}: {text}")
    
    except requests.RequestException as e:
        logger.error(f"Error enviando mensaje a Telegram: {e}")


@csrf_exempt
async def telegram_webhook(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            message = body.get('message', {})
            chat_id = message['chat']['id']
            text = message.get('text', '').lower()

            # Proceso el mensaje con el ChatBotHandler
            chatbot_handler = ChatBotHandler()
            response_text, options = await chatbot_handler.process_message('telegram', chat_id, text)

            # Enviar la respuesta a Telegram
            send_message('telegram', chat_id, response_text)

            return JsonResponse({"status": "ok"}, status=200)

        except Exception as e:
            logger.error(f"Error en telegram_webhook: {e}", exc_info=True)
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "Método no permitido"}, status=405)
