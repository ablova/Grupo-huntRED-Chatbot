import asyncio
from typing import Callable, Dict, Any, Optional
from functools import wraps
import logging
from aapp.com.chatbot.components.channel_config import ChannelConfig

logger = logging.getLogger(__name__)

class MessageRetry:
    @staticmethod
    def with_retry(platform: str):
        """Decorator para manejar reintentos de mensajes."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                config = ChannelConfig.get_config()[platform]
                attempts = config['retry_attempts']
                delay = config['retry_delay']
                
                for attempt in range(attempts):
                    try:
                        result = await func(*args, **kwargs)
                        if result:
                            return result
                    except Exception as e:
                        logger.error(f"Error sending message on attempt {attempt + 1}: {str(e)}")
                        
                        if attempt < attempts - 1:
                            await asyncio.sleep(delay)
                            logger.info(f"Retrying message in {delay} seconds...")
                        else:
                            logger.error(f"Failed to send message after {attempts} attempts")
                            
                            # Intentar con el canal de fallback
                            fallback_channel = config['fallback_channel']
                            if fallback_channel != platform:
                                logger.info(f"Switching to fallback channel: {fallback_channel}")
                                # Aquí iría la lógica para enviar al canal de fallback
                                pass
                            
                            raise
                
                return None
            return wrapper
        return decorator

    @staticmethod
    async def process_batch(platform: str, messages: list):
        """Procesa un lote de mensajes con control de rate limit."""
        config = ChannelConfig.get_config()[platform]
        batch_size = config['batch_size']
        rate_limit = config['rate_limit']
        
        # Dividir en lotes
        batches = [messages[i:i + batch_size] for i in range(0, len(messages), batch_size)]
        
        for batch in batches:
            # Procesar cada mensaje con retry
            for message in batch:
                await MessageRetry.with_retry(platform)(message.send)()
                
            # Esperar según el rate limit
            await asyncio.sleep(60 / rate_limit)

    @staticmethod
    def validate_message(platform: str, message: Dict[str, Any]) -> bool:
        """Valida que el mensaje cumpla con las restricciones del canal."""
        config = ChannelConfig.get_config()[platform]
        
        # Validar longitud
        if len(str(message.get('text', ''))) > config['max_message_length']:
            logger.warning(f"Message too long for {platform}")
            return False
            
        # Validar tipo de contenido
        if message.get('media') and not config['media_supported']:
            logger.warning(f"Media not supported in {platform}")
            return False
            
        return True
