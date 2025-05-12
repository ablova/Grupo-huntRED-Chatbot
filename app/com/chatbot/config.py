from typing import Dict, Any, Optional
import environ
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from ai_huntred.settings import CHATBOT_CONFIG
from app.com.chatbot.metrics import chatbot_metrics

env = environ.Env()
logger = logging.getLogger(__name__)

# Register all chatbot modules at startup
from app.import_config import register_module
register_module('channel_config', 'app.com.chatbot.config.ChannelConfig')
register_module('rate_limiter', 'app.com.chatbot.config.RateLimiter')

def get_channel_config():
    """Get the channel configuration."""
    return {
        'whatsapp': {
            'retry_attempts': 3,
            'retry_delay': 5,  # segundos
            'batch_size': 50,
            'rate_limit': 20,  # mensajes por minuto
            'max_message_length': 4096,
            'media_supported': True,
            'fallback_channel': 'email',
            'metrics': {
                'enabled': True,
                'collection_interval': 60,  # segundos
                'metrics_to_track': ['delivery_rate', 'response_time', 'error_rate']
            }
        },
        'telegram': {
            'retry_attempts': 3,
            'retry_delay': 3,
            'batch_size': 100,
            'rate_limit': 30,
            'max_message_length': 4096,
            'media_supported': True,
            'fallback_channel': 'email',
            'metrics': {
                'enabled': True,
                'collection_interval': 60,
                'metrics_to_track': ['delivery_rate', 'response_time', 'error_rate']
            }
        },
        'messenger': {
            'retry_attempts': 2,
            'retry_delay': 2,
            'batch_size': 100,
            'rate_limit': 30,
            'max_message_length': 2000,
            'media_supported': True,
            'fallback_channel': 'email',
            'metrics': {
                'enabled': True,
                'collection_interval': 60,
                'metrics_to_track': ['delivery_rate', 'response_time', 'error_rate']
            }
        },
        'instagram': {
            'retry_attempts': 1,
            'retry_delay': 10,
            'batch_size': 20,
            'rate_limit': 10,
            'max_message_length': 2200,
            'media_supported': True,
            'fallback_channel': 'email',
            'metrics': {
                'enabled': True,
                'collection_interval': 60,
                'metrics_to_track': ['delivery_rate', 'response_time', 'error_rate']
            }
        },
        'slack': {
            'retry_attempts': 3,
            'retry_delay': 2,
            'batch_size': 100,
            'rate_limit': 50,
            'max_message_length': 40000,
            'media_supported': True,
            'fallback_channel': 'email',
            'metrics': {
                'enabled': True,
                'collection_interval': 60,
                'metrics_to_track': ['delivery_rate', 'response_time', 'error_rate']
            }
        }
    }

def get_rate_limiter():
    """Get the rate limiter instance."""
    class RateLimiter:
        def __init__(self):
            self.limits = defaultdict(int)
            self.last_reset = defaultdict(lambda: datetime.now())
            self.channel_limits = {
                'whatsapp': 20,  # mensajes por minuto
                'telegram': 30,
                'messenger': 30,
                'slack': 50,
                'instagram': 20
            }

        async def check_limit(self, channel: str) -> bool:
            """Check if we can send another message on this channel."""
            if channel not in self.channel_limits:
                return True

            limit = self.channel_limits[channel]
            now = datetime.now()
            
            # Reset counter if we're in a new minute
            if (now - self.last_reset[channel]).total_seconds() > 60:
                self.limits[channel] = 0
                self.last_reset[channel] = now

            # Check if we've reached the limit
            if self.limits[channel] >= limit:
                return False

            # Increment counter and return True
            self.limits[channel] += 1
            return True

        async def wait_for_limit(self, channel: str) -> None:
            """Wait until we can send another message on this channel."""
            while not await self.check_limit(channel):
                await asyncio.sleep(1)
    
    return RateLimiter()

def start_metrics_collection():
    """Inicia la recolección de métricas del chatbot."""
    logger.info("Iniciando recolección de métricas del chatbot...")
    
    # Configurar intervalo de recolección
    chatbot_metrics.collection_interval = CHATBOT_CONFIG['METRICS_COLLECTION_INTERVAL']
    
    # Iniciar recolección
    asyncio.run(chatbot_metrics.collect_metrics())

def get_chat_state_manager():
    """Función diferida para obtener ChatStateManager."""
    from app.com.chatbot.chat_state_manager import ChatStateManager
    return ChatStateManager

def get_intent_processor():
    """Función diferida para obtener IntentProcessor."""
    from app.com.chatbot.intents_handler import IntentProcessor
    return IntentProcessor

def get_whatsapp_handler():
    """Función diferida para obtener WhatsAppHandler."""
    from app.com.chatbot.integrations.whatsapp import WhatsAppHandler
    return WhatsAppHandler

def get_fetch_whatsapp_user_data():
    """Función diferida para obtener fetch_whatsapp_user_data."""
    from app.com.chatbot.integrations.whatsapp import fetch_whatsapp_user_data
    return fetch_whatsapp_user_data

def get_telegram_handler():
    """Función diferida para obtener TelegramHandler."""
    from app.com.chatbot.integrations.telegram import TelegramHandler
    return TelegramHandler

def get_fetch_telegram_user_data():
    """Función diferida para obtener fetch_telegram_user_data."""
    from app.com.chatbot.integrations.telegram import fetch_telegram_user_data
    return fetch_telegram_user_data

def get_slack_handler():
    """Función diferida para obtener SlackHandler."""
    from app.com.chatbot.integrations.slack import SlackHandler
    return SlackHandler

def get_fetch_slack_user_data():
    """Función diferida para obtener fetch_slack_user_data."""
    from app.com.chatbot.integrations.slack import fetch_slack_user_data
    return fetch_slack_user_data

def get_instagram_handler():
    """Función diferida para obtener InstagramHandler."""
    from app.com.chatbot.integrations.instagram import InstagramHandler
    return InstagramHandler

def get_fetch_instagram_user_data():
    """Función diferida para obtener fetch_instagram_user_data."""
    from app.com.chatbot.integrations.instagram import fetch_instagram_user_data
    return fetch_instagram_user_data

def get_message_service():
    """Función diferida para obtener MessageService."""
    from app.com.chatbot.integrations.services import MessageService
    return MessageService

def get_gamification_service():
    """Función diferida para obtener GamificationService."""
    from app.com.chatbot.integrations.services import GamificationService
    return GamificationService

def get_conversational_flow_manager():
    """Función diferida para obtener ConversationalFlowManager."""
    from app.com.chatbot.conversational_flow import ConversationalFlowManager
    return ConversationalFlowManager

def get_intent_detector():
    """Función diferida para obtener IntentDetector."""
    from app.com.chatbot.components.intent_detector import IntentDetector
    return IntentDetector

def get_context_manager():
    """Función diferida para obtener ContextManager."""
    from app.com.chatbot.components.context_manager import ContextManager
    return ContextManager

def get_response_generator():
    """Función diferida para obtener ResponseGenerator."""
    from app.com.chatbot.components.response_generator import ResponseGenerator
    return ResponseGenerator

def get_state_manager():
    """Función diferida para obtener StateManager."""
    from app.com.chatbot.components.state_manager import StateManager
    return StateManager

def get_gpt_handler():
    """Función diferida para obtener GPTHandler."""
    from app.com.chatbot.gpt import GPTHandler
    return GPTHandler

def get_cv_parser():
    """Función diferida para obtener CVParser."""
    from app.com.utils.parser import CVParser
    return CVParser

def get_workflow_context():
    """Función diferida para obtener workflow context."""
    from app.com.chatbot.workflow.common import get_workflow_context
    return get_workflow_context()
