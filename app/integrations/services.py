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
from app.integrations.instagram import send_instagram_message, send_instagram_quick_replies

logger = logging.getLogger(__name__)

def handle_message(user_id, message_text, platform):
    """
    Procesa el mensaje recibido y determina la respuesta adecuada.
    """
    logger.info(f"Procesando mensaje de {platform}: {message_text}")
    
    # Obtener o crear el estado del chat
    chat_state, created = ChatState.objects.get_or_create(user_id=user_id, platform=platform)
    
    if not chat_state.current_question:
        # Iniciar conversación si no hay pregunta actual
        primera_pregunta = Pregunta.objects.filter(active=True).first()
        if primera_pregunta:
            chat_state.current_question = primera_pregunta
            chat_state.save()
            respuesta = f"Bienvenido a Amigro.org. {primera_pregunta.name}"
            send_message(platform, user_id, respuesta)
            return
    
    # Aquí puedes implementar la lógica para manejar las respuestas del usuario
    # Por ejemplo, avanzar a la siguiente pregunta según la respuesta
    # Esto dependerá de cómo esté estructurada tu lógica de preguntas y respuestas
    
    # Ejemplo simplificado:
    siguiente_pregunta = get_next_question(user_id, platform)
    if siguiente_pregunta:
        respuesta = siguiente_pregunta.name
        chat_state.current_question = siguiente_pregunta
        chat_state.save()
        send_message(platform, user_id, respuesta)
    else:
        respuesta = "Gracias por tu tiempo. Si necesitas más ayuda, no dudes en contactarnos."
        send_message(platform, user_id, respuesta)
        chat_state.delete()

def send_message(platform, user_id, message_text):
    """
    Envía un mensaje a través de la plataforma especificada.
    """
    if platform == 'instagram':
        instagram_api = InstagramAPI.objects.first()
        if instagram_api:
            send_instagram_message(user_id, message_text, instagram_api.access_token)
        else:
            logger.error("No se encontró configuración de API de Instagram")
    # Aquí puedes manejar otras plataformas de manera similar
