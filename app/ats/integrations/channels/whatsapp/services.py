from typing import Dict, Any, Optional, List
import httpx
import logging
from app.ats.config.settings.chatbot import CHATBOT_CONFIG

logger = logging.getLogger('integrations.whatsapp')

class WhatsAppService:
    """
    Servicios específicos para la integración con WhatsApp.
    Maneja la comunicación con la API de WhatsApp Business.
    """
    
    def __init__(self):
        self.api_url = CHATBOT_CONFIG['WHATSAPP_API_URL']
        self.api_token = CHATBOT_CONFIG['WHATSAPP_API_TOKEN']
        self.phone_number_id = CHATBOT_CONFIG['WHATSAPP_PHONE_NUMBER_ID']
        
    async def send_text_message(self, to: str, text: str) -> Dict[str, Any]:
        """
        Envía un mensaje de texto
        """
        try:
            payload = {
                'messaging_product': 'whatsapp',
                'to': to,
                'type': 'text',
                'text': {
                    'body': text
                }
            }
            
            return await self._make_api_request('messages', payload)
            
        except Exception as e:
            logger.error(f"Error enviando mensaje de texto: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }
            
    async def send_template_message(self, to: str, template_name: str, 
                                  parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Envía un mensaje usando una plantilla
        """
        try:
            payload = {
                'messaging_product': 'whatsapp',
                'to': to,
                'type': 'template',
                'template': {
                    'name': template_name,
                    'language': {
                        'code': 'es'
                    },
                    'components': [
                        {
                            'type': 'body',
                            'parameters': parameters
                        }
                    ]
                }
            }
            
            return await self._make_api_request('messages', payload)
            
        except Exception as e:
            logger.error(f"Error enviando mensaje de plantilla: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }
            
    async def send_document(self, to: str, document_url: str, 
                          caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Envía un documento
        """
        try:
            payload = {
                'messaging_product': 'whatsapp',
                'to': to,
                'type': 'document',
                'document': {
                    'link': document_url
                }
            }
            
            if caption:
                payload['document']['caption'] = caption
                
            return await self._make_api_request('messages', payload)
            
        except Exception as e:
            logger.error(f"Error enviando documento: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            }
            
    async def _make_api_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza una petición a la API de WhatsApp
        """
        url = f"{self.api_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json() 