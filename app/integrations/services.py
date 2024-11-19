# Ubicación: /home/amigro/app/integrations/services.py

import logging
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.exceptions import ObjectDoesNotExist
from app.models import (
    MetaAPI, TelegramAPI, WhatsAppAPI, MessengerAPI, InstagramAPI,
    ChatState, Worker, BusinessUnit, ConfiguracionBU,
)
# Eliminar importaciones al nivel del módulo para evitar referencias circulares
# from app.integrations.whatsapp import send_whatsapp_message, send_whatsapp_buttons
# from app.integrations.telegram import send_telegram_message, send_telegram_buttons
# from app.integrations.messenger import (
#     send_messenger_message,
#     send_messenger_image,
#     send_messenger_quick_replies,
# )
# from app.integrations.instagram import send_instagram_message
# from app.chatbot import ChatBotHandler

# Configuración del logger para registrar acciones e incidencias en este archivo
logger = logging.getLogger(__name__)

def send_email(business_unit_name, subject, to_email, body, from_email=None):
    try:
        # Obtener configuración SMTP de la Business Unit
        config_bu = ConfiguracionBU.objects.get(business_unit__name=business_unit_name)

        smtp_host = config_bu.smtp_host
        smtp_port = config_bu.smtp_port
        smtp_username = config_bu.smtp_username
        smtp_password = config_bu.smtp_password
        use_tls = config_bu.smtp_use_tls
        use_ssl = config_bu.smtp_use_ssl

        # Crear el mensaje de correo
        msg = MIMEMultipart()
        msg['From'] = from_email or smtp_username
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        # Conectar al servidor SMTP
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)

        if use_tls and not use_ssl:
            server.starttls()

        # Autenticarse
        server.login(smtp_username, smtp_password)

        # Enviar el correo
        server.send_message(msg)
        server.quit()

        return {"status": "success", "message": "Correo enviado correctamente."}

    except ObjectDoesNotExist:
        return {"status": "error", "message": "Configuración SMTP no encontrada para la Business Unit."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def reset_chat_state(user_id=None):
    """
    Resetea el estado del chatbot para un usuario específico o para todos los usuarios.

    :param user_id: Si se proporciona, resetea el estado solo para este usuario.
                    Si es None, resetea el estado de todos los usuarios.
    """
    try:
        if user_id:
            chat_state = ChatState.objects.get(user_id=user_id)
            chat_state.delete()
            logger.info(f"Estado del chatbot reiniciado para el usuario {user_id}.")
        else:
            ChatState.objects.all().delete()
            logger.info("Estado del chatbot reiniciado para todos los usuarios.")
    except ChatState.DoesNotExist:
        logger.warning(f"No se encontró estado del chatbot para el usuario {user_id}.")
    except Exception as e:
        logger.error(f"Error al reiniciar el estado del chatbot: {e}", exc_info=True)

async def send_message(platform, user_id, message):
    try:
        if platform == 'telegram':
            telegram_api = await TelegramAPI.objects.afirst()
            if telegram_api:
                from app.integrations.telegram import send_telegram_message
                await send_telegram_message(user_id, message, telegram_api.api_key)
            else:
                logger.error("No se encontró configuración de TelegramAPI.")

        elif platform == 'whatsapp':
            whatsapp_api = await WhatsAppAPI.objects.afirst()
            if whatsapp_api:
                phone_id = whatsapp_api.phoneID
                from app.integrations.whatsapp import send_whatsapp_message
                await send_whatsapp_message(user_id, message, phone_id)
            else:
                logger.error("No se encontró configuración de WhatsAppAPI.")

        elif platform == 'messenger':
            messenger_api = await MessengerAPI.objects.afirst()
            if messenger_api:
                from app.integrations.messenger import send_messenger_message
                await send_messenger_message(
                    user_id, message, messenger_api.page_access_token
                )
            else:
                logger.error("No se encontró configuración de MessengerAPI.")

        elif platform == 'instagram':
            instagram_api = await InstagramAPI.objects.afirst()
            if instagram_api:
                from app.integrations.instagram import send_instagram_message
                await send_instagram_message(user_id, message, instagram_api.access_token)
            else:
                logger.error("No se encontró configuración de InstagramAPI.")

        else:
            logger.error(f"Plataforma desconocida: {platform}")

    except Exception as e:
        logger.error(f"Error enviando mensaje en {platform}: {e}", exc_info=True)

# Mover importaciones dentro de las funciones para evitar referencias circulares
async def send_logo(platform, user_id):
    try:
        configuracion = await ConfiguracionBU.objects.afirst()
        image_url = configuracion.logo_url if configuracion else "https://amigro.org/logo.png"

        if platform == 'whatsapp':
            whatsapp_api = await WhatsAppAPI.objects.afirst()
            if whatsapp_api:
                from app.integrations.whatsapp import send_whatsapp_message
                await send_whatsapp_message(
                    user_id,
                    '',
                    whatsapp_api.api_token,
                    whatsapp_api.phoneID,
                    whatsapp_api.v_api,
                    image_url=image_url,
                )
            else:
                logger.error("No se encontró configuración de WhatsAppAPI.")

        elif platform == 'messenger':
            messenger_api = await MessengerAPI.objects.afirst()
            if messenger_api:
                from app.integrations.messenger import send_messenger_image
                await send_messenger_image(
                    user_id, image_url, messenger_api.page_access_token
                )
            else:
                logger.error("No se encontró configuración de MessengerAPI.")

        else:
            logger.error(f"Envío de imágenes no soportado para la plataforma {platform}")

    except Exception as e:
        logger.error(f"Error enviando imagen en {platform}: {e}", exc_info=True)

async def send_image(platform, user_id, image_url):
    try:
        if platform == 'whatsapp':
            whatsapp_api = await WhatsAppAPI.objects.afirst()
            if whatsapp_api:
                from app.integrations.whatsapp import send_whatsapp_message
                await send_whatsapp_message(
                    user_id,
                    '',
                    whatsapp_api.api_token,
                    whatsapp_api.phoneID,
                    whatsapp_api.v_api,
                    image_url=image_url,
                )
            else:
                logger.error("No se encontró configuración de WhatsAppAPI.")

        elif platform == 'messenger':
            messenger_api = await MessengerAPI.objects.afirst()
            if messenger_api:
                from app.integrations.messenger import send_messenger_image
                await send_messenger_image(
                    user_id, image_url, messenger_api.page_access_token
                )
            else:
                logger.error("No se encontró configuración de MessengerAPI.")

        else:
            logger.error(f"Envío de imágenes no soportado para la plataforma {platform}")

    except Exception as e:
        logger.error(f"Error enviando imagen en {platform}: {e}", exc_info=True)

async def send_menu(platform, user_id):
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
            whatsapp_api = await WhatsAppAPI.objects.afirst()
            if whatsapp_api:
                from app.integrations.whatsapp import send_whatsapp_message
                await send_whatsapp_message(
                    user_id,
                    menu_message,
                    whatsapp_api.api_token,
                    whatsapp_api.phoneID,
                    whatsapp_api.v_api,
                )
            else:
                logger.error("No se encontró configuración de WhatsAppAPI.")

        elif platform == 'telegram':
            telegram_api = await TelegramAPI.objects.afirst()
            if telegram_api:
                from app.integrations.telegram import send_telegram_message
                await send_telegram_message(user_id, menu_message, telegram_api.api_key)
            else:
                logger.error("No se encontró configuración de TelegramAPI.")

        elif platform == 'messenger':
            messenger_api = await MessengerAPI.objects.afirst()
            if messenger_api:
                from app.integrations.messenger import send_messenger_message
                await send_messenger_message(
                    user_id, menu_message, messenger_api.page_access_token
                )
            else:
                logger.error("No se encontró configuración de MessengerAPI.")

        elif platform == 'instagram':
            instagram_api = await InstagramAPI.objects.afirst()
            if instagram_api:
                from app.integrations.instagram import send_instagram_message
                await send_instagram_message(
                    user_id, menu_message, instagram_api.access_token
                )
            else:
                logger.error("No se encontró configuración de InstagramAPI.")

        else:
            logger.error(f"Plataforma desconocida: {platform}")

    except Exception as e:
        logger.error(f"Error enviando el menú a través de {platform}: {e}", exc_info=True)

async def send_options(platform, user_id, message, buttons=None):
    try:
        if platform == 'whatsapp':
            whatsapp_api = await WhatsAppAPI.objects.afirst()
            if whatsapp_api and buttons:
                from app.integrations.whatsapp import send_whatsapp_buttons
                button_options = [
                    {
                        'type': 'reply',
                        'reply': {'id': str(i), 'title': button.name},
                    }
                    for i, button in enumerate(buttons)
                ]
                await send_whatsapp_buttons(
                    user_id,
                    message,
                    button_options,
                    whatsapp_api.api_token,
                    whatsapp_api.phoneID,
                    whatsapp_api.v_api,
                )
            else:
                logger.error("No se encontró configuración de WhatsAppAPI o botones.")

        elif platform == 'telegram':
            telegram_api = await TelegramAPI.objects.afirst()
            if telegram_api and buttons:
                from app.integrations.telegram import send_telegram_buttons
                telegram_buttons = [
                    [{'text': button.name, 'callback_data': button.name}]
                    for button in buttons
                ]
                await send_telegram_buttons(
                    user_id, message, telegram_buttons, telegram_api.api_key
                )
            else:
                logger.error("No se encontró configuración de TelegramAPI o botones.")

        elif platform == 'messenger':
            messenger_api = await MessengerAPI.objects.afirst()
            if messenger_api and buttons:
                from app.integrations.messenger import send_messenger_quick_replies
                quick_reply_options = [
                    {'content_type': 'text', 'title': button.name, 'payload': button.name}
                for button in buttons
                ]
                await send_messenger_quick_replies(
                    user_id,
                    message,
                    quick_reply_options,
                    messenger_api.page_access_token,
                )
            else:
                logger.error("No se encontró configuración de MessengerAPI o botones.")

        elif platform == 'instagram':
            instagram_api = await InstagramAPI.objects.afirst()
            if instagram_api and buttons:
                from app.integrations.instagram import send_instagram_message
                options_text = "\n".join(
                    [f"{idx + 1}. {button.name}" for idx, button in enumerate(buttons)]
                )
                message_with_options = f"{message}\n\nOpciones:\n{options_text}"
                await send_instagram_message(
                    user_id, message_with_options, instagram_api.access_token
                )
            else:
                logger.error("No se encontró configuración de InstagramAPI o botones.")

        else:
            logger.error(f"Plataforma desconocida para envío de opciones: {platform}")

    except Exception as e:
        logger.error(f"Error enviando opciones a través de {platform}: {e}", exc_info=True)

def render_dynamic_content(template_text, context):
    """
    Renderiza el contenido dinámico de un mensaje utilizando un texto de plantilla y un contexto de variables.

    :param template_text: Texto de plantilla que contiene las variables a reemplazar.
    :param context: Diccionario con variables para reemplazar en la plantilla.
    :return: Texto renderizado con el contenido dinámico.
    """
    try:
        # Reemplazar variables en el texto de plantilla usando `str.format`
        content = template_text.format(**context)
        return content
    except KeyError as e:
        logger.error(f"Error al renderizar contenido dinámico: Variable faltante {e}")
        return template_text  # Retornar el texto original en caso de error

def notify_employer(worker, message):
    try:
        if worker.whatsapp:
            whatsapp_api = WhatsAppAPI.objects.first()
            if whatsapp_api:
                from app.integrations.whatsapp import send_whatsapp_message
                send_whatsapp_message(
                    worker.whatsapp,
                    message,
                    whatsapp_api.api_token,
                    whatsapp_api.phoneID,
                    whatsapp_api.v_api,
                )
                logger.info(f"Notificación enviada al empleador {worker.name}.")
            else:
                logger.error("No se encontró configuración de WhatsAppAPI.")
        else:
            logger.warning(f"El empleador {worker.name} no tiene número de WhatsApp configurado.")

    except Exception as e:
        logger.error(f"Error enviando notificación al empleador {worker.name}: {e}", exc_info=True)

async def process_text_message(platform, sender_id, message_text):
    from app.chatbot import ChatBotHandler  # Mover importación dentro de la función
    chatbot_handler = ChatBotHandler()

    try:
        if platform == 'whatsapp':
            whatsapp_api = await WhatsAppAPI.objects.afirst()
            if whatsapp_api:
                business_unit = whatsapp_api.business_unit
                await chatbot_handler.process_message(
                    platform, sender_id, message_text, business_unit
                )
            else:
                logger.error("No se encontró configuración de WhatsAppAPI.")

        # Agregar lógica similar para otras plataformas si es necesario

    except Exception as e:
        logger.error(f"Error procesando mensaje de texto: {e}", exc_info=True)
