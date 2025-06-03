"""
Configuración del módulo de publicación.

Este módulo define la configuración específica para el módulo de publicación,
incluyendo configuraciones de canales de publicación, procesamiento de contenido,
notificaciones y validación.
"""

from typing import Dict, Any, Optional
from app.config.base import BaseConfig

class PublishConfig(BaseConfig):
    """Configuración específica para el módulo de publicación."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Configuración de canales de publicación
        self.channels = {
            'linkedin': {
                'enabled': True,
                'api_key': '',
                'api_secret': '',
                'access_token': '',
                'company_id': '',
                'max_posts_per_day': 10,
                'min_interval': 3600,  # segundos
                'retry_attempts': 3,
                'timeout': 30
            },
            'indeed': {
                'enabled': True,
                'api_key': '',
                'publisher_id': '',
                'max_posts_per_day': 20,
                'min_interval': 1800,  # segundos
                'retry_attempts': 3,
                'timeout': 30
            },
            'occ': {
                'enabled': True,
                'api_key': '',
                'company_id': '',
                'max_posts_per_day': 15,
                'min_interval': 2700,  # segundos
                'retry_attempts': 3,
                'timeout': 30
            },
            'bumeran': {
                'enabled': True,
                'api_key': '',
                'company_id': '',
                'max_posts_per_day': 25,
                'min_interval': 1440,  # segundos
                'retry_attempts': 3,
                'timeout': 30
            }
        }
        
        # Configuración de procesamiento de contenido
        self.processing = {
            'enabled': True,
            'templates_dir': 'templates/publish',
            'output_dir': 'output/publish',
            'max_retries': 3,
            'timeout': 30,  # segundos
            'batch_size': 10,
            'concurrent_tasks': 5,
            'content_types': [
                'job_posting',
                'company_update',
                'article',
                'event'
            ],
            'formats': {
                'job_posting': ['html', 'markdown', 'plain'],
                'company_update': ['html', 'markdown', 'plain'],
                'article': ['html', 'markdown'],
                'event': ['html', 'markdown', 'plain']
            }
        }
        
        # Configuración de programación
        self.scheduling = {
            'enabled': True,
            'timezone': 'America/Mexico_City',
            'max_future_days': 30,
            'min_interval': 3600,  # segundos
            'default_times': [
                '09:00',
                '12:00',
                '15:00',
                '18:00'
            ],
            'blackout_days': [
                'saturday',
                'sunday'
            ],
            'holidays': [
                '2024-01-01',  # Año Nuevo
                '2024-02-05',  # Día de la Constitución
                '2024-03-18',  # Natalicio de Benito Juárez
                '2024-05-01',  # Día del Trabajo
                '2024-09-16',  # Día de la Independencia
                '2024-11-20',  # Día de la Revolución
                '2024-12-25'   # Navidad
            ]
        }
        
        # Configuración de notificaciones
        self.notifications = {
            'enabled': True,
            'templates': {
                'publish_success': 'notifications/publish_success.html',
                'publish_failed': 'notifications/publish_failed.html',
                'schedule_reminder': 'notifications/schedule_reminder.html',
                'content_approval': 'notifications/content_approval.html'
            },
            'channels': {
                'email': {
                    'subject_prefix': '[Grupo huntRED®] ',
                    'from_email': 'publicaciones@huntred.com'
                },
                'whatsapp': {
                    'template_prefix': 'Grupo huntRED®: '
                }
            }
        }
        
        # Configuración de validación
        self.validation = {
            'enabled': True,
            'required_fields': [
                'title',
                'content',
                'type',
                'channel',
                'schedule_date'
            ],
            'field_validators': {
                'title': r'^.{10,100}$',
                'content': r'^.{50,5000}$',
                'type': r'^(job_posting|company_update|article|event)$',
                'channel': r'^(linkedin|indeed|occ|bumeran)$',
                'schedule_date': r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
            },
            'content_rules': {
                'min_length': 50,
                'max_length': 5000,
                'min_words': 10,
                'max_words': 1000,
                'allowed_tags': [
                    'p', 'br', 'strong', 'em', 'ul', 'ol', 'li',
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
                ],
                'allowed_attributes': [
                    'class', 'id', 'style'
                ]
            }
        }
        
        # Configuración de seguridad
        self.security = {
            'enabled': True,
            'encryption_key': '',
            'signature_required': True,
            'rate_limiting': {
                'enabled': True,
                'requests_per_minute': 60
            },
            'data_retention': {
                'posts': 730,  # días
                'drafts': 365,  # días
                'logs': 90  # días
            }
        }
        
        # Configuración de caché
        self.cache = {
            'enabled': True,
            'backend': 'redis',
            'timeout': 3600,  # 1 hora
            'max_size': 1000
        }
        
        # Configuración de logging
        self.logging = {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'publish.log',
            'max_size': 10485760,  # 10MB
            'backup_count': 5
        }
        
        # Validar la configuración
        self.validate()
    
    def validate(self) -> None:
        """Valida la configuración."""
        super().validate()
        
        # Validar canales de publicación
        for channel, config in self.channels.items():
            if config['enabled']:
                if not config['api_key']:
                    raise ValueError(f"API key no configurada para {channel}")
                if config['max_posts_per_day'] <= 0:
                    raise ValueError(f"El número máximo de publicaciones por día debe ser mayor que 0 para {channel}")
                if config['min_interval'] <= 0:
                    raise ValueError(f"El intervalo mínimo debe ser mayor que 0 para {channel}")
                if config['retry_attempts'] < 0:
                    raise ValueError(f"El número de reintentos no puede ser negativo para {channel}")
                if config['timeout'] <= 0:
                    raise ValueError(f"El timeout debe ser mayor que 0 para {channel}")
        
        # Validar procesamiento de contenido
        if self.processing['enabled']:
            if not self.processing['templates_dir']:
                raise ValueError("El directorio de plantillas no puede estar vacío")
            if not self.processing['output_dir']:
                raise ValueError("El directorio de salida no puede estar vacío")
            if self.processing['max_retries'] < 0:
                raise ValueError("El número máximo de reintentos no puede ser negativo")
            if self.processing['timeout'] <= 0:
                raise ValueError("El timeout debe ser mayor que 0")
            if self.processing['batch_size'] <= 0:
                raise ValueError("El tamaño del lote debe ser mayor que 0")
            if self.processing['concurrent_tasks'] <= 0:
                raise ValueError("El número de tareas concurrentes debe ser mayor que 0")
            if not self.processing['content_types']:
                raise ValueError("La lista de tipos de contenido no puede estar vacía")
            if not self.processing['formats']:
                raise ValueError("El diccionario de formatos no puede estar vacío")
        
        # Validar programación
        if self.scheduling['enabled']:
            if not self.scheduling['timezone']:
                raise ValueError("La zona horaria no puede estar vacía")
            if self.scheduling['max_future_days'] <= 0:
                raise ValueError("El número máximo de días futuros debe ser mayor que 0")
            if self.scheduling['min_interval'] <= 0:
                raise ValueError("El intervalo mínimo debe ser mayor que 0")
            if not self.scheduling['default_times']:
                raise ValueError("La lista de horas predeterminadas no puede estar vacía")
            if not self.scheduling['blackout_days']:
                raise ValueError("La lista de días de bloqueo no puede estar vacía")
            if not self.scheduling['holidays']:
                raise ValueError("La lista de días festivos no puede estar vacía")
        
        # Validar notificaciones
        if self.notifications['enabled']:
            for template in self.notifications['templates'].values():
                if not template:
                    raise ValueError("La plantilla no puede estar vacía")
        
        # Validar validación
        if self.validation['enabled']:
            if not self.validation['required_fields']:
                raise ValueError("La lista de campos requeridos no puede estar vacía")
            if not self.validation['field_validators']:
                raise ValueError("El diccionario de validadores no puede estar vacío")
            if not self.validation['content_rules']:
                raise ValueError("Las reglas de contenido no pueden estar vacías")
            if self.validation['content_rules']['min_length'] <= 0:
                raise ValueError("La longitud mínima debe ser mayor que 0")
            if self.validation['content_rules']['max_length'] <= 0:
                raise ValueError("La longitud máxima debe ser mayor que 0")
            if self.validation['content_rules']['min_words'] <= 0:
                raise ValueError("El número mínimo de palabras debe ser mayor que 0")
            if self.validation['content_rules']['max_words'] <= 0:
                raise ValueError("El número máximo de palabras debe ser mayor que 0")
            if not self.validation['content_rules']['allowed_tags']:
                raise ValueError("La lista de etiquetas permitidas no puede estar vacía")
            if not self.validation['content_rules']['allowed_attributes']:
                raise ValueError("La lista de atributos permitidos no puede estar vacía")
        
        # Validar seguridad
        if self.security['enabled']:
            if not self.security['encryption_key']:
                raise ValueError("La clave de encriptación no puede estar vacía")
            if self.security['rate_limiting']['enabled']:
                if self.security['rate_limiting']['requests_per_minute'] <= 0:
                    raise ValueError("El límite de solicitudes por minuto debe ser mayor que 0")
            for retention in self.security['data_retention'].values():
                if retention <= 0:
                    raise ValueError("El período de retención debe ser mayor que 0")
        
        # Validar caché
        if self.cache['enabled']:
            if self.cache['backend'] not in ['redis', 'memcached']:
                raise ValueError("Backend de caché inválido")
            if self.cache['timeout'] <= 0:
                raise ValueError("El timeout de caché debe ser mayor que 0")
            if self.cache['max_size'] <= 0:
                raise ValueError("El tamaño máximo de caché debe ser mayor que 0")
        
        # Validar logging
        if self.logging['level'] not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError("Nivel de logging inválido")
        if not self.logging['format']:
            raise ValueError("El formato de logging no puede estar vacío")
        if not self.logging['file']:
            raise ValueError("El archivo de logging no puede estar vacío")
        if self.logging['max_size'] <= 0:
            raise ValueError("El tamaño máximo del archivo de logging debe ser mayor que 0")
        if self.logging['backup_count'] < 0:
            raise ValueError("El número de archivos de respaldo no puede ser negativo")
    
    def get_channel_config(self, channel: str) -> Dict[str, Any]:
        """Obtiene la configuración de un canal específico."""
        if channel not in self.channels:
            raise ValueError(f"Canal {channel} no encontrado")
        return self.channels[channel]
    
    def is_channel_enabled(self, channel: str) -> bool:
        """Verifica si un canal está habilitado."""
        if channel not in self.channels:
            return False
        return self.channels[channel]['enabled']
    
    def get_template_config(self, template: str) -> Optional[str]:
        """Obtiene la configuración de una plantilla específica."""
        return self.notifications['templates'].get(template)
    
    def is_template_enabled(self, template: str) -> bool:
        """Verifica si una plantilla está habilitada."""
        return template in self.notifications['templates']
    
    def is_content_type_valid(self, content_type: str) -> bool:
        """Verifica si un tipo de contenido es válido."""
        return content_type in self.processing['content_types']
    
    def is_format_valid(self, content_type: str, format: str) -> bool:
        """Verifica si un formato es válido para un tipo de contenido."""
        if not self.is_content_type_valid(content_type):
            return False
        return format in self.processing['formats'].get(content_type, []) 