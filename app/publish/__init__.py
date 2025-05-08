"""
Módulo de publicación y campañas digitales
"""

__version__ = "1.0.0"

# Registrar procesadores
from .processors import register_processors
register_processors()

# Registrar integraciones
from .integrations import register_integrations
register_integrations()
