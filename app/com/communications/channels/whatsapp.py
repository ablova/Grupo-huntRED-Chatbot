"""
Integración con WhatsApp
Ubicación: /app/com/communications/channels/whatsapp.py
Responsabilidad: Manejo bidireccional de comunicación con WhatsApp

Created: 2025-05-15
Updated: 2025-05-15
"""

import asyncio
from app.config.settings.chatbot import CHATBOT_CONFIG
from app.com.chatbot.services.response.generator import ResponseGenerator

class WhatsAppHandler:
    def __init__(self):
        self.rate_limit = CHATBOT_CONFIG['RATE_LIMITING']['WHATSAPP']
        self.response_generator = ResponseGenerator()
        self.last_message_time = None

    async def handle_incoming(self, message, phone_number):
        """Maneja mensajes entrantes de WhatsApp"""
        await self._check_rate_limit()
        response = self._process_message(message)
        await self._send_response(response, phone_number)

    def _process_message(self, message):
        """Procesa el mensaje y genera respuesta"""
        return self.response_generator.generate_response(message)

    async def _send_response(self, response, phone_number):
        """Envía respuesta a WhatsApp"""
        # Implementación específica de envío
        pass

    async def _check_rate_limit(self):
        """Verifica y aplica límite de tasa"""
        if self.last_message_time:
            time_since_last = (datetime.now() - self.last_message_time).total_seconds()
            if time_since_last < self.rate_limit:
                await asyncio.sleep(self.rate_limit - time_since_last)
        self.last_message_time = datetime.now()
