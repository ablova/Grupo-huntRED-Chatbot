"""
Configuración del módulo de pagos.

Este módulo define la configuración específica para el módulo de pagos,
incluyendo configuraciones de pasarelas de pago, procesamiento de pagos,
facturación y notificaciones relacionadas con pagos.
"""

from typing import Dict, Any, Optional
from app.config.base import BaseConfig

class PagosConfig(BaseConfig):
    """Configuración específica para el módulo de pagos."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Configuración de pasarelas de pago
        self.gateways = {
            'stripe': {
                'enabled': True,
                'api_key': '',
                'webhook_secret': '',
                'currency': 'MXN',
                'mode': 'live',  # 'live' o 'test'
                'retry_attempts': 3,
                'timeout': 30
            },
            'paypal': {
                'enabled': True,
                'client_id': '',
                'client_secret': '',
                'currency': 'MXN',
                'mode': 'live',  # 'live' o 'sandbox'
                'retry_attempts': 3,
                'timeout': 30
            },
            'openpay': {
                'enabled': True,
                'merchant_id': '',
                'private_key': '',
                'public_key': '',
                'currency': 'MXN',
                'mode': 'live',  # 'live' o 'test'
                'retry_attempts': 3,
                'timeout': 30
            }
        }
        
        # Configuración de procesamiento de pagos
        self.processing = {
            'enabled': True,
            'batch_size': 100,
            'max_retries': 3,
            'retry_delay': 300,  # segundos
            'timeout': 30,  # segundos
            'webhook_timeout': 10,  # segundos
            'notification_delay': 60  # segundos
        }
        
        # Configuración de facturación
        self.billing = {
            'enabled': True,
            'tax_rate': 0.16,  # 16%
            'currency': 'MXN',
            'decimal_places': 2,
            'rounding_mode': 'HALF_UP',  # 'HALF_UP', 'HALF_DOWN', 'UP', 'DOWN'
            'invoice_prefix': 'INV-',
            'invoice_number_format': '{prefix}{year}{month:02d}{number:04d}',
            'due_days': 30,
            'late_fee_rate': 0.05,  # 5%
            'grace_period': 5  # días
        }
        
        # Configuración de notificaciones de pago
        self.notifications = {
            'enabled': True,
            'templates': {
                'payment_success': 'notifications/payment_success.html',
                'payment_failed': 'notifications/payment_failed.html',
                'invoice_created': 'notifications/invoice_created.html',
                'invoice_paid': 'notifications/invoice_paid.html',
                'invoice_overdue': 'notifications/invoice_overdue.html'
            },
            'channels': {
                'email': {
                    'subject_prefix': '[Grupo huntRED®] ',
                    'from_email': 'pagos@huntred.com'
                },
                'whatsapp': {
                    'template_prefix': 'Grupo huntRED®: '
                }
            }
        }
        
        # Configuración de seguridad
        self.security = {
            'enabled': True,
            'encryption_key': '',
            'webhook_ips': [],  # Lista de IPs permitidas para webhooks
            'rate_limiting': {
                'enabled': True,
                'requests_per_minute': 60
            },
            'data_retention': {
                'transactions': 730,  # días
                'invoices': 730,  # días
                'receipts': 730  # días
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
            'file': 'pagos.log',
            'max_size': 10485760,  # 10MB
            'backup_count': 5
        }
        
        # Validar la configuración
        self.validate()
    
    def validate(self) -> None:
        """Valida la configuración."""
        super().validate()
        
        # Validar pasarelas de pago
        for gateway, config in self.gateways.items():
            if config['enabled']:
                if not config['api_key']:
                    raise ValueError(f"API key no configurada para {gateway}")
                if not config['currency']:
                    raise ValueError(f"Moneda no configurada para {gateway}")
                if config['mode'] not in ['live', 'test', 'sandbox']:
                    raise ValueError(f"Modo inválido para {gateway}")
        
        # Validar procesamiento de pagos
        if self.processing['enabled']:
            if self.processing['batch_size'] <= 0:
                raise ValueError("El tamaño del lote debe ser mayor que 0")
            if self.processing['max_retries'] < 0:
                raise ValueError("El número máximo de reintentos no puede ser negativo")
            if self.processing['retry_delay'] < 0:
                raise ValueError("El retraso de reintento no puede ser negativo")
            if self.processing['timeout'] <= 0:
                raise ValueError("El timeout debe ser mayor que 0")
        
        # Validar facturación
        if self.billing['enabled']:
            if self.billing['tax_rate'] < 0:
                raise ValueError("La tasa de impuestos no puede ser negativa")
            if not self.billing['currency']:
                raise ValueError("La moneda no puede estar vacía")
            if self.billing['decimal_places'] < 0:
                raise ValueError("El número de decimales no puede ser negativo")
            if self.billing['rounding_mode'] not in ['HALF_UP', 'HALF_DOWN', 'UP', 'DOWN']:
                raise ValueError("Modo de redondeo inválido")
            if self.billing['due_days'] <= 0:
                raise ValueError("Los días de vencimiento deben ser mayores que 0")
            if self.billing['late_fee_rate'] < 0:
                raise ValueError("La tasa de recargo no puede ser negativa")
            if self.billing['grace_period'] < 0:
                raise ValueError("El período de gracia no puede ser negativo")
        
        # Validar notificaciones
        if self.notifications['enabled']:
            for template in self.notifications['templates'].values():
                if not template:
                    raise ValueError("La plantilla no puede estar vacía")
        
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
    
    def get_gateway_config(self, gateway: str) -> Dict[str, Any]:
        """Obtiene la configuración de una pasarela específica."""
        if gateway not in self.gateways:
            raise ValueError(f"Pasarela {gateway} no encontrada")
        return self.gateways[gateway]
    
    def is_gateway_enabled(self, gateway: str) -> bool:
        """Verifica si una pasarela está habilitada."""
        if gateway not in self.gateways:
            return False
        return self.gateways[gateway]['enabled']
    
    def get_template_config(self, template: str) -> Optional[str]:
        """Obtiene la configuración de una plantilla específica."""
        return self.notifications['templates'].get(template)
    
    def is_template_enabled(self, template: str) -> bool:
        """Verifica si una plantilla está habilitada."""
        return template in self.notifications['templates'] 