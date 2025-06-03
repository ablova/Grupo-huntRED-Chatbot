from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime
from app.ats.integrations.base.base_handler import BaseHandler
from app.ats.chatbot.services.response.generator import ResponseGenerator
from app.ats.config.settings.chatbot import CHATBOT_CONFIG

logger = logging.getLogger('integrations.whatsapp')

class WhatsAppHandler(BaseHandler):
    """
    Manejador de integración con WhatsApp.
    Proporciona métodos para enviar y recibir mensajes.
    """
    
    def __init__(self):
        super().__init__()
        self.response_generator = ResponseGenerator()
        self.last_message_time = None
        
    def _get_rate_limit(self) -> float:
        """
        Obtiene el límite de tasa para WhatsApp
        """
        return CHATBOT_CONFIG['RATE_LIMITING']['WHATSAPP']
        
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un mensaje entrante de WhatsApp
        """
        try:
            # Verificar límite de tasa
            await self._check_rate_limit()
            
            # Extraer información del mensaje
            user_id = message.get('from')
            message_type = message.get('type')
            content = message.get(message_type, {})
            
            # Procesar según el tipo de mensaje
            if message_type == 'text':
                response = await self._process_text_message(content)
            elif message_type == 'document':
                response = await self._process_document_message(content)
            else:
                response = {
                    'error': f'Tipo de mensaje no soportado: {message_type}',
                    'status': 'error'
                }
                
            return response
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }
            
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Envía un mensaje a través de WhatsApp
        """
        try:
            # Verificar límite de tasa
            await self._check_rate_limit()
            
            # Enviar mensaje
            # TODO: Implementar envío real a WhatsApp
            return True
            
        except Exception as e:
            logger.error(f"Error enviando mensaje: {str(e)}")
            return False
            
    async def _check_rate_limit(self):
        """
        Verifica y aplica límite de tasa
        """
        if self.last_message_time:
            time_since_last = (datetime.now() - self.last_message_time).total_seconds()
            if time_since_last < self.rate_limit:
                await asyncio.sleep(self.rate_limit - time_since_last)
        self.last_message_time = datetime.now()
        
    async def _process_text_message(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un mensaje de texto
        """
        text = content.get('body', '')
        return self.response_generator.generate_response(text)
        
    async def _process_document_message(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un mensaje con documento
        """
        # TODO: Implementar procesamiento de documentos
        return {
            'message': 'Documento recibido',
            'status': 'success'
        } 