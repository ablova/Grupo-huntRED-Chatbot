from app.publish.utils.content_adapters import ContentAdapter, WhatsAppAdapter, TelegramAdapter, SocialMediaAdapter
from app.publish.utils.content_adapters import get_adapter

def get_content_adapter(channel_type: str) -> ContentAdapter:
    """
    Obtiene el adaptador de contenido apropiado para el tipo de canal
    """
    return get_adapter(channel_type)
