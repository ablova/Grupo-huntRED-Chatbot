from django.conf import settings
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger('app.notifications.config')

class NotificationsConfig:
    """Configuración centralizada para notificaciones."""
    
    @staticmethod
    def get_channel_config(channel_type: str) -> Dict:
        """Obtiene la configuración para un canal específico."""
        return {
            'email': {
                'host': settings.EMAIL_HOST,
                'port': settings.EMAIL_PORT,
                'use_tls': settings.EMAIL_USE_TLS,
                'username': settings.EMAIL_HOST_USER,
                'password': settings.EMAIL_HOST_PASSWORD
            },
            'whatsapp': {
                'api_key': settings.WHATSAPP_API_KEY,
                'api_secret': settings.WHATSAPP_API_SECRET
            },
            'x': {
                'api_key': settings.X_API_KEY,
                'api_secret': settings.X_API_SECRET,
                'access_token': settings.X_ACCESS_TOKEN
            }
        }.get(channel_type, {})
    
    @staticmethod
    def get_template_config(template_type: str) -> Dict:
        """Obtiene la configuración para un template específico."""
        return {
            'proposal': {
                'subject': 'Notificación de Propuesta - huntRED',
                'template_path': 'notifications/templates/proposal.html'
            },
            'payment': {
                'subject': 'Estado de Pago - huntRED',
                'template_path': 'notifications/templates/payment.html'
            },
            'opportunity': {
                'subject': 'Nueva Oportunidad - huntRED',
                'template_path': 'notifications/templates/opportunity.html'
            },
            'fiscal': {
                'subject': 'Notificación Fiscal - huntRED',
                'template_path': 'notifications/templates/fiscal.html'
            },
            'collector': {
                'subject': 'Notificación de Cobro - huntRED',
                'template_path': 'notifications/templates/collector.html'
            },
            'interview': {
                'subject': 'Notificación de Entrevista - huntRED',
                'template_path': 'notifications/templates/interview.html'
            }
        }.get(template_type, {})
    
    @staticmethod
    def get_recipient_config(recipient_type: str) -> Dict:
        """Obtiene la configuración para un tipo de destinatario."""
        return {
            'candidate': {
                'default_channels': ['email', 'whatsapp'],
                'notification_types': ['proposal', 'opportunity', 'interview']
            },
            'consultant': {
                'default_channels': ['email', 'x'],
                'notification_types': ['proposal', 'payment', 'collector']
            },
            'client': {
                'default_channels': ['email', 'whatsapp'],
                'notification_types': ['payment', 'opportunity']
            },
            'fiscal': {
                'default_channels': ['email', 'whatsapp'],
                'notification_types': ['fiscal']
            },
            'collector': {
                'default_channels': ['email', 'whatsapp', 'x'],
                'notification_types': ['collector']
            },
            'interview': {
                'default_channels': ['email', 'whatsapp', 'x'],
                'notification_types': ['interview']
            }
        }.get(recipient_type, {})
    
    @staticmethod
    def get_priority_channels() -> List[Tuple[str, int]]:
        """Obtiene la lista de canales ordenados por prioridad."""
        return [
            ('email', 1),
            ('whatsapp', 2),
            ('x', 3)
        ]
    
    @staticmethod
    def get_retry_config() -> Dict:
        """Obtiene la configuración de reintentos para los canales."""
        return {
            'max_retries': 3,
            'retry_delay': 60,  # segundos
            'backoff_factor': 1.5
        }
    
    @staticmethod
    def get_logging_config() -> Dict:
        """Obtiene la configuración de logging para las notificaciones."""
        return {
            'level': 'DEBUG',
            'handlers': ['file', 'console'],
            'log_file': settings.BASE_DIR / 'logs' / 'notifications.log'
        }
