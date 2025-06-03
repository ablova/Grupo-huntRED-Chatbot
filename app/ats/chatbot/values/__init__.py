"""
Paquete para manejar valores y principios fundamentales en el chatbot.

Este paquete contiene los módulos necesarios para gestionar los valores fundamentales
y principios que guían las interacciones del chatbot con los usuarios.
"""

# Importaciones principales para facilitar el acceso
try:
    from .core import ValuesPrinciples, UserPreferencesCache
    from .principles import *
    from .purpose import *
    from .integrations import *
    
    # Middleware de valores
    from .middleware import values_middleware
except ImportError as e:
    import logging
    logging.warning(f"Error al importar módulos de valores: {e}")
    
    # Definir un values_middleware por defecto para evitar errores de importación
    def values_middleware(func):
        return func

__all__ = [
    'ValuesPrinciples',
    'UserPreferencesCache',
    'values_middleware'
]
