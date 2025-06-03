"""
Configuración del módulo de pagos.

Este módulo proporciona acceso a la configuración específica del módulo de pagos
utilizando la configuración global del sistema.
"""

from app.config import settings

# Exportar la configuración de pagos
PAGOS_CONFIG = settings.pagos

# Exportar configuraciones específicas
GATEWAY_CONFIG = PAGOS_CONFIG.gateways
PROCESSING_CONFIG = PAGOS_CONFIG.processing
BILLING_CONFIG = PAGOS_CONFIG.billing
NOTIFICATION_CONFIG = PAGOS_CONFIG.notifications
SECURITY_CONFIG = PAGOS_CONFIG.security
CACHE_CONFIG = PAGOS_CONFIG.cache
LOGGING_CONFIG = PAGOS_CONFIG.logging

# Exportar funciones de utilidad
def get_gateway_config(gateway: str):
    """Obtiene la configuración de una pasarela específica."""
    return PAGOS_CONFIG.get_gateway_config(gateway)

def is_gateway_enabled(gateway: str) -> bool:
    """Verifica si una pasarela está habilitada."""
    return PAGOS_CONFIG.is_gateway_enabled(gateway)

def get_template_config(template: str):
    """Obtiene la configuración de una plantilla específica."""
    return PAGOS_CONFIG.get_template_config(template)

def is_template_enabled(template: str) -> bool:
    """Verifica si una plantilla está habilitada."""
    return PAGOS_CONFIG.is_template_enabled(template)

# Exportar todo
__all__ = [
    'PAGOS_CONFIG',
    'GATEWAY_CONFIG',
    'PROCESSING_CONFIG',
    'BILLING_CONFIG',
    'NOTIFICATION_CONFIG',
    'SECURITY_CONFIG',
    'CACHE_CONFIG',
    'LOGGING_CONFIG',
    'get_gateway_config',
    'is_gateway_enabled',
    'get_template_config',
    'is_template_enabled'
] 