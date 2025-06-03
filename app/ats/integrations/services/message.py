import logging
import aiohttp
import json
from typing import Optional, Dict, Any, List, Union
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import (
    MAX_RETRIES, REQUEST_TIMEOUT, CACHE_TIMEOUT,
    whatsapp_semaphore, apply_rate_limit, Button
)

logger = logging.getLogger('integrations')

class MessageService:
    """
    Servicio base para el envío de mensajes a través de diferentes plataformas
    """
    def __init__(self, api_instance: Any):
        self.api_instance = api_instance
        self.platform = api_instance.__class__.__name__.replace('API', '').lower()

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def send_message(
        self,
        user_id: str,
        message: Union[str, Dict[str, Any]],
        buttons: Optional[List[Button]] = None,
        template: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Envía un mensaje a través de la plataforma correspondiente
        """
        if not await apply_rate_limit(self.platform, user_id, message):
            logger.warning(f"Rate limit exceeded for {self.platform} user {user_id}")
            return False

        try:
            if isinstance(message, str):
                message = {"text": message}

            if buttons:
                message["buttons"] = [button.__dict__ for button in buttons]

            if template:
                message["template"] = template

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_instance.webhook_url,
                    json={
                        "recipient": {"id": user_id},
                        "message": message
                    },
                    timeout=REQUEST_TIMEOUT
                ) as response:
                    if response.status == 200:
                        return True
                    logger.error(f"Error sending message: {await response.text()}")
                    return False

        except Exception as e:
            logger.error(f"Error in send_message: {str(e)}")
            raise

    async def send_template(
        self,
        user_id: str,
        template_name: str,
        components: List[Dict[str, Any]]
    ) -> bool:
        """
        Envía un mensaje de plantilla
        """
        template = {
            "name": template_name,
            "language": {"code": "es"},
            "components": components
        }
        return await self.send_message(user_id, {}, template=template)

    async def send_document(
        self,
        user_id: str,
        document_url: str,
        caption: Optional[str] = None
    ) -> bool:
        """
        Envía un documento
        """
        message = {
            "attachment": {
                "type": "file",
                "payload": {
                    "url": document_url
                }
            }
        }
        if caption:
            message["caption"] = caption
        return await self.send_message(user_id, message)

class WhatsAppMessageService(MessageService):
    """
    Servicio específico para el envío de mensajes de WhatsApp
    """
    async def send_message(
        self,
        user_id: str,
        message: Union[str, Dict[str, Any]],
        buttons: Optional[List[Button]] = None,
        template: Optional[Dict[str, Any]] = None
    ) -> bool:
        async with whatsapp_semaphore:
            return await super().send_message(user_id, message, buttons, template)

class TelegramMessageService(MessageService):
    """
    Servicio específico para el envío de mensajes de Telegram
    """
    async def send_message(
        self,
        user_id: str,
        message: Union[str, Dict[str, Any]],
        buttons: Optional[List[Button]] = None,
        template: Optional[Dict[str, Any]] = None
    ) -> bool:
        # Implementación específica para Telegram
        return await super().send_message(user_id, message, buttons, template)

class MessengerMessageService(MessageService):
    """
    Servicio específico para el envío de mensajes de Messenger
    """
    async def send_message(
        self,
        user_id: str,
        message: Union[str, Dict[str, Any]],
        buttons: Optional[List[Button]] = None,
        template: Optional[Dict[str, Any]] = None
    ) -> bool:
        # Implementación específica para Messenger
        return await super().send_message(user_id, message, buttons, template)

class InstagramMessageService(MessageService):
    """
    Servicio específico para el envío de mensajes de Instagram
    """
    async def send_message(
        self,
        user_id: str,
        message: Union[str, Dict[str, Any]],
        buttons: Optional[List[Button]] = None,
        template: Optional[Dict[str, Any]] = None
    ) -> bool:
        # Implementación específica para Instagram
        return await super().send_message(user_id, message, buttons, template)

class SlackMessageService(MessageService):
    """
    Servicio específico para el envío de mensajes de Slack
    """
    async def send_message(
        self,
        user_id: str,
        message: Union[str, Dict[str, Any]],
        buttons: Optional[List[Button]] = None,
        template: Optional[Dict[str, Any]] = None
    ) -> bool:
        # Implementación específica para Slack
        return await super().send_message(user_id, message, buttons, template) 