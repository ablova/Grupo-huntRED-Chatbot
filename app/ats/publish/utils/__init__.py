# app/ats/publish/utils/__init__.py
"""
Utilidades para el módulo de publicación.
"""

from .content_adapters import ContentAdapter
import logging

logger = logging.getLogger(__name__)

def get_channel_processor(channel_type: str) -> ContentAdapter:
    """
    Obtiene el procesador específico para un tipo de canal.
    
    Args:
        channel_type: Tipo de canal (TELEGRAM_BOT, WHATSAPP_BROADCAST, etc.)
        
    Returns:
        Instancia del procesador correspondiente
    """
    try:
        # Por ahora, retornamos el adaptador de contenido base
        # En el futuro, aquí se implementaría la lógica para obtener
        # el procesador específico según el tipo de canal
        return ContentAdapter()
    except Exception as e:
        logger.error(f"Error obteniendo procesador para canal {channel_type}: {e}")
        return None 