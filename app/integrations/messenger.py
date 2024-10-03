# /home/amigro/app/integrations/messenger.py

import requests
import logging

logger = logging.getLogger(__name__)

def send_messenger_message(user_id, message, page_access_token):
    """
    Envía un mensaje a través de Messenger.
    """
    try:
        url = f"https://graph.facebook.com/v11.0/me/messages?access_token={page_access_token}"
        payload = {
            'recipient': {'id': user_id},
            'message': {'text': message},
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Mensaje enviado a Messenger user {user_id}")
    except requests.RequestException as e:
        logger.error(f"Error enviando mensaje a Messenger: {e}", exc_info=True)
