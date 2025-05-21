"""
Módulo de Valores Fundamentales para el Chatbot.

Este paquete proporciona las herramientas necesarias para integrar los valores
del Grupo huntRED® en las interacciones del chatbot, incluyendo detección de
contexto emocional, personalización de mensajes y gestión de preferencias de usuario.
"""

from .core import ValuesPrinciples, UserPreferencesCache
from .integrations import ValuesChatMiddleware

# Instancia global para uso en todo el sistema
values_principles = ValuesPrinciples()
values_middleware = ValuesChatMiddleware(values_principles)

# Exportar la API pública
__all__ = [
    'ValuesPrinciples',
    'UserPreferencesCache',
    'ValuesChatMiddleware',
    'values_principles',
    'values_middleware'
]
