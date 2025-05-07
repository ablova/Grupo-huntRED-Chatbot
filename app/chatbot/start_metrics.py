import asyncio
import logging
from ai_huntred.settings import CHATBOT_CONFIG
from app.chatbot.metrics import chatbot_metrics

logger = logging.getLogger(__name__)

def start_metrics_collection():
    """Inicia la recolección de métricas del chatbot."""
    logger.info("Iniciando recolección de métricas del chatbot...")
    
    # Configurar intervalo de recolección
    chatbot_metrics.collection_interval = CHATBOT_CONFIG['METRICS_COLLECTION_INTERVAL']
    
    # Iniciar recolección
    asyncio.run(chatbot_metrics.collect_metrics())

if __name__ == "__main__":
    start_metrics_collection()
