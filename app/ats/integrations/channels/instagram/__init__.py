# app/ats/integrations/channels/instagram/__init__.py - Integración de Instagram para canales de chatbot.
# Optimización: Diseño modular para integración de canales de chatbot.
# Mejora: Diseño dinámico con herencia de clases para canales de chatbot, manteniendo nombres como 'instagram_webhook'.
# Type hints y comentarios para mejores prácticas.

from typing import Dict, Any, List  # Type hints para legibilidad y errores tempranos.
from .instagram import instagram_webhook  # Import dinámico desde instagram.py, asumiendo estructura.

"""
Instagram integration channel module.
"""
from .instagram import instagram_webhook
