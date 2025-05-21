#!/usr/bin/env python3
# Script para probar las importaciones después de las modificaciones

import sys
import os

print("Iniciando prueba de importaciones...")

# Añadir el directorio raíz al path para permitir importaciones absolutas
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    print("Probando importación directa de RateLimiter...")
    from app.com.chatbot.components.rate_limiter import RateLimiter
    print("✅ Importación de RateLimiter exitosa")
except Exception as e:
    print(f"❌ Error al importar RateLimiter: {e}")

try:
    print("Probando importación directa de ChannelConfig...")
    from app.com.chatbot.components.channel_config import ChannelConfig
    print("✅ Importación de ChannelConfig exitosa")
except Exception as e:
    print(f"❌ Error al importar ChannelConfig: {e}")

try:
    print("Probando importación de WhatsAppHandler con sus nuevas dependencias...")
    from app.com.chatbot.integrations.whatsapp import WhatsAppHandler
    print("✅ Importación de WhatsAppHandler exitosa")
except Exception as e:
    print(f"❌ Error al importar WhatsAppHandler: {e}")

try:
    print("Probando importación de ChatStateManager con sus nuevas dependencias...")
    from app.com.chatbot.components.chat_state_manager import ChatStateManager
    print("✅ Importación de ChatStateManager exitosa")
except Exception as e:
    print(f"❌ Error al importar ChatStateManager: {e}")

print("Prueba de importaciones completada")
