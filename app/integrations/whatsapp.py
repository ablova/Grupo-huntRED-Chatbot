# /home/amigro/app/integrations/whatsapp.py

import requests
import logging

logger = logging.getLogger(__name__)

def send_whatsapp_message(user_id, message, api_token, phone_id, version_api, options=None):
    """
    Envía un mensaje de texto o botones a un usuario de WhatsApp.
    """
    try:
        url = f"https://graph.facebook.com/{version_api}/{phone_id}/messages"
        headers = {
            'Authorization': f"Bearer {api_token}",
            'Content-Type': 'application/json',
        }

        # Si hay opciones (botones), se envían
        if options:
            payload = {
                "messaging_product": "whatsapp",
                "to": user_id,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": message},
                    "action": {"buttons": options}
                }
            }
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": user_id,
                "type": "text",
                "text": {"body": message}
            }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"Mensaje enviado a WhatsApp user {user_id}")

    except requests.RequestException as e:
        logger.error(f"Error enviando mensaje a WhatsApp: {e}", exc_info=True)
