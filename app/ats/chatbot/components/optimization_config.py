from typing import Dict, Any
import environ

env = environ.Env()

class OptimizationConfig:
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Obtiene la configuración de optimización del chatbot."""
        return {
            'INTENT_PROCESSING': {
                'MAX_CONCURRENT_INTENTS': env.int('CHATBOT_MAX_INTENTS', default=10),
                'CACHE_DURATION': env.int('CHATBOT_CACHE_DURATION', default=300),  # 5 minutos
                'PATTERN_OPTIMIZATION_ENABLED': env.bool('CHATBOT_PATTERN_OPTIMIZATION', default=True),
                'BATCH_SIZE': env.int('CHATBOT_BATCH_SIZE', default=1000)
            },
            'ML': {
                'BATCH_SIZE': env.int('ML_BATCH_SIZE', default=1000),
                'N_JOBS': env.int('ML_N_JOBS', default=-1),  # Usar todos los cores disponibles
                'MAX_FEATURES': env.int('ML_MAX_FEATURES', default=1000),
                'CACHE_ENABLED': env.bool('ML_CACHE_ENABLED', default=True),
                'CACHE_DURATION': env.int('ML_CACHE_DURATION', default=3600)  # 1 hora
            },
            'CHANNELS': {
                'MAX_RETRIES': env.int('CHANNEL_MAX_RETRIES', default=3),
                'RETRY_DELAY': env.int('CHANNEL_RETRY_DELAY', default=5),  # segundos
                'RATE_LIMITING': {
                    'ENABLED': env.bool('CHANNEL_RATE_LIMITING', default=True),
                    'DEFAULT_RATE': env.int('CHANNEL_DEFAULT_RATE', default=20),  # mensajes por minuto
                    'WHATSAPP_RATE': env.int('WHATSAPP_RATE', default=20),
                    'TELEGRAM_RATE': env.int('TELEGRAM_RATE', default=30),
                    'MESSENGER_RATE': env.int('MESSENGER_RATE', default=30),
                    'INSTAGRAM_RATE': env.int('INSTAGRAM_RATE', default=10),
                    'SLACK_RATE': env.int('SLACK_RATE', default=100)
                }
            },
            'MEMORY': {
                'MAX_SESSIONS': env.int('MEMORY_MAX_SESSIONS', default=100),
                'SESSION_TIMEOUT': env.int('MEMORY_SESSION_TIMEOUT', default=300),  # 5 minutos
                'CACHE_ENABLED': env.bool('MEMORY_CACHE_ENABLED', default=True),
                'CACHE_DURATION': env.int('MEMORY_CACHE_DURATION', default=3600)  # 1 hora
            },
            'METRICS': {
                'ENABLED': env.bool('METRICS_ENABLED', default=True),
                'COLLECTION_INTERVAL': env.int('METRICS_COLLECTION_INTERVAL', default=60),  # segundos
                'METRICS_TO_TRACK': [
                    'intent_detection',
                    'message_delivery',
                    'response_time',
                    'error_rate',
                    'active_users',
                    'ml_training',
                    'ml_prediction'
                ]
            }
        }
