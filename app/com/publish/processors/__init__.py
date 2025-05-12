from .base_processor import BaseProcessor
from .whatsapp_processor import WhatsAppProcessor
from .telegram_processor import TelegramProcessor

def get_processor(channel_type: str) -> BaseProcessor:
    """
    Obtiene el procesador apropiado para el tipo de canal
    """
    processors = {
        'WHATSAPP_GROUP': WhatsAppProcessor,
        'WHATSAPP_BROADCAST': WhatsAppProcessor,
        'TELEGRAM_CHANNEL': TelegramProcessor,
        'TELEGRAM_BOT': TelegramProcessor,
        # Agregar más procesadores aquí
    }
    
    ProcessorClass = processors.get(channel_type)
    if not ProcessorClass:
        raise ValueError(f"No se encontró procesador para el canal: {channel_type}")
    
    return ProcessorClass
