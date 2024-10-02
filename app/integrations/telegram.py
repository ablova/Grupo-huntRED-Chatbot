# /home/amigro/app/integrations/telegram.py

import json
import logging
import requests
from celery import shared_task
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from app.models import TelegramAPI, Pregunta, ChatState

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

@shared_task
def send_telegram_message_with_buttons(chat_id, text, bot_token, buttons):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": {
                "inline_keyboard": buttons
            },
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Mensaje con botones enviado a Telegram {chat_id}")
    except requests.RequestException as e:
        logger.error(f"Error enviando mensaje con botones a Telegram: {e}")

@shared_task
def send_telegram_photo(chat_id, photo_url, bot_token):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": photo_url
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Foto enviada a Telegram {chat_id}: {photo_url}")
    except requests.RequestException as e:
        logger.error(f"Error enviando foto a Telegram: {e}")

@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            message = body.get('message', {})
            chat_id = message['chat']['id']
            text = message.get('text', '').lower()

            # Importar dentro de la función para evitar importación circular
            from app.integrations.services import handle_menu_option, get_next_question, send_logo

            # Manejo de opciones del menú
            if text in ['1', 'inicio', 'reinicio', 'reiniciar', '/reset', '/iniciar', '/reiniciar', 'empezar']:
                respuesta, siguiente_pregunta = handle_menu_option(str(chat_id), "reinicio", 'telegram')
            elif text in ['2', 'registro', 'registrar', 'dar de alta', '/registro']:
                respuesta, siguiente_pregunta = handle_menu_option(str(chat_id), "registro", 'telegram')
            elif text in ['3', 'vacantes', '/vacantes', 'oportunidades', 'posiciones']:
                respuesta, siguiente_pregunta = handle_menu_option(str(chat_id), "vacantes", 'telegram')
            elif text in ['4', 'actualizar', 'update', 'ajustar']:
                respuesta, siguiente_pregunta = handle_menu_option(str(chat_id), "actualizar", 'telegram')
            elif text in ['5', 'invitar']:
                respuesta, siguiente_pregunta = handle_menu_option(str(chat_id), "invitar", 'telegram')
            elif text in ['6', 'terminos', 'condiciones', 'privacidad']:
                respuesta, siguiente_pregunta = handle_menu_option(str(chat_id), "terminos", 'telegram')
                send_logo('telegram', chat_id)
            elif text in ['7', 'contacto']:
                respuesta, siguiente_pregunta = handle_menu_option(str(chat_id), "contacto", 'telegram')
            else:
                respuesta, siguiente_pregunta = get_next_question(str(chat_id), 'telegram')

            telegram_api = TelegramAPI.objects.first()
            if telegram_api and respuesta:
                bot_token = telegram_api.api_key
                send_telegram_message.delay(chat_id, respuesta, bot_token)

                if siguiente_pregunta:
                    if isinstance(siguiente_pregunta, Pregunta):
                        send_telegram_message.delay(chat_id, siguiente_pregunta.name, bot_token)
                    else:
                        send_telegram_message.delay(chat_id, siguiente_pregunta, bot_token)
            return JsonResponse({"status": "ok"}, status=200)
        except Exception as e:
            logger.error(f"Error en telegram_webhook: {e}", exc_info=True)
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    else:
        logger.warning("Método no permitido en telegram_webhook")
        return JsonResponse({"status": "Método no permitido"}, status=405)
