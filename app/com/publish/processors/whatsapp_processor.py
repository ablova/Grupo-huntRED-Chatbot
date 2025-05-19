import httpx
from typing import Dict, Any
import logging
import httpx
from typing import Dict, Any
from django.conf import settings
from django.db import models
from app.com.publish.processors.base_processor import BaseProcessor
from app.com.publish.utils.content_adapters import WhatsAppAdapter

class WhatsAppProcessor(BaseProcessor):
    """
    Procesador para publicación en WhatsApp
    """
    def __init__(self, channel: Dict[str, Any]):
        super().__init__(channel)
        self.client = httpx.AsyncClient(timeout=30)
        
    async def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publica contenido en WhatsApp
        """
        # Adaptar contenido para WhatsApp
        adapter = WhatsAppAdapter(content)
        adapted_content = adapter.adapt()
        
        # Obtener configuración específica para esta unidad de negocio
        config = self._get_whatsapp_config()
        
        # Determinar el tipo de envío
        if self.channel['type'] == 'WHATSAPP_GROUP':
            return await self._send_to_group(adapted_content, config)
        elif self.channel['type'] == 'WHATSAPP_BROADCAST':
            return await self._send_to_broadcast(adapted_content, config)
        else:
            raise ValueError(f"Tipo de canal no soportado: {self.channel['type']}")
            
    async def get_analytics(self) -> Dict[str, Any]:
        """
        Obtiene métricas del canal
        """
        config = self._get_whatsapp_config()
        try:
            response = await self.client.get(
                f"{config['base_url']}{config['phone_id']}/message_statistics",
                headers={
                    "Authorization": f"Bearer {config['api_token']}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error getting WhatsApp analytics: {str(e)}")
            raise
            
    def _get_whatsapp_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración de WhatsApp para esta unidad de negocio
        """
        from app.models import WhatsAppAPI
        
        try:
            config = WhatsAppAPI.objects.get(
                business_unit=self.business_unit,
                is_active=True
            )
            return {
                'base_url': f'https://graph.facebook.com/{config.v_api}/',
                'api_token': config.api_token,
                'phone_id': config.phoneID
            }
        except WhatsAppAPI.DoesNotExist:
            self.logger.error(f"No se encontró configuración de WhatsApp para la unidad de negocio {self.business_unit.name}")
            raise
            
    async def _send_to_group(self, content: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía contenido a un grupo de WhatsApp
        """
        try:
            response = await self.client.post(
                f"{config['base_url']}{config['phone_id']}/messages",
                headers={
                    "Authorization": f"Bearer {config['api_token']}",
                    "Content-Type": "application/json"
                },
                json=content
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error sending to WhatsApp group: {str(e)}")
            raise
            
    async def _send_to_broadcast(self, content: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía contenido a una lista de difusión
        """
        try:
            response = await self.client.post(
                f"{config['base_url']}{config['phone_id']}/messages",
                headers={
                    "Authorization": f"Bearer {config['api_token']}",
                    "Content-Type": "application/json"
                },
                json=content
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error sending to WhatsApp broadcast: {str(e)}")
            raise
