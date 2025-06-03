"""
Configuración del módulo de propuestas.

Este módulo proporciona acceso a la configuración específica del módulo de propuestas
utilizando la configuración global del sistema.
"""

from app.config import settings

# Exportar la configuración de propuestas
PROPOSALS_CONFIG = settings.proposals

# Exportar configuraciones específicas
GENERATION_CONFIG = PROPOSALS_CONFIG.generation
TRACKING_CONFIG = PROPOSALS_CONFIG.tracking
NOTIFICATION_CONFIG = PROPOSALS_CONFIG.notifications
VALIDATION_CONFIG = PROPOSALS_CONFIG.validation
SECURITY_CONFIG = PROPOSALS_CONFIG.security
CACHE_CONFIG = PROPOSALS_CONFIG.cache
LOGGING_CONFIG = PROPOSALS_CONFIG.logging

# Exportar funciones de utilidad
def get_template_config(template: str):
    """Obtiene la configuración de una plantilla específica."""
    return PROPOSALS_CONFIG.get_template_config(template)

def is_template_enabled(template: str) -> bool:
    """Verifica si una plantilla está habilitada."""
    return PROPOSALS_CONFIG.is_template_enabled(template)

def is_state_valid(state: str) -> bool:
    """Verifica si un estado es válido."""
    return PROPOSALS_CONFIG.is_state_valid(state)

def is_transition_valid(from_state: str, to_state: str) -> bool:
    """Verifica si una transición es válida."""
    return PROPOSALS_CONFIG.is_transition_valid(from_state, to_state)

# Exportar todo
__all__ = [
    'PROPOSALS_CONFIG',
    'GENERATION_CONFIG',
    'TRACKING_CONFIG',
    'NOTIFICATION_CONFIG',
    'VALIDATION_CONFIG',
    'SECURITY_CONFIG',
    'CACHE_CONFIG',
    'LOGGING_CONFIG',
    'get_template_config',
    'is_template_enabled',
    'is_state_valid',
    'is_transition_valid'
] 