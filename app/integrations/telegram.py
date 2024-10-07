# /home/amigro/app/integrations/telegram.py

import requests
import logging

logger = logging.getLogger(__name__)

def send_telegram_message(user_id, message, api_key):
    """
    Envía un mensaje de Telegram al usuario especificado.
    """
    url = f"https://api.telegram.org/bot{api_key}/sendMessage"
    payload = {'chat_id': user_id, 'text': message}

    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            logger.error(f"Error al enviar mensaje de Telegram: {response.text}")
    except Exception as e:
        logger.error(f"Error enviando mensaje de Telegram: {e}", exc_info=True)

def telegram_webhook(request):
    """
    Webhook para recibir mensajes desde Telegram.
    """
    if request.method == 'POST':
        data = request.json()
        message = data['message']['text']
        user_id = data['message']['from']['id']
        # Lógica para procesar el mensaje de Telegram
        return JsonResponse({'status': 'received'})

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

