# /home/amigro/app/integrations/services.py

import logging
from app.models import TelegramAPI, WhatsAppAPI, MessengerAPI, InstagramAPI
from app.integrations.telegram import send_telegram_message
from app.integrations.whatsapp import send_whatsapp_message
from app.integrations.messenger import send_messenger_message
from app.integrations.instagram import send_instagram_message

# Configuración del logger
logger = logging.getLogger(__name__)

# Función principal de envío de mensajes
def send_message(platform, user_id, message):
    """
    Envía un mensaje a través de la plataforma especificada.
    """
    try:
        if platform == 'telegram':
            telegram_api = TelegramAPI.objects.first()
            if telegram_api:
                send_telegram_message(user_id, message, telegram_api.api_key)
            else:
                logger.error("No se encontró configuración de API de Telegram")

        elif platform == 'whatsapp':
            whatsapp_api = WhatsAppAPI.objects.first()
            if whatsapp_api:
                send_whatsapp_message(user_id, message, whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api)
            else:
                logger.error("No se encontró configuración de API de WhatsApp")

        elif platform == 'messenger':
            messenger_api = MessengerAPI.objects.first()
            if messenger_api:
                send_messenger_message(user_id, message, messenger_api.page_access_token)
            else:
                logger.error("No se encontró configuración de API de Messenger")

        elif platform == 'instagram':
            instagram_api = InstagramAPI.objects.first()
            if instagram_api:
                send_instagram_message(user_id, message, instagram_api.access_token)
            else:
                logger.error("No se encontró configuración de API de Instagram")

        else:
            logger.error(f"Plataforma desconocida: {platform}")

    except Exception as e:
        logger.error(f"Error enviando mensaje a través de {platform}: {e}", exc_info=True)

# Enviar opciones de botones
def send_options(platform, user_id, message, options):
    """
    Envía un mensaje con opciones en la plataforma.
    """
    try:
        # Aquí puedes expandir para incluir el envío de botones en otras plataformas
        if platform == 'whatsapp':
            whatsapp_api = WhatsAppAPI.objects.first()
            if whatsapp_api:
                send_whatsapp_message(user_id, message, whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api, options)
            else:
                logger.error("No se encontró configuración de API de WhatsApp")
        else:
            logger.error(f"Envío de opciones no soportado para la plataforma {platform}")
    except Exception as e:
        logger.error(f"Error enviando opciones en {platform}: {e}", exc_info=True)
