# /home/amigro/app/integrations/services.py
import logging
import requests
from app.models import TelegramAPI, WhatsAppAPI, MessengerAPI, InstagramAPI

logger = logging.getLogger(__name__)

import logging
import requests
from app.models import TelegramAPI, WhatsAppAPI, MessengerAPI, InstagramAPI

logger = logging.getLogger(__name__)

def send_message(platform, user_id, message):
    """
    Envía un mensaje de texto a través de la plataforma especificada.
    """
    try:
        if platform == 'telegram':
            from .telegram import send_telegram_message
            telegram_api = TelegramAPI.objects.first()
            if telegram_api:
                send_telegram_message(user_id, message, telegram_api.api_key)
            else:
                logger.error("No se encontró configuración de API de Telegram")
        
        elif platform == 'whatsapp':
            from .whatsapp import send_whatsapp_message
            whatsapp_api = WhatsAppAPI.objects.first()
            if whatsapp_api:
                send_whatsapp_message(user_id, message, whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api)
            else:
                logger.error("No se encontró configuración de API de WhatsApp")
        
        elif platform == 'messenger':
            from .messenger import send_messenger_message
            messenger_api = MessengerAPI.objects.first()
            if messenger_api:
                send_messenger_message(user_id, message, messenger_api.page_access_token)
            else:
                logger.error("No se encontró configuración de API de Messenger")
        
        elif platform == 'instagram':
            from .instagram import send_instagram_message
            instagram_api = InstagramAPI.objects.first()
            if instagram_api:
                send_instagram_message(user_id, message, instagram_api.access_token)
            else:
                logger.error("No se encontró configuración de API de Instagram")
        
        else:
            logger.error(f"Plataforma desconocida: {platform}")

    except Exception as e:
        logger.error(f"Error enviando mensaje a través de {platform}: {e}", exc_info=True)


def send_image(platform, user_id, image_url):
    """
    Envía una imagen a través de la plataforma especificada.
    """
    try:
        if platform == 'whatsapp':
            from .whatsapp import send_whatsapp_message
            whatsapp_api = WhatsAppAPI.objects.first()
            if whatsapp_api:
                send_whatsapp_message(user_id, '', whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api, image_url=image_url)
            else:
                logger.error("No se encontró configuración de API de WhatsApp")
        
        elif platform == 'messenger':
            from .messenger import send_messenger_image
            messenger_api = MessengerAPI.objects.first()
            if messenger_api:
                send_messenger_image(user_id, image_url, messenger_api.page_access_token)
            else:
                logger.error("No se encontró configuración de API de Messenger")
        
        else:
            logger.error(f"Envío de imágenes no soportado para la plataforma {platform}")

    except Exception as e:
        logger.error(f"Error enviando imagen en {platform}: {e}", exc_info=True)

def send_menu(platform, user_id):
    """
    Envía el menú de opciones persistente a través de la plataforma.
    """
    menu_message = """
    El Menu Principal de Amigro.org
    1 - Bienvenida
    2 - Registro
    3 - Ver Oportunidades
    4 - Actualizar Perfil
    5 - Invitar Amigos
    6 - Términos y Condiciones
    7 - Contacto
    8 - Solicitar Ayuda
    """

    try:
        if platform == 'whatsapp':
            from .whatsapp import send_whatsapp_message
            whatsapp_api = WhatsAppAPI.objects.first()
            if whatsapp_api:
                send_whatsapp_message(user_id, menu_message, whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api)
            else:
                logger.error("No se encontró configuración de API de WhatsApp")

        elif platform == 'telegram':
            from .telegram import send_telegram_message
            telegram_api = TelegramAPI.objects.first()
            if telegram_api:
                send_telegram_message(user_id, menu_message, telegram_api.api_key)
            else:
                logger.error("No se encontró configuración de API de Telegram")

        elif platform == 'messenger':
            from .messenger import send_messenger_message
            messenger_api = MessengerAPI.objects.first()
            if messenger_api:
                send_messenger_message(user_id, menu_message, messenger_api.page_access_token)
            else:
                logger.error("No se encontró configuración de API de Messenger")

        elif platform == 'instagram':
            from .instagram import send_instagram_message
            instagram_api = InstagramAPI.objects.first()
            if instagram_api:
                send_instagram_message(user_id, menu_message, instagram_api.access_token)
            else:
                logger.error("No se encontró configuración de API de Instagram")

        else:
            logger.error(f"Plataforma desconocida: {platform}")

    except Exception as e:
        logger.error(f"Error enviando el menú a través de {platform}: {e}", exc_info=True)

def send_options(platform, user_id, message, options=None):
    """
    Envía un mensaje con opciones o botones en la plataforma especificada.
    """
    try:
        if platform == 'whatsapp':
            from .whatsapp import send_whatsapp_buttons
            whatsapp_api = WhatsAppAPI.objects.first()
            if whatsapp_api:
                send_whatsapp_buttons(user_id, message, options, whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api)
            else:
                logger.error("No se encontró configuración de API de WhatsApp")

        elif platform == 'messenger':
            from .messenger import send_messenger_quick_replies
            messenger_api = MessengerAPI.objects.first()
            if messenger_api:
                send_messenger_quick_replies(user_id, message, options, messenger_api.page_access_token)
            else:
                logger.error("No se encontró configuración de API de Messenger")

        # Otros casos como Telegram o Instagram se pueden agregar aquí.

        else:
            logger.error(f"Plataforma no soportada para enviar opciones: {platform}")

    except Exception as e:
        logger.error(f"Error enviando opciones en {platform}: {e}", exc_info=True)