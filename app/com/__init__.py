"""Módulo com - Componentes y utilidades comunes."""

from app.imports import imports

# Registrar los submódulos para importación perezosa
imports.add_lazy_module('chatbot', 'app.com.chatbot')
imports.add_lazy_module('utils', 'app.com.utils')
imports.add_lazy_module('pagos', 'app.com.pagos')
imports.add_lazy_module('publish', 'app.com.publish')
imports.add_lazy_module('notifications', 'app.com.notifications')
imports.add_lazy_module('onboarding', 'app.com.onboarding')

__all__ = [
    'chatbot',
    'utils',
    'pagos',
    'publish',
    'notifications',
    'onboarding'
]

# Definir los getters para cada submódulo
def get_chatbot():
    """Obtiene el módulo chatbot."""
    return imports.get_module('chatbot')

def get_utils():
    """Obtiene el módulo utils."""
    return imports.get_module('utils')

def get_pagos():
    """Obtiene el módulo pagos."""
    return imports.get_module('pagos')

def get_publish():
    """Obtiene el módulo publish."""
    return imports.get_module('publish')

def get_notifications():
    """Obtiene el módulo notifications."""
    return imports.get_module('notifications')

def get_onboarding():
    """Obtiene el módulo onboarding."""
    return imports.get_module('onboarding') 