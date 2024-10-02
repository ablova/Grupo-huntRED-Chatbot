# /home/amigro/app/integrations/services.py

import logging
from app.models import (
    WhatsAppAPI,
    TelegramAPI,
    MessengerAPI,
    InstagramAPI,
    MetaAPI,
    Pregunta,
    ChatState,
)

logger = logging.getLogger(__name__)

# Maneja las opciones de menú del chatbot para diferentes acciones
def handle_menu_option(user_id, option, platform):
    if option == "reinicio":
        reset_chat_state(user_id, platform)
        return (
            "Bienvenido de nuevo a Amigro.org. ¿Cómo puedo ayudarte?",
            get_welcome_message(),
        )
    elif option == "registro":
        return "Vamos a comenzar tu registro. ¿Cuál es tu nombre completo?", None
    elif option == "vacantes":
        return (
            "Aquí tienes nuestras vacantes disponibles: https://amigro.org/browse-jobs-map/",
            None,
        )
    elif option == "actualizar":
        return (
            "Vamos a actualizar tus datos. ¿Qué información deseas modificar?",
            None,
        )
    elif option == "invitar":
        return (
            "Invita a tus amigos a unirse a Amigro.org: https://amigro.org/invitar",
            None,
        )
    elif option == "terminos":
        send_logo(platform, user_id)  # Envía el logo al usuario
        return "Aquí están nuestros términos y condiciones: https://amigro.org/tos", None
    elif option == "contacto":
        return "Contáctanos en: https://amigro.org/contact", None
    else:
        return "Opción no válida. Por favor, elige una opción del menú.", get_welcome_message()

# Restablece el estado del chat para el usuario
def reset_chat_state(user_id, platform):
    ChatState.objects.filter(user_id=user_id, platform=platform).delete()
    welcome_message = "¡Bienvenido de nuevo a Amigro.org!"
    send_message(platform, user_id, welcome_message)

# Envía un mensaje dependiendo de la plataforma
def send_message(platform, recipient, message):
    if platform == 'whatsapp':
        whatsapp_api = WhatsAppAPI.objects.first()
        if whatsapp_api:
            from app.integrations.whatsapp import send_whatsapp_message  # Importar dentro de la función
            send_whatsapp_message.delay(
                recipient, message, whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api
            )
        else:
            logger.error("No se encontró configuración de API de WhatsApp")
    elif platform == 'telegram':
        telegram_api = TelegramAPI.objects.first()
        if telegram_api:
            from app.integrations.telegram import send_telegram_message  # Importar dentro de la función
            send_telegram_message.delay(recipient, message, telegram_api.api_key)
        else:
            logger.error("No se encontró configuración de API de Telegram")
    elif platform == 'messenger':
        messenger_api = MessengerAPI.objects.first()
        if messenger_api:
            from app.integrations.messenger import send_messenger_message  # Importar dentro de la función
            send_messenger_message.delay(recipient, message, messenger_api.page_access_token)
        else:
            logger.error("No se encontró configuración de API de Messenger")
    elif platform == 'instagram':
        instagram_api = InstagramAPI.objects.first()
        if instagram_api:
            from app.integrations.instagram import send_instagram_message  # Importar dentro de la función
            send_instagram_message(recipient, message, instagram_api.access_token)
        else:
            logger.error("No se encontró configuración de API de Instagram")
    else:
        logger.error(f"Plataforma desconocida: {platform}")

# Enviar opciones como botones en la plataforma correspondiente
def send_options(platform, user_id, message):
    if platform == 'telegram':
        options = [
            [{"text": "Sí", "callback_data": "yes"}, {"text": "No", "callback_data": "no"}],
            [{"text": "Hombre", "callback_data": "male"}, {"text": "Mujer", "callback_data": "female"}],
        ]
        telegram_api = TelegramAPI.objects.first()
        if telegram_api:
            bot_token = telegram_api.api_key
            from app.integrations.telegram import send_telegram_message_with_buttons  # Importar dentro de la función
            send_telegram_message_with_buttons.delay(user_id, message, bot_token, options)
        else:
            logger.error("No se encontró configuración de API de Telegram")

    elif platform == 'whatsapp':
        options = [
            {"type": "reply", "reply": {"id": "yes", "title": "Sí"}},
            {"type": "reply", "reply": {"id": "no", "title": "No"}},
            {"type": "reply", "reply": {"id": "male", "title": "Hombre"}},
            {"type": "reply", "reply": {"id": "female", "title": "Mujer"}},
        ]
        whatsapp_api = WhatsAppAPI.objects.first()
        if whatsapp_api:
            from app.integrations.whatsapp import send_whatsapp_buttons  # Importar dentro de la función
            send_whatsapp_buttons.delay(
                user_id,
                message,
                options,
                whatsapp_api.api_token,
                whatsapp_api.phoneID,
                whatsapp_api.v_api,
            )
        else:
            logger.error("No se encontró configuración de API de WhatsApp")

    elif platform == 'messenger':
        options = [
            {"content_type": "text", "title": "Sí", "payload": "yes"},
            {"content_type": "text", "title": "No", "payload": "no"},
            {"content_type": "text", "title": "Hombre", "payload": "male"},
            {"content_type": "text", "title": "Mujer", "payload": "female"},
        ]
        messenger_api = MessengerAPI.objects.first()
        if messenger_api:
            from app.integrations.messenger import send_messenger_quick_replies  # Importar dentro de la función
            send_messenger_quick_replies.delay(
                user_id, message, options, messenger_api.page_access_token
            )
        else:
            logger.error("No se encontró configuración de API de Messenger")
    
    elif platform == 'instagram':
        options = [
            {"title": "Sí", "payload": "yes"},
            {"title": "No", "payload": "no"},
            {"title": "Hombre", "payload": "male"},
            {"title": "Mujer", "payload": "female"},
        ]
        instagram_api = InstagramAPI.objects.first()
        if instagram_api:
            from app.integrations.instagram import send_instagram_quick_replies  # Importar dentro de la función
            send_instagram_quick_replies.delay(
                user_id, message, options, instagram_api.access_token
            )
        else:
            logger.error("No se encontró configuración de API de Instagram")
    else:
        logger.error(f"Plataforma desconocida: {platform}")

# Obtiene la siguiente pregunta del flujo de preguntas
def get_next_question(user_id, platform):
    chat_state = ChatState.objects.filter(user_id=user_id, platform=platform).first()

    if not chat_state:
        primera_pregunta = Pregunta.objects.filter(active=True).first()
        if primera_pregunta:
            ChatState.objects.create(
                user_id=user_id, platform=platform, current_question=primera_pregunta
            )
            return (
                f"Bienvenido a Amigro.org, {primera_pregunta.name}, ¿Conoces algo de lo que hacemos?",
                primera_pregunta,
            )
        return "No hay preguntas disponibles en este momento.", None

    current_question = chat_state.current_question
    siguiente_pregunta = (
        Pregunta.objects.filter(id__gt=current_question.id, active=True)
        .order_by('id')
        .first()
    )

    if siguiente_pregunta:
        chat_state.current_question = siguiente_pregunta
        chat_state.save()
        return siguiente_pregunta.name, siguiente_pregunta

    return "Gracias por responder todas las preguntas.", None

# Función para enviar el logo (opcional)
def send_logo(platform, recipient):
    """
    Envía el logo a través de la plataforma seleccionada.
    """
    logo_link = "https://amigro.org/logo.png"

    if platform == 'whatsapp':
        whatsapp_api = WhatsAppAPI.objects.first()
        if whatsapp_api:
            from app.integrations.whatsapp import send_whatsapp_message  # Importar dentro de la función
            send_whatsapp_message.delay(
                recipient,
                f"Aquí está nuestro logo: {logo_link}",
                whatsapp_api.api_token,
                whatsapp_api.phoneID,
                whatsapp_api.v_api,
            )
        else:
            logger.error("No se encontró configuración de API de WhatsApp")
    elif platform == 'telegram':
        telegram_api = TelegramAPI.objects.first()
        if telegram_api:
            from app.integrations.telegram import send_telegram_photo  # Importar dentro de la función
            send_telegram_photo.delay(recipient, logo_link, telegram_api.api_key)
        else:
            logger.error("No se encontró configuración de API de Telegram")
    elif platform == 'messenger':
        messenger_api = MessengerAPI.objects.first()
        if messenger_api:
            from app.integrations.messenger import send_messenger_image  # Importar dentro de la función
            send_messenger_image.delay(recipient, logo_link, messenger_api.page_access_token)
        else:
            logger.error("No se encontró configuración de API de Messenger")
    elif platform == 'instagram':
        instagram_api = InstagramAPI.objects.first()
        if instagram_api:
            from app.integrations.instagram import send_instagram_image  # Importar dentro de la función
            send_instagram_image(recipient, logo_link, instagram_api.access_token)
        else:
            logger.error("No se encontró configuración de API de Instagram")
    else:
        logger.error(f"Plataforma no reconocida para enviar logo: {platform}")

# Mensaje de bienvenida
def get_welcome_message():
    return """  
Al continuar aceptas nuestros términos y condiciones, si gustas conocerlos los puedes revisar en https://amigro.org/tos
Por favor, elige una opción:
[1] Iniciar conversación / Conoce Amigro.org
[2] Registro
[3] Ver vacantes
[4] Actualizar datos
[5] Invitar o compartir a Amigro.org
[6] Términos, condiciones & Política de Privacidad
[7] Contacto
[8] Salir
"""

# Maneja mensajes entrantes
def handle_message(user_id, message_text, platform):
    # Procesa el mensaje y genera una respuesta
    # Aquí puedes implementar la lógica para manejar el mensaje
    respuesta, siguiente_pregunta = get_next_question(user_id, platform)
    # Envía la respuesta al usuario
    send_message(platform, user_id, respuesta)

# Maneja mensajes de Instagram (opcional, ya que handle_message ya cubre todas las plataformas)
def handle_instagram_message(sender_id, message_text):
    handle_message(sender_id, message_text, 'instagram')
