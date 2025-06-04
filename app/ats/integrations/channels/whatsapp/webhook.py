from typing import Dict, Any
import logging
from app.ats.integrations.base.webhooks import BaseWebhook
from app.ats.integrations.channels.whatsapp.handler import WhatsAppHandler
from app.ats.config.settings.chatbot import CHATBOT_CONFIG

logger = logging.getLogger('integrations.whatsapp')

class WhatsAppWebhook(BaseWebhook):
    """
    Manejador de webhooks de WhatsApp.
    Procesa eventos entrantes de la API de WhatsApp Business.
    """
    
    def __init__(self):
        super().__init__(secret_key=CHATBOT_CONFIG.get('WHATSAPP_WEBHOOK_SECRET'))
        self.handler = WhatsAppHandler()
        
    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja un webhook entrante de WhatsApp
        """
        try:
            # Extraer mensaje del payload
            entry = payload.get('entry', [])[0]
            changes = entry.get('changes', [])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])
            
            if not messages:
                return {
                    'status': 'success',
                    'message': 'No messages to process'
                }
                
            # Procesar mensaje
            message = messages[0]
            response = await self.handler.handle_message(message)
            
            return {
                'status': 'success',
                'response': response
            }
            
        except Exception as e:
            logger.error(f"Error en webhook de WhatsApp: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
            
    def extract_payload(self, request: HttpRequest) -> Dict[str, Any]:
        """
        Extrae el payload del webhook de WhatsApp
        """
        try:
            payload = super().extract_payload(request)
            
            # Verificar estructura del payload
            if not payload.get('entry'):
                raise ValueError("Payload inválido: falta 'entry'")
                
            return payload
            
        except Exception as e:
            logger.error(f"Error extrayendo payload de WhatsApp: {str(e)}")
            return {} 