# /home/pablo/app/com/chatbot/integrations/whatsapp.py
#
# Módulo para manejar la integración con WhatsApp Business API.
# Procesa mensajes entrantes, envía respuestas, y gestiona interacciones como botones y listas.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.
# Incluye soporte para carruseles de vacantes y manejo de documentos (CV).

import json
import logging
import asyncio
import httpx
import time
import os
from typing import Optional, Dict, Any, List
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.conf import settings
from asgiref.sync import sync_to_async
from tenacity import retry, stop_after_attempt, wait_exponential
from app.models import (
    Person, BusinessUnit, WhatsAppAPI, ChatState,
    ChatConversation, ChatMessage, Notification,
    Metric, WorkflowStatus, ChannelSettings
)
# Importaciones directas siguiendo estándares de Django

# Import at runtime to avoid circular imports
def get_intent_processor():
    from app.com.chatbot.intents_handler import IntentProcessor
    return IntentProcessor

from app.com.chatbot.integrations.enhanced_document_processor import EnhancedDocumentProcessor
from app.com.chatbot.middleware.message_retry import MessageRetry
from app.com.chatbot.integrations.services import MessageService

logger = logging.getLogger('chatbot')

# Configuraciones globales
REQUEST_TIMEOUT = 10.0
MAX_RETRIES = 3
CACHE_TIMEOUT = 600  # 10 minutos
whatsapp_semaphore = asyncio.Semaphore(10)

class WhatsAppHandler:
    """
    Manejador de integración con WhatsApp.
    
    Proporciona métodos para:
    - Enviar mensajes
    - Recibir mensajes
    - Procesar respuestas
    """
    
    def __init__(self):
        self.service = MessageService()
        self.retry = MessageRetry()
        
    async def send_message(self, message: Dict) -> bool:
        """
        Envía un mensaje a través de WhatsApp.
        
        Args:
            message: Mensaje a enviar
            
        Returns:
            bool indicando éxito
        """
        return await self.retry.process_message(message, self.service)
        
    async def receive_message(self, message: Dict) -> Dict:
        """
        Procesa un mensaje recibido de WhatsApp.
        
        Args:
            message: Mensaje recibido
            
        Returns:
            Dict con respuesta procesada
        """
        try:
            # Procesar mensaje
            response = await self.service.process_message(message)
            
            # Enviar respuesta
            await self.send_message(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }

@csrf_exempt
async def whatsapp_webhook(request):
    """Webhook para procesar mensajes entrantes de WhatsApp."""
    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

        payload = json.loads(request.body.decode("utf-8"))
        entry = payload.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        if not messages:
            return JsonResponse({"status": "success", "message": "No messages to process"}, status=200)

        message = messages[0]
        user_id = message.get('from')
        phone_number_id = value.get('metadata', {}).get('phone_number_id')
        business_unit = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
            phoneID=phone_number_id, is_active=True
        ).first().business_unit)()

        handler = WhatsAppHandler()
        response = await handler.receive_message(message)
        return JsonResponse({"status": "success", "response": response}, status=200)
    except Exception as e:
        logger.error(f"Error en whatsapp_webhook: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)