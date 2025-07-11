# app/ats/publish/processors/__init__.py
"""
Módulo de procesadores para canales de publicación.
"""

from .base_processor import BaseProcessor
import logging

logger = logging.getLogger(__name__)

def get_processor(channel_type: str) -> BaseProcessor:
    """
    Obtiene el procesador específico para un tipo de canal.
    
    Args:
        channel_type: Tipo de canal (TELEGRAM_BOT, WHATSAPP_BROADCAST, etc.)
        
    Returns:
        Instancia del procesador correspondiente
    """
    try:
        # Por ahora, retornamos el procesador base
        # En el futuro, aquí se implementaría la lógica para obtener
        # el procesador específico según el tipo de canal
        return BaseProcessor()
    except Exception as e:
        logger.error(f"Error obteniendo procesador para canal {channel_type}: {e}")
        return None 