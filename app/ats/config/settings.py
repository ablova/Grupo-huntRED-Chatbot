from django.conf import settings
from typing import Dict, Any
import os

class ATSSettings:
    """Configuración centralizada del ATS"""
    
    # Configuración de Notificaciones
    NOTIFICATIONS = {
        'DEFAULT_CHANNEL': 'email',
        'CHANNELS': {
            'email': {
                'enabled': True,
                'priority': 1,
                'rate_limit': 100,
            },
            'linkedin': {
                'enabled': True,
                'priority': 2,
                'rate_limit': 50,
            },
            'whatsapp': {
                'enabled': True,
                'priority': 3,
                'rate_limit': 30,
            }
        },
        'TEMPLATES_DIR': os.path.join(settings.BASE_DIR, 'app/ats/templates/notifications'),
        'CACHE_TTL': 3600,  # 1 hora
    }
    
    # Configuración de Chatbot
    CHATBOT = {
        'MODEL': 'gpt-4',
        'TEMPERATURE': 0.7,
        'MAX_TOKENS': 2000,
        'CACHE_TTL': 1800,  # 30 minutos
        'FALLBACK_RESPONSES': {
            'error': 'Lo siento, ha ocurrido un error. Por favor, inténtalo de nuevo.',
            'timeout': 'La solicitud está tomando más tiempo de lo esperado. Por favor, inténtalo de nuevo.',
            'invalid': 'No entiendo tu solicitud. ¿Podrías reformularla?'
        }
    }
    
    # Configuración de Análisis de Mercado
    MARKET_ANALYSIS = {
        'UPDATE_FREQUENCY': 86400,  # 24 horas
        'CACHE_TTL': 43200,  # 12 horas
        'MIN_DATA_POINTS': 100,
        'CONFIDENCE_THRESHOLD': 0.8,
        'TREND_WINDOW': 30,  # días
    }
    
    # Configuración de Aprendizaje
    LEARNING = {
        'PROVIDERS': {
            'coursera': {
                'enabled': True,
                'api_version': 'v1',
            },
            'udemy': {
                'enabled': True,
                'api_version': 'v2',
            },
            'linkedin_learning': {
                'enabled': True,
                'api_version': 'v1',
            }
        },
        'CACHE_TTL': 7200,  # 2 horas
        'RECOMMENDATION_THRESHOLD': 0.7,
    }
    
    # Configuración de Precios
    PRICING = {
        'CURRENCY': 'USD',
        'DECIMAL_PLACES': 2,
        'DISCOUNT_RULES': {
            'max_discount': 0.3,  # 30%
            'min_purchase': 100,
        },
        'REFERRAL_FEE': {
            'percentage': 0.1,  # 10%
            'min_amount': 50,
        }
    }
    
    # Configuración de Analytics
    ANALYTICS = {
        'TRACKING_ENABLED': True,
        'EVENT_RETENTION': 90,  # días
        'BATCH_SIZE': 1000,
        'METRICS': {
            'update_frequency': 3600,  # 1 hora
            'aggregation_window': 86400,  # 24 horas
        }
    }
    
    @classmethod
    def get_setting(cls, path: str, default: Any = None) -> Any:
        """Obtiene una configuración específica usando notación de punto"""
        try:
            value = cls
            for key in path.split('.'):
                value = getattr(value, key)
            return value
        except (AttributeError, KeyError):
            return default
    
    @classmethod
    def update_setting(cls, path: str, value: Any) -> None:
        """Actualiza una configuración específica"""
        keys = path.split('.')
        target = cls
        for key in keys[:-1]:
            target = getattr(target, key)
        setattr(target, keys[-1], value)

# Instancia global de configuración
ats_settings = ATSSettings() 