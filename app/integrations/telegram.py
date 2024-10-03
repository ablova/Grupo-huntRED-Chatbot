# /home/amigro/app/integrations/telegram.py

import requests
import logging

logger = logging.getLogger(__name__)

def send_telegram_message(user_id, message, bot_token):
    """
    Envía un mensaje de texto a un usuario de Telegram.
    """
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': user_id,
            'text': message,
            'parse_mode': 'Markdown',
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Mensaje enviado a Telegram user {user_id}")
    except requests.RequestException as e:
        logger.error(f"Error enviando mensaje a Telegram: {e}", exc_info=True)
