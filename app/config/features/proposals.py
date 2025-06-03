"""
Configuración del módulo de propuestas.

Este módulo define la configuración específica para el módulo de propuestas,
incluyendo configuraciones de generación de propuestas, seguimiento,
notificaciones y validación.
"""

from typing import Dict, Any, Optional
from app.config.base import BaseConfig

class ProposalsConfig(BaseConfig):
    """Configuración específica para el módulo de propuestas."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Configuración de generación de propuestas
        self.generation = {
            'enabled': True,
            'templates_dir': 'templates/proposals',
            'output_dir': 'output/proposals',
            'max_retries': 3,
            'timeout': 30,  # segundos
            'batch_size': 10,
            'concurrent_tasks': 5
        }
        
        # Configuración de seguimiento de propuestas
        self.tracking = {
            'enabled': True,
            'states': [
                'draft',
                'pending_review',
                'approved',
                'sent',
                'accepted',
                'rejected',
                'expired'
            ],
            'transitions': {
                'draft': ['pending_review', 'expired'],
                'pending_review': ['approved', 'rejected'],
                'approved': ['sent', 'expired'],
                'sent': ['accepted', 'rejected', 'expired'],
                'accepted': [],
                'rejected': [],
                'expired': []
            },
            'expiration_days': 30,
            'reminder_days': [7, 3, 1],  # días antes de la expiración
            'auto_expire': True
        }
        
        # Configuración de notificaciones
        self.notifications = {
            'enabled': True,
            'templates': {
                'proposal_created': 'notifications/proposal_created.html',
                'proposal_approved': 'notifications/proposal_approved.html',
                'proposal_sent': 'notifications/proposal_sent.html',
                'proposal_accepted': 'notifications/proposal_accepted.html',
                'proposal_rejected': 'notifications/proposal_rejected.html',
                'proposal_expired': 'notifications/proposal_expired.html',
                'proposal_reminder': 'notifications/proposal_reminder.html'
            },
            'channels': {
                'email': {
                    'subject_prefix': '[Grupo huntRED®] ',
                    'from_email': 'propuestas@huntred.com'
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
                'client_name',
                'client_email',
                'proposal_date',
                'valid_until',
                'items',
                'total_amount',
                'payment_terms'
            ],
            'field_validators': {
                'client_email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'proposal_date': r'^\d{4}-\d{2}-\d{2}$',
                'valid_until': r'^\d{4}-\d{2}-\d{2}$',
                'total_amount': r'^\d+(\.\d{2})?$'
            },
            'min_items': 1,
            'max_items': 50,
            'min_amount': 0.01,
            'max_amount': 1000000.00
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
                'proposals': 730,  # días
                'attachments': 730,  # días
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
            'file': 'proposals.log',
            'max_size': 10485760,  # 10MB
            'backup_count': 5
        }
        
        # Validar la configuración
        self.validate()
    
    def validate(self) -> None:
        """Valida la configuración."""
        super().validate()
        
        # Validar generación de propuestas
        if self.generation['enabled']:
            if not self.generation['templates_dir']:
                raise ValueError("El directorio de plantillas no puede estar vacío")
            if not self.generation['output_dir']:
                raise ValueError("El directorio de salida no puede estar vacío")
            if self.generation['max_retries'] < 0:
                raise ValueError("El número máximo de reintentos no puede ser negativo")
            if self.generation['timeout'] <= 0:
                raise ValueError("El timeout debe ser mayor que 0")
            if self.generation['batch_size'] <= 0:
                raise ValueError("El tamaño del lote debe ser mayor que 0")
            if self.generation['concurrent_tasks'] <= 0:
                raise ValueError("El número de tareas concurrentes debe ser mayor que 0")
        
        # Validar seguimiento de propuestas
        if self.tracking['enabled']:
            if not self.tracking['states']:
                raise ValueError("La lista de estados no puede estar vacía")
            if not self.tracking['transitions']:
                raise ValueError("El diccionario de transiciones no puede estar vacío")
            if self.tracking['expiration_days'] <= 0:
                raise ValueError("Los días de expiración deben ser mayores que 0")
            if not self.tracking['reminder_days']:
                raise ValueError("La lista de días de recordatorio no puede estar vacía")
            for days in self.tracking['reminder_days']:
                if days <= 0:
                    raise ValueError("Los días de recordatorio deben ser mayores que 0")
        
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
            if self.validation['min_items'] <= 0:
                raise ValueError("El número mínimo de items debe ser mayor que 0")
            if self.validation['max_items'] <= 0:
                raise ValueError("El número máximo de items debe ser mayor que 0")
            if self.validation['min_amount'] < 0:
                raise ValueError("El monto mínimo no puede ser negativo")
            if self.validation['max_amount'] <= 0:
                raise ValueError("El monto máximo debe ser mayor que 0")
        
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
    
    def get_template_config(self, template: str) -> Optional[str]:
        """Obtiene la configuración de una plantilla específica."""
        return self.notifications['templates'].get(template)
    
    def is_template_enabled(self, template: str) -> bool:
        """Verifica si una plantilla está habilitada."""
        return template in self.notifications['templates']
    
    def is_state_valid(self, state: str) -> bool:
        """Verifica si un estado es válido."""
        return state in self.tracking['states']
    
    def is_transition_valid(self, from_state: str, to_state: str) -> bool:
        """Verifica si una transición es válida."""
        if not self.is_state_valid(from_state) or not self.is_state_valid(to_state):
            return False
        return to_state in self.tracking['transitions'].get(from_state, []) 