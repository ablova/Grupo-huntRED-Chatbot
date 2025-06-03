# /home/pablo/app/com/config.py
#
# Configuración centralizada para el módulo de comunicaciones.
#
from django.conf import settings
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger('app.ats.config')

class ComConfig:
    """Configuración centralizada para el módulo de comunicaciones."""
    
    @staticmethod
    def get_channel_config(channel_type: str) -> Dict:
        """Obtiene la configuración para un canal específico."""
        return {
            'whatsapp': {
                'api_key': settings.WHATSAPP_API_KEY,
                'api_secret': settings.WHATSAPP_API_SECRET,
                'retry_delay': 30,
                'max_retries': 3
            },
            'x': {
                'api_key': settings.X_API_KEY,
                'api_secret': settings.X_API_SECRET,
                'access_token': settings.X_ACCESS_TOKEN,
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
