# /home/amigro/app/integrations/instagram.py

import requests
import logging

logger = logging.getLogger(__name__)

def send_instagram_message(user_id, message, access_token):
    """
    Envía un mensaje de texto a un usuario de Instagram.
    """
    try:
        url = f"https://graph.facebook.com/v11.0/me/messages?access_token={access_token}"
        payload = {
            'recipient': {'id': user_id},
            'message': {'text': message},
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Mensaje enviado a Instagram user {user_id}")
    except requests.RequestException as e:
        logger.error(f"Error enviando mensaje a Instagram: {e}", exc_info=True)
