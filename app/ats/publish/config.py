"""
Configuración del módulo de publicación.

Este módulo proporciona acceso a la configuración específica del módulo de publicación
utilizando la configuración global del sistema.
"""

from app.config import settings

# Exportar la configuración de publicación
PUBLISH_CONFIG = settings.publish

# Exportar configuraciones específicas
CHANNEL_CONFIG = PUBLISH_CONFIG.channels
PROCESSING_CONFIG = PUBLISH_CONFIG.processing
SCHEDULING_CONFIG = PUBLISH_CONFIG.scheduling
NOTIFICATION_CONFIG = PUBLISH_CONFIG.notifications
VALIDATION_CONFIG = PUBLISH_CONFIG.validation
SECURITY_CONFIG = PUBLISH_CONFIG.security
CACHE_CONFIG = PUBLISH_CONFIG.cache
LOGGING_CONFIG = PUBLISH_CONFIG.logging

# Exportar funciones de utilidad
def get_channel_config(channel: str):
    """Obtiene la configuración de un canal específico."""
    return PUBLISH_CONFIG.get_channel_config(channel)

def is_channel_enabled(channel: str) -> bool:
    """Verifica si un canal está habilitado."""
    return PUBLISH_CONFIG.is_channel_enabled(channel)

def get_template_config(template: str):
    """Obtiene la configuración de una plantilla específica."""
    return PUBLISH_CONFIG.get_template_config(template)

def is_template_enabled(template: str) -> bool:
    """Verifica si una plantilla está habilitada."""
    return PUBLISH_CONFIG.is_template_enabled(template)

def is_content_type_valid(content_type: str) -> bool:
    """Verifica si un tipo de contenido es válido."""
    return PUBLISH_CONFIG.is_content_type_valid(content_type)

def is_format_valid(content_type: str, format: str) -> bool:
    """Verifica si un formato es válido para un tipo de contenido."""
    return PUBLISH_CONFIG.is_format_valid(content_type, format)

# Exportar todo
__all__ = [
    'PUBLISH_CONFIG',
    'CHANNEL_CONFIG',
    'PROCESSING_CONFIG',
    'SCHEDULING_CONFIG',
    'NOTIFICATION_CONFIG',
    'VALIDATION_CONFIG',
    'SECURITY_CONFIG',
    'CACHE_CONFIG',
    'LOGGING_CONFIG',
    'get_channel_config',
    'is_channel_enabled',
    'get_template_config',
    'is_template_enabled',
    'is_content_type_valid',
    'is_format_valid'
]
