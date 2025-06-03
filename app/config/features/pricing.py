"""
Configuración del módulo de precios.

Este módulo define la configuración específica para el módulo de precios,
incluyendo configuraciones de precios progresivos, precios por volumen,
generación de propuestas y seguimiento de precios.
"""

from typing import Dict, Any, Optional
from app.config.base import BaseConfig

class PricingConfig(BaseConfig):
    """Configuración específica para el módulo de precios."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Configuración de precios progresivos
        self.progressive = {
            'enabled': True,
            'tiers': [
                {
                    'name': 'básico',
                    'min_volume': 1,
                    'max_volume': 10,
                    'discount': 0.00  # 0%
                },
                {
                    'name': 'estándar',
                    'min_volume': 11,
                    'max_volume': 50,
                    'discount': 0.05  # 5%
                },
                {
                    'name': 'premium',
                    'min_volume': 51,
                    'max_volume': 100,
                    'discount': 0.10  # 10%
                },
                {
                    'name': 'enterprise',
                    'min_volume': 101,
                    'max_volume': None,
                    'discount': 0.15  # 15%
                }
            ],
            'base_price': 1000.00,
            'currency': 'MXN',
            'decimal_places': 2,
            'rounding_mode': 'HALF_UP'  # 'HALF_UP', 'HALF_DOWN', 'UP', 'DOWN'
        }
        
        # Configuración de precios por volumen
        self.volume = {
            'enabled': True,
            'tiers': [
                {
                    'name': 'pequeño',
                    'min_volume': 1,
                    'max_volume': 5,
                    'price_per_unit': 1000.00
                },
                {
                    'name': 'mediano',
                    'min_volume': 6,
                    'max_volume': 20,
                    'price_per_unit': 900.00
                },
                {
                    'name': 'grande',
                    'min_volume': 21,
                    'max_volume': 50,
                    'price_per_unit': 800.00
                },
                {
                    'name': 'extra grande',
                    'min_volume': 51,
                    'max_volume': None,
                    'price_per_unit': 700.00
                }
            ],
            'currency': 'MXN',
            'decimal_places': 2,
            'rounding_mode': 'HALF_UP'  # 'HALF_UP', 'HALF_DOWN', 'UP', 'DOWN'
        }
        
        # Configuración de generación de propuestas
        self.proposal = {
            'enabled': True,
            'templates_dir': 'templates/pricing',
            'output_dir': 'output/pricing',
            'max_retries': 3,
            'timeout': 30,  # segundos
            'batch_size': 10,
            'concurrent_tasks': 5
        }
        
        # Configuración de seguimiento de precios
        self.tracking = {
            'enabled': True,
            'history_size': 100,  # número de cambios de precio a mantener
            'notify_changes': True,
            'min_change_percent': 0.05,  # 5%
            'max_change_percent': 0.50  # 50%
        }
        
        # Configuración de notificaciones
        self.notifications = {
            'enabled': True,
            'templates': {
                'price_change': 'notifications/price_change.html',
                'tier_upgrade': 'notifications/tier_upgrade.html',
                'tier_downgrade': 'notifications/tier_downgrade.html',
                'volume_discount': 'notifications/volume_discount.html'
            },
            'channels': {
                'email': {
                    'subject_prefix': '[Grupo huntRED®] ',
                    'from_email': 'precios@huntred.com'
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
                'volume',
                'base_price',
                'discount',
                'final_price'
            ],
            'field_validators': {
                'client_email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'volume': r'^\d+$',
                'base_price': r'^\d+(\.\d{2})?$',
                'discount': r'^\d+(\.\d{2})?$',
                'final_price': r'^\d+(\.\d{2})?$'
            },
            'min_volume': 1,
            'max_volume': 1000,
            'min_price': 0.01,
            'max_price': 1000000.00,
            'min_discount': 0.00,
            'max_discount': 0.50
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
                'prices': 730,  # días
                'history': 365,  # días
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
            'file': 'pricing.log',
            'max_size': 10485760,  # 10MB
            'backup_count': 5
        }
        
        # Validar la configuración
        self.validate()
    
    def validate(self) -> None:
        """Valida la configuración."""
        super().validate()
        
        # Validar precios progresivos
        if self.progressive['enabled']:
            if not self.progressive['tiers']:
                raise ValueError("La lista de niveles no puede estar vacía")
            for tier in self.progressive['tiers']:
                if not tier['name']:
                    raise ValueError("El nombre del nivel no puede estar vacío")
                if tier['min_volume'] <= 0:
                    raise ValueError("El volumen mínimo debe ser mayor que 0")
                if tier['max_volume'] is not None and tier['max_volume'] <= tier['min_volume']:
                    raise ValueError("El volumen máximo debe ser mayor que el mínimo")
                if tier['discount'] < 0 or tier['discount'] > 1:
                    raise ValueError("El descuento debe estar entre 0 y 1")
            if self.progressive['base_price'] <= 0:
                raise ValueError("El precio base debe ser mayor que 0")
            if not self.progressive['currency']:
                raise ValueError("La moneda no puede estar vacía")
            if self.progressive['decimal_places'] < 0:
                raise ValueError("El número de decimales no puede ser negativo")
            if self.progressive['rounding_mode'] not in ['HALF_UP', 'HALF_DOWN', 'UP', 'DOWN']:
                raise ValueError("Modo de redondeo inválido")
        
        # Validar precios por volumen
        if self.volume['enabled']:
            if not self.volume['tiers']:
                raise ValueError("La lista de niveles no puede estar vacía")
            for tier in self.volume['tiers']:
                if not tier['name']:
                    raise ValueError("El nombre del nivel no puede estar vacío")
                if tier['min_volume'] <= 0:
                    raise ValueError("El volumen mínimo debe ser mayor que 0")
                if tier['max_volume'] is not None and tier['max_volume'] <= tier['min_volume']:
                    raise ValueError("El volumen máximo debe ser mayor que el mínimo")
                if tier['price_per_unit'] <= 0:
                    raise ValueError("El precio por unidad debe ser mayor que 0")
            if not self.volume['currency']:
                raise ValueError("La moneda no puede estar vacía")
            if self.volume['decimal_places'] < 0:
                raise ValueError("El número de decimales no puede ser negativo")
            if self.volume['rounding_mode'] not in ['HALF_UP', 'HALF_DOWN', 'UP', 'DOWN']:
                raise ValueError("Modo de redondeo inválido")
        
        # Validar generación de propuestas
        if self.proposal['enabled']:
            if not self.proposal['templates_dir']:
                raise ValueError("El directorio de plantillas no puede estar vacío")
            if not self.proposal['output_dir']:
                raise ValueError("El directorio de salida no puede estar vacío")
            if self.proposal['max_retries'] < 0:
                raise ValueError("El número máximo de reintentos no puede ser negativo")
            if self.proposal['timeout'] <= 0:
                raise ValueError("El timeout debe ser mayor que 0")
            if self.proposal['batch_size'] <= 0:
                raise ValueError("El tamaño del lote debe ser mayor que 0")
            if self.proposal['concurrent_tasks'] <= 0:
                raise ValueError("El número de tareas concurrentes debe ser mayor que 0")
        
        # Validar seguimiento de precios
        if self.tracking['enabled']:
            if self.tracking['history_size'] <= 0:
                raise ValueError("El tamaño del historial debe ser mayor que 0")
            if self.tracking['min_change_percent'] < 0:
                raise ValueError("El porcentaje mínimo de cambio no puede ser negativo")
            if self.tracking['max_change_percent'] <= 0:
                raise ValueError("El porcentaje máximo de cambio debe ser mayor que 0")
            if self.tracking['min_change_percent'] >= self.tracking['max_change_percent']:
                raise ValueError("El porcentaje mínimo de cambio debe ser menor que el máximo")
        
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
            if self.validation['min_volume'] <= 0:
                raise ValueError("El volumen mínimo debe ser mayor que 0")
            if self.validation['max_volume'] <= 0:
                raise ValueError("El volumen máximo debe ser mayor que 0")
            if self.validation['min_price'] <= 0:
                raise ValueError("El precio mínimo debe ser mayor que 0")
            if self.validation['max_price'] <= 0:
                raise ValueError("El precio máximo debe ser mayor que 0")
            if self.validation['min_discount'] < 0:
                raise ValueError("El descuento mínimo no puede ser negativo")
            if self.validation['max_discount'] <= 0:
                raise ValueError("El descuento máximo debe ser mayor que 0")
            if self.validation['min_discount'] >= self.validation['max_discount']:
                raise ValueError("El descuento mínimo debe ser menor que el máximo")
        
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
    
    def get_tier_config(self, tier_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene la configuración de un nivel específico."""
        for tier in self.progressive['tiers']:
            if tier['name'] == tier_name:
                return tier
        return None
    
    def get_volume_tier_config(self, tier_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene la configuración de un nivel de volumen específico."""
        for tier in self.volume['tiers']:
            if tier['name'] == tier_name:
                return tier
        return None
    
    def get_template_config(self, template: str) -> Optional[str]:
        """Obtiene la configuración de una plantilla específica."""
        return self.notifications['templates'].get(template)
    
    def is_template_enabled(self, template: str) -> bool:
        """Verifica si una plantilla está habilitada."""
        return template in self.notifications['templates']
    
    def calculate_progressive_price(self, volume: int) -> float:
        """Calcula el precio progresivo para un volumen dado."""
        if not self.progressive['enabled']:
            return self.progressive['base_price']
        
        for tier in self.progressive['tiers']:
            if tier['min_volume'] <= volume and (tier['max_volume'] is None or volume <= tier['max_volume']):
                return self.progressive['base_price'] * (1 - tier['discount'])
        
        return self.progressive['base_price']
    
    def calculate_volume_price(self, volume: int) -> float:
        """Calcula el precio por volumen para un volumen dado."""
        if not self.volume['enabled']:
            return 0.0
        
        for tier in self.volume['tiers']:
            if tier['min_volume'] <= volume and (tier['max_volume'] is None or volume <= tier['max_volume']):
                return tier['price_per_unit'] * volume
        
        return 0.0 