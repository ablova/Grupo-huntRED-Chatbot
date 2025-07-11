# app/ats/integrations/channels/whatsapp/__init__.py - Integración de WhatsApp para canales de chatbot.
# Optimización: Diseño modular para integración de canales de chatbot.
# Mejora: Diseño dinámico con herencia de clases para canales de chatbot, manteniendo nombres como 'whatsapp_webhook'.
# Type hints y comentarios para mejores prácticas.

from typing import Dict, Any, List  # Type hints para legibilidad y errores tempranos.
from .whatsapp import whatsapp_webhook  # Import dinámico desde whatsapp.py, asumiendo estructura.

"""
WhatsApp integration channel module.
Proporciona funcionalidades para envío y recepción de mensajes a través de WhatsApp.
"""

from .whatsapp import *
from .services import *
from .handler import *
from .webhook import *
from .whatsapp import whatsapp_webhook
