# /home/pablo/app/com/config.py
#
# Configuración centralizada para el módulo de comunicaciones.
#
from django.conf import settings
from typing import Dict, List, Tuple
import logging
import os
from pathlib import Path
from app.config import settings as global_settings

logger = logging.getLogger('app.ats.config')

# Directorios
ATS_MODELS_DIR = os.path.join(settings.BASE_DIR, 'ats_models')
ATS_DATA_DIR = os.path.join(settings.BASE_DIR, 'ats_data')
ATS_LOGS_DIR = os.path.join(settings.BASE_DIR, 'ats_logs')

# Crear directorios si no existen
for directory in [ATS_MODELS_DIR, ATS_DATA_DIR, ATS_LOGS_DIR]:
    Path(directory).mkdir(parents=True, exist_ok=True)

# Exportar la configuración de ATS
ATS_CONFIG = global_settings.ats

# Exportar configuraciones específicas
CHANNEL_CONFIG = ATS_CONFIG.channels
WORKFLOW_CONFIG = ATS_CONFIG.workflows
NOTIFICATION_CONFIG = ATS_CONFIG.notifications
ML_CONFIG = ATS_CONFIG.ml
CACHE_CONFIG = ATS_CONFIG.cache
LOGGING_CONFIG = ATS_CONFIG.logging
SECURITY_CONFIG = ATS_CONFIG.security

# Configuración de métricas
METRICS_CONFIG = {
    'tracking': {
        'enabled': True,
        'interval': 300,  # 5 minutos
        'retention_days': 90
    },
    'alerts': {
        'enabled': True,
        'thresholds': {
            'response_time': 24,  # horas
            'conversion_rate': 0.3,  # 30%
            'satisfaction_score': 4.0  # escala 1-5
        }
    }
}

# Configuración de integraciones
INTEGRATION_CONFIG = {
    'whatsapp': {
        'enabled': True
    },
    'x': {
        'enabled': True
    },
    'calendar': {
        'provider': 'google',
        'credentials_file': os.path.join(settings.BASE_DIR, 'credentials.json'),
        'enabled': True
    }
}

ATS_CONFIG = {
    'SYSTEM': {
        'ENABLED': True,
        'DEBUG': settings.DEBUG,
        'VERSION': '1.0.0'
    },
    'STORAGE': {
        'BASE_DIR': ATS_MODELS_DIR,
        'CACHE': CACHE_CONFIG,
        'LOGGING': LOGGING_CONFIG
    },
    'COMMUNICATION': {
        'CHANNELS': CHANNEL_CONFIG,
        'NOTIFICATIONS': NOTIFICATION_CONFIG,
        'INTEGRATIONS': INTEGRATION_CONFIG
    },
    'WORKFLOW': WORKFLOW_CONFIG,
    'METRICS': METRICS_CONFIG,
    'SECURITY': SECURITY_CONFIG
}

class ComConfig:
    """Configuración centralizada para el módulo de comunicaciones."""
    
    @staticmethod
    def get_channel_config(channel_type: str) -> Dict:
        """Obtiene la configuración para un canal específico."""
        from app.models import WhatsAppAPI, TelegramAPI, MessengerAPI, InstagramAPI, SlackAPI, XAPI
        
        return {
            'whatsapp': {
                'retry_delay': 30,
                'max_retries': 3
            },
            'telegram': {
                'retry_delay': 30,
                'max_retries': 3
            },
            'messenger': {
                'retry_delay': 30,
                'max_retries': 3
            },
            'instagram': {
                'retry_delay': 30,
                'max_retries': 3
            },
            'slack': {
                'retry_delay': 30,
                'max_retries': 3
            },
            'x': {
                'retry_delay': 60,
                'max_retries': 3
            },
            'email': {
                'host': settings.EMAIL_HOST,
                'port': settings.EMAIL_PORT,
                'use_tls': settings.EMAIL_USE_TLS,
                'username': settings.EMAIL_HOST_USER,
                'password': settings.EMAIL_HOST_PASSWORD,
                'retry_delay': 10,
                'max_retries': 3
            }
        }.get(channel_type, {})
    
    @staticmethod
    def get_recipient_config(recipient_type: str) -> Dict:
        """Obtiene la configuración para un tipo de destinatario."""
        return {
            'candidate': {
                'default_channels': ['whatsapp', 'email'],
                'notification_types': ['proposal', 'opportunity', 'interview']
            },
            'consultant': {
                'default_channels': ['whatsapp', 'x', 'email'],
                'notification_types': ['proposal', 'payment', 'collector']
            },
            'client': {
                'default_channels': ['whatsapp', 'email'],
                'notification_types': ['payment', 'opportunity']
            },
            'fiscal': {
                'default_channels': ['whatsapp', 'email'],
                'notification_types': ['fiscal']
            },
            'collector': {
                'default_channels': ['whatsapp', 'x', 'email'],
                'notification_types': ['collector']
            }
        }.get(recipient_type, {})
    
    @staticmethod
    def get_workflow_config() -> Dict:
        """Obtiene la configuración del flujo de trabajo."""
        return {
            'states': {
                'initial': 'INICIO',
                'states': [
                    'INICIO',
                    'IDENTIFICACION',
                    'PERFIL',
                    'OPORTUNIDAD',
                    'ENTREVISTA',
                    'PROPUESTA',
                    'CERRADO'
                ],
                'transitions': {
                    'INICIO': ['IDENTIFICACION'],
                    'IDENTIFICACION': ['PERFIL'],
                    'PERFIL': ['OPORTUNIDAD'],
                    'OPORTUNIDAD': ['ENTREVISTA'],
                    'ENTREVISTA': ['PROPUESTA'],
                    'PROPUESTA': ['CERRADO']
                }
            },
            'timeouts': {
                'IDENTIFICACION': 24 * 3600,  # 24 horas
                'PERFIL': 48 * 3600,  # 48 horas
                'OPORTUNIDAD': 72 * 3600,  # 72 horas
                'ENTREVISTA': 24 * 3600,  # 24 horas
                'PROPUESTA': 48 * 3600,  # 48 horas
            }
        }
    
    @staticmethod
    def get_visualization_config() -> Dict:
        """Obtiene la configuración para la visualización del flujo."""
        return {
            'charts': {
                'flow': {
                    'type': 'sankey',
                    'fields': ['state_from', 'state_to', 'count']
                },
                'metrics': {
                    'type': 'line',
                    'fields': ['date', 'metric', 'value']
                },
                'status': {
                    'type': 'pie',
                    'fields': ['status', 'count']
                }
            },
            'tables': {
                'conversations': ['id', 'recipient', 'channel', 'state', 'last_message', 'timestamp'],
                'notifications': ['id', 'recipient', 'type', 'status', 'timestamp'],
                'metrics': ['metric', 'value', 'timestamp']
            }
        }

# Exportar funciones de utilidad
def get_channel_config(channel: str):
    """Obtiene la configuración de un canal específico."""
    return ATS_CONFIG.get_channel_config(channel)

def get_workflow_config(workflow: str):
    """Obtiene la configuración de un workflow específico."""
    return ATS_CONFIG.get_workflow_config(workflow)

def get_template_config(template: str):
    """Obtiene la configuración de una plantilla específica."""
    return ATS_CONFIG.get_template_config(template)

def get_model_config(model: str):
    """Obtiene la configuración de un modelo específico."""
    return ATS_CONFIG.get_model_config(model)

def is_channel_enabled(channel: str) -> bool:
    """Verifica si un canal está habilitado."""
    return ATS_CONFIG.is_channel_enabled(channel)

def is_workflow_enabled(workflow: str) -> bool:
    """Verifica si un workflow está habilitado."""
    return ATS_CONFIG.is_workflow_enabled(workflow)

def is_template_enabled(template: str) -> bool:
    """Verifica si una plantilla está habilitada."""
    return ATS_CONFIG.is_template_enabled(template)

def is_model_enabled(model: str) -> bool:
    """Verifica si un modelo está habilitado."""
    return ATS_CONFIG.is_model_enabled(model)

# Exportar todo
__all__ = [
    'ATS_CONFIG',
    'CHANNEL_CONFIG',
    'WORKFLOW_CONFIG',
    'NOTIFICATION_CONFIG',
    'ML_CONFIG',
    'CACHE_CONFIG',
    'LOGGING_CONFIG',
    'SECURITY_CONFIG',
    'get_channel_config',
    'get_workflow_config',
    'get_template_config',
    'get_model_config',
    'is_channel_enabled',
    'is_workflow_enabled',
    'is_template_enabled',
    'is_model_enabled'
]
