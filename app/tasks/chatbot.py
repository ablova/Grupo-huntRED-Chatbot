"""
Tareas asíncronas relacionadas con el módulo de Chatbot.
Este módulo centraliza todas las tareas de procesamiento conversacional,
integración con canales y análisis de mensajes.
"""
from celery import shared_task
import logging
from django.conf import settings
from django.core.cache import cache
import asyncio
import time
from asgiref.sync import async_to_sync
import json

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_kwargs={'max_retries': 5},
    queue='chatbot'
)
def process_message(self, user_id, message, channel, metadata=None):
    """
    Procesa un mensaje recibido por cualquier canal del chatbot.
    
    Args:
        user_id (str): ID del usuario que envía el mensaje
        message (str): Contenido del mensaje
        channel (str): Canal por el que se recibió (whatsapp, telegram, etc)
        metadata (dict): Datos adicionales relacionados con el mensaje
        
    Returns:
        dict: Resultado del procesamiento con la respuesta generada
    """
    from app.ats.chatbot.chatbot import ChatBot
    
    logger.info(f"Processing message from user {user_id} via {channel}")
    start_time = time.time()
    
    try:
        # Procesar mensaje de forma asíncrona
        chatbot = ChatBot()
        result = async_to_sync(chatbot.process_message)(user_id, message, channel, metadata)
        
        # Registrar métricas de rendimiento
        processing_time = time.time() - start_time
        async_to_sync(register_performance_metric)('chatbot_processing_time', processing_time, 
                                                   {'user_id': user_id, 'channel': channel})
        
        return result
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
    queue='chatbot'
)
def analyze_intent(self, message, user_id, context=None):
    """
    Analiza la intención del mensaje del usuario.
    
    Args:
        message (str): Mensaje a analizar
        user_id (str): ID del usuario
        context (dict): Contexto previo de la conversación
        
    Returns:
        dict: Intención detectada y confianza
    """
    from app.ats.chatbot.intents_handler import IntentsHandler
    
    logger.info(f"Analyzing intent for user {user_id}")
    
    try:
        handler = IntentsHandler()
        return async_to_sync(handler.analyze_intent)(message, user_id, context)
    except Exception as e:
        logger.error(f"Error analyzing intent: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
    queue='chatbot'
)
def generate_response(self, user_id, intent, message, context=None):
    """
    Genera una respuesta basada en la intención detectada.
    
    Args:
        user_id (str): ID del usuario
        intent (dict): Intención detectada
        message (str): Mensaje original
        context (dict): Contexto de la conversación
        
    Returns:
        dict: Respuesta generada
    """
    from app.ats.chatbot.response_generator import ResponseGenerator
    
    logger.info(f"Generating response for user {user_id} with intent {intent.get('name', 'unknown')}")
    
    try:
        generator = ResponseGenerator()
        return async_to_sync(generator.generate)(user_id, intent, message, context)
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(queue='maintenance')
def retry_failed_messages():
    """
    Reintenta enviar mensajes que fallaron previamente.
    Esta tarea se ejecuta periódicamente.
    """
    from app.ats.chatbot.middleware.message_retry import MessageRetryManager
    
    logger.info("Starting retry of failed messages")
    
    try:
        retry_manager = MessageRetryManager()
        result = async_to_sync(retry_manager.process_pending_retries)()
        
        logger.info(f"Processed {result.get('processed', 0)} retries, "
                   f"successful: {result.get('successful', 0)}, "
                   f"failed: {result.get('failed', 0)}")
        
        return result
    except Exception as e:
        logger.error(f"Error in retry_failed_messages: {str(e)}", exc_info=True)
        raise


async def register_performance_metric(metric_name, value, tags=None):
    """
    Registra una métrica de rendimiento en Redis para análisis posterior.
    
    Args:
        metric_name (str): Nombre de la métrica
        value (float): Valor de la métrica
        tags (dict): Etiquetas para segmentar la métrica
    """
    tags = tags or {}
    timestamp = int(time.time())
    
    # Almacenar en Redis para análisis en tiempo real
    metric_key = f"metrics:{metric_name}:{timestamp}"
    metric_data = {
        "value": value,
        "timestamp": timestamp,
        "tags": tags
    }
    
    await cache.aset(metric_key, json.dumps(metric_data), timeout=86400)  # Expirar en 24 horas
    
    # Actualizar contadores para promedios
    avg_key = f"metrics:avg:{metric_name}"
    count_key = f"metrics:count:{metric_name}"
    
    current_avg = await cache.aget(avg_key) or 0
    current_count = await cache.aget(count_key) or 0
    
    # Actualizar promedio móvil
    new_count = current_count + 1
    new_avg = ((current_avg * current_count) + value) / new_count
    
    await cache.aset(avg_key, new_avg, timeout=86400)
    await cache.aset(count_key, new_count, timeout=86400)
