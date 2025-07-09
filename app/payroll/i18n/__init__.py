"""
Inicializador del paquete de internacionalización
"""

from app.payroll.i18n.whatsapp_messages import (
    get_message, 
    get_button_text, 
    detect_language,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE
)

__all__ = [
    'get_message',
    'get_button_text',
    'detect_language',
    'SUPPORTED_LANGUAGES',
    'DEFAULT_LANGUAGE'
]
