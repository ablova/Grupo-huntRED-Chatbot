# /home/pablo/app/com/chatbot/middleware/message_retry.py
import asyncio
from typing import Callable, Dict, Any, Optional
from functools import wraps
import logging
from datetime import datetime, timedelta
import importlib
from django.conf import settings
from asgiref.sync import sync_to_async
from app.com.chatbot.components.channel_config import ChannelConfig

logger = logging.getLogger(__name__)

class MessageRetry:
    """
    Middleware para manejo de reintentos y referencias circulares.
    
    Proporciona mecanismos para:
    - Reintentar mensajes fallidos
    - Resolver dependencias circulares
    - Gestionar cola de mensajes
    - Validar mensajes por plataforma
    """
    
    def __init__(self):
        self.max_retries = getattr(settings, 'MESSAGE_MAX_RETRIES', 3)
        self.retry_delay = getattr(settings, 'MESSAGE_RETRY_DELAY', 5)  # segundos
        self.pending_messages = {}
        self.circular_deps = {}
    
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

    async def process_message(self, message: Dict, handler: Any) -> bool:
        """
        Procesa un mensaje con manejo de reintentos.
        
        Args:
            message: Mensaje a procesar
            handler: Manejador del mensaje
            
        Returns:
            bool indicando éxito
        """
        message_id = message.get('id')
        if not message_id:
            logger.error("Mensaje sin ID")
            return False
            
        retry_count = self.pending_messages.get(message_id, {}).get('retry_count', 0)
        
        try:
            # Intentar procesar el mensaje
            result = await handler.process(message)
            
            # Si fue exitoso, remover de pendientes
            if message_id in self.pending_messages:
                del self.pending_messages[message_id]
                
            return result
            
        except Exception as e:
            logger.error(f"Error procesando mensaje {message_id}: {str(e)}")
            
            # Verificar si debemos reintentar
            if retry_count < self.max_retries:
                # Programar reintento
                await self._schedule_retry(message_id, message, handler)
                return False
            else:
                # Máximo de reintentos alcanzado
                logger.error(f"Máximo de reintentos alcanzado para mensaje {message_id}")
                return False
    
    async def _schedule_retry(self, message_id: str, message: Dict, handler: Any):
        """Programa un reintento para un mensaje fallido."""
        retry_count = self.pending_messages.get(message_id, {}).get('retry_count', 0) + 1
        
        self.pending_messages[message_id] = {
            'message': message,
            'handler': handler,
            'retry_count': retry_count,
            'next_retry': datetime.now() + timedelta(seconds=self.retry_delay)
        }
        
        # Programar reintento
        asyncio.create_task(self._retry_message(message_id))
    
    async def _retry_message(self, message_id: str):
        """Ejecuta un reintento programado."""
        await asyncio.sleep(self.retry_delay)
        
        if message_id in self.pending_messages:
            message_data = self.pending_messages[message_id]
            await self.process_message(message_data['message'], message_data['handler'])
    
    def resolve_circular_dependency(self, module_name: str) -> Any:
        """
        Resuelve una dependencia circular en importaciones.
        
        Args:
            module_name: Nombre del módulo a importar
            
        Returns:
            Módulo importado
        """
        if module_name in self.circular_deps:
            return self.circular_deps[module_name]
            
        try:
            module = importlib.import_module(module_name)
            self.circular_deps[module_name] = module
            return module
        except ImportError as e:
            logger.error(f"Error importando módulo {module_name}: {str(e)}")
            return None
    
    async def cleanup_pending_messages(self):
        """Limpia mensajes pendientes antiguos."""
        now = datetime.now()
        expired_messages = [
            msg_id for msg_id, data in self.pending_messages.items()
            if now > data['next_retry'] + timedelta(minutes=30)
        ]
        
        for msg_id in expired_messages:
            del self.pending_messages[msg_id]
            logger.info(f"Mensaje {msg_id} expirado y removido")
    
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
