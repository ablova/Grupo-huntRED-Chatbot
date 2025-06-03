# Configuración de enlaces y mensajes de invitación al chatbot

CHATBOT_INVITE_CONFIG = {
    'whatsapp': {
        'invite_link': 'https://wa.me/525518490291',  # Enlace de WhatsApp
        'message': (
            "¡Hola! Soy el asistente de Grupo huntRED®. Estoy aquí para ayudarte en tu proceso de reclutamiento."
            "\n\n¿Necesitas más información sobre la vacante? ¿Te gustaría programar una entrevista?"
            "\n\nEscríbeme y estaré encantado de ayudarte."
        )
    },
    'telegram': {
        'invite_link': 'https://t.me/huntred_bot',  # Enlace de Telegram
        'message': (
            "¡Hola! Soy el asistente de Grupo huntRED® en Telegram."
            "\n\n¿Necesitas más información sobre la vacante? ¿Te gustaría programar una entrevista?"
            "\n\nEscríbeme y estaré encantado de ayudarte."
        )
    }
}

# Función para obtener el mensaje de invitación formateado
def get_chatbot_invite_message(platform):
    """
    Obtiene el mensaje de invitación formateado para una plataforma específica
    
    Args:
        platform (str): Plataforma ('whatsapp' o 'telegram')
        
    Returns:
        str: Mensaje de invitación formateado
    """
    if platform not in CHATBOT_INVITE_CONFIG:
        return ""
    
    config = CHATBOT_INVITE_CONFIG[platform]
    return f"""
¡Hola! Para más información sobre esta vacante, te invito a contactarme a través de nuestro chatbot:

{config['message']}

Puedes encontrarme en: {config['invite_link']}
"""
