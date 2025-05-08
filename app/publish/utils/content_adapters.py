from typing import Dict, Any
import re

class ContentAdapter:
    """
    Adaptador base para contenido
    """
    def __init__(self, content: Dict[str, Any]):
        self.content = content
        
    def adapt(self) -> Dict[str, Any]:
        """
        Adapta el contenido para el canal específico
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")

class WhatsAppAdapter(ContentAdapter):
    """
    Adaptador para WhatsApp
    """
    def adapt(self) -> Dict[str, Any]:
        """
        Adapta el contenido para WhatsApp
        """
        adapted = {
            'text': self._truncate_text(self.content.get('text', '')),
            'media': self._filter_media(self.content.get('media', [])),
            'metadata': self.content.get('metadata', {})
        }
        return adapted
    
    def _truncate_text(self, text: str) -> str:
        """
        Trunca el texto para que no supere el límite de WhatsApp
        """
        return text[:1000] if text else ''
    
    def _filter_media(self, media: list) -> list:
        """
        Filtra los medios para que no supere el límite de WhatsApp
        """
        return media[:5] if media else []

class TelegramAdapter(ContentAdapter):
    """
    Adaptador para Telegram
    """
    def adapt(self) -> Dict[str, Any]:
        """
        Adapta el contenido para Telegram
        """
        adapted = {
            'text': self._format_markdown(self.content.get('text', '')),
            'media': self._filter_media(self.content.get('media', [])),
            'metadata': self.content.get('metadata', {})
        }
        return adapted
    
    def _format_markdown(self, text: str) -> str:
        """
        Formatea el texto para Markdown de Telegram
        """
        text = text.replace('*', '\*')  # Escape asterisks
        text = text.replace('_', '\_')  # Escape underscores
        return text
    
    def _filter_media(self, media: list) -> list:
        """
        Filtra los medios para que no supere el límite de Telegram
        """
        return media[:10] if media else []

class SocialMediaAdapter(ContentAdapter):
    """
    Adaptador para redes sociales
    """
    def adapt(self) -> Dict[str, Any]:
        """
        Adapta el contenido para redes sociales
        """
        adapted = {
            'text': self._format_social(self.content.get('text', '')),
            'media': self._filter_media(self.content.get('media', [])),
            'metadata': self.content.get('metadata', {})
        }
        return adapted
    
    def _format_social(self, text: str) -> str:
        """
        Formatea el texto para redes sociales
        """
        # Agregar hashtags relevantes
        hashtags = self._generate_hashtags()
        return f"{text} {hashtags}"
    
    def _generate_hashtags(self) -> str:
        """
        Genera hashtags relevantes
        """
        hashtags = [
            '#Empleo',
            '#Trabajo',
            '#Oportunidades',
            '#RecursosHumanos'
        ]
        return ' '.join(hashtags)
    
    def _filter_media(self, media: list) -> list:
        """
        Filtra los medios para redes sociales
        """
        return media[:4] if media else []

def get_adapter(channel_type: str) -> ContentAdapter:
    """
    Obtiene el adaptador apropiado para el tipo de canal
    """
    adapters = {
        'WHATSAPP_GROUP': WhatsAppAdapter,
        'WHATSAPP_BROADCAST': WhatsAppAdapter,
        'TELEGRAM_CHANNEL': TelegramAdapter,
        'TELEGRAM_BOT': TelegramAdapter,
        'X_PROFILE': SocialMediaAdapter,
        'INSTAGRAM_PROFILE': SocialMediaAdapter,
        'LINKEDIN_PROFILE': SocialMediaAdapter
    }
    
    AdapterClass = adapters.get(channel_type)
    if not AdapterClass:
        raise ValueError(f"No se encontró adaptador para el canal: {channel_type}")
    
    return AdapterClass
