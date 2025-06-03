"""
Módulo de configuración del sistema.

Este módulo proporciona una interfaz centralizada para acceder a la configuración
de toda la aplicación. Utiliza un sistema de configuración basado en clases con
validación de tipos y valores por defecto.
"""

from .settings import settings
from .base import BaseConfig, Environment
from .features.ats import ATSConfig

__all__ = [
    'settings',
    'BaseConfig',
    'Environment',
    'ATSConfig'
] 