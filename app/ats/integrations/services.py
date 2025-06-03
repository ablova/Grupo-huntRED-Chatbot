from typing import Dict, Any, Optional, List
import logging
from django.core.cache import cache
from app.ats.integrations.channels.whatsapp.handler import WhatsAppHandler
from app.ats.integrations.channels.whatsapp.services import WhatsAppService
from app.ats.config.settings.chatbot import CHATBOT_CONFIG

logger = logging.getLogger('integrations')

# Instancias globales de handlers
_whatsapp_handler = None
_whatsapp_service = None

def get_whatsapp_handler() -> WhatsAppHandler:
    """
    Obtiene una instancia del handler de WhatsApp
    """
    global _whatsapp_handler
    if _whatsapp_handler is None:
        _whatsapp_handler = WhatsAppHandler()
    return _whatsapp_handler

def get_whatsapp_service() -> WhatsAppService:
    """
    Obtiene una instancia del servicio de WhatsApp
    """
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service

class MessageService:
    """
    Servicio unificado para el manejo de mensajes en diferentes canales
    """
    
    def __init__(self):
        self.whatsapp = get_whatsapp_service()
        
    async def send_message(self, channel: str, to: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía un mensaje a través del canal especificado
        """
        try:
            if channel == 'whatsapp':
                return await self.whatsapp.send_text_message(to, content.get('text', ''))
            else:
                raise ValueError(f"Canal no soportado: {channel}")
                
        except Exception as e:
            logger.error(f"Error enviando mensaje: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }
            
    async def send_template(self, channel: str, to: str, template_name: str,
                          parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Envía un mensaje usando una plantilla
        """
        try:
            if channel == 'whatsapp':
                return await self.whatsapp.send_template_message(to, template_name, parameters)
            else:
                raise ValueError(f"Canal no soportado: {channel}")
                
        except Exception as e:
            logger.error(f"Error enviando plantilla: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }
            
    async def send_document(self, channel: str, to: str, document_url: str,
                          caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Envía un documento
        """
        try:
            if channel == 'whatsapp':
                return await self.whatsapp.send_document(to, document_url, caption)
            else:
                raise ValueError(f"Canal no soportado: {channel}")
                
        except Exception as e:
            logger.error(f"Error enviando documento: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }

# Funciones de utilidad para compatibilidad con código existente
async def send_message(channel: str, to: str, content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función de utilidad para enviar mensajes
    """
    service = MessageService()
    return await service.send_message(channel, to, content)

async def send_template(channel: str, to: str, template_name: str,
                       parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Función de utilidad para enviar plantillas
    """
    service = MessageService()
    return await service.send_template(channel, to, template_name, parameters)

async def send_document(channel: str, to: str, document_url: str,
                       caption: Optional[str] = None) -> Dict[str, Any]:
    """
    Función de utilidad para enviar documentos
    """
    service = MessageService()
    return await service.send_document(channel, to, document_url, caption) 