# app/ats/integrations/services/message.py
"""
Message sending utilities for chatbot integrations.
This module contains functions for sending messages through different platforms
without creating circular imports.
"""
import logging
import asyncio
from typing import Optional, List, Dict, Any, Union
from functools import wraps
from datetime import datetime

from django.conf import settings
from asgiref.sync import sync_to_async
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models import BusinessUnit, MessageLog
# Imports de handlers movidos dentro de _get_handler para evitar importaciones
# circulares (por ejemplo InstagramHandler ↔︎ MessageService).

logger = logging.getLogger('chatbot')

def message_retry(max_attempts=3):
    """Decorador para reintentar operaciones de mensajería."""
    def decorator(func):
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            reraise=True
        )
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error en {func.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator

class MessageService:
    """Servicio para manejar el envío de mensajes a través de diferentes plataformas."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self._handlers = {}
    
    async def _get_handler(self, platform: str) -> Any:
        """Obtiene o crea el manejador para la plataforma especificada."""
        if platform not in self._handlers:
            if platform == 'telegram':
                from app.ats.integrations.channels.telegram.telegram import TelegramHandler
                self._handlers[platform] = TelegramHandler(self.business_unit)
            elif platform == 'whatsapp':
                from app.ats.integrations.channels.whatsapp.whatsapp import WhatsAppHandler
                self._handlers[platform] = WhatsAppHandler(self.business_unit)
            elif platform == 'slack':
                from app.ats.integrations.channels.slack.slack import SlackHandler
                self._handlers[platform] = SlackHandler(self.business_unit)
            elif platform == 'messenger':
                from app.ats.integrations.channels.messenger.messenger import MessengerHandler
                self._handlers[platform] = MessengerHandler(self.business_unit)
            elif platform == 'instagram':
                from app.ats.integrations.channels.instagram.instagram import InstagramHandler
                self._handlers[platform] = InstagramHandler(self.business_unit)
            elif platform == 'x':
                from app.ats.integrations.channels.x.x import XHandler
                self._handlers[platform] = XHandler(self.business_unit)
            else:
                raise ValueError(f"Plataforma no soportada: {platform}")
        
        return self._handlers[platform]
    
    @message_retry(max_attempts=3)
    async def send_message(
        self,
        platform: str,
        user_id: str,
        message: str,
        options: Optional[List[Dict]] = None,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Envía un mensaje a través de la plataforma especificada.
        
        Args:
            platform: Plataforma de destino (telegram, whatsapp, etc.)
            user_id: ID del usuario
            message: Mensaje a enviar
            options: Opciones adicionales (botones, etc.)
            priority: Prioridad del mensaje (0-5, donde 5 es la más alta)
        
        Returns:
            Dict con el resultado de la operación
        """
        try:
            handler = await self._get_handler(platform)
            
            # Registramos el intento de envío
            log = await sync_to_async(MessageLog.objects.create)(
                platform=platform,
                user_id=user_id,
                message=message,
                business_unit=self.business_unit,
                status='pending',
                priority=priority
            )
            
            # Enviamos el mensaje
            if options:
                result = await handler.send_options(user_id, message, options)
            else:
                result = await handler.send_message(user_id, message)
            
            # Actualizamos el log
            if result.get('success'):
                await sync_to_async(log.mark_as_sent)()
            else:
                await sync_to_async(log.mark_as_failed)(result.get('error'))
            
            return result
            
        except Exception as e:
            logger.error(f"Error enviando mensaje a {platform}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @message_retry(max_attempts=3)
    async def send_menu(
        self,
        platform: str,
        user_id: str,
        menu_type: str = 'main'
    ) -> Dict[str, Any]:
        """
        Envía el menú principal al usuario.
        
        Args:
            platform: Plataforma de destino
            user_id: ID del usuario
            menu_type: Tipo de menú a enviar
        
        Returns:
            Dict con el resultado de la operación
        """
        try:
            handler = await self._get_handler(platform)
            return await handler.send_menu(user_id, menu_type)
            
        except Exception as e:
            logger.error(f"Error enviando menú a {platform}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @message_retry(max_attempts=3)
    async def send_options(
        self,
        platform: str,
        user_id: str,
        message: str,
        options: List[Dict],
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Envía un mensaje con opciones interactivas.
        
        Args:
            platform: Plataforma de destino
            user_id: ID del usuario
            message: Mensaje a enviar
            options: Lista de opciones
            priority: Prioridad del mensaje
        
        Returns:
            Dict con el resultado de la operación
        """
        return await self.send_message(platform, user_id, message, options, priority)
    
    @message_retry(max_attempts=3)
    async def send_image(
        self,
        platform: str,
        user_id: str,
        message: str,
        image_url: str,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Envía una imagen al usuario.
        
        Args:
            platform: Plataforma de destino
            user_id: ID del usuario
            message: Mensaje a enviar
            image_url: URL de la imagen
            priority: Prioridad del mensaje
        
        Returns:
            Dict con el resultado de la operación
        """
        try:
            handler = await self._get_handler(platform)
            
            # Registramos el intento de envío
            log = await sync_to_async(MessageLog.objects.create)(
                platform=platform,
                user_id=user_id,
                message=message,
                business_unit=self.business_unit,
                status='pending',
                priority=priority,
                media_type='image',
                media_url=image_url
            )
            
            # Enviamos la imagen
            result = await handler.send_image(user_id, message, image_url)
            
            # Actualizamos el log
            if result.get('success'):
                await sync_to_async(log.mark_as_sent)()
            else:
                await sync_to_async(log.mark_as_failed)(result.get('error'))
            
            return result
            
        except Exception as e:
            logger.error(f"Error enviando imagen a {platform}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @message_retry(max_attempts=3)
    async def send_document(
        self,
        platform: str,
        user_id: str,
        message: str,
        document_url: str,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Envía un documento al usuario.
        
        Args:
            platform: Plataforma de destino
            user_id: ID del usuario
            message: Mensaje a enviar
            document_url: URL del documento
            priority: Prioridad del mensaje
        
        Returns:
            Dict con el resultado de la operación
        """
        try:
            handler = await self._get_handler(platform)
            
            # Registramos el intento de envío
            log = await sync_to_async(MessageLog.objects.create)(
                platform=platform,
                user_id=user_id,
                message=message,
                business_unit=self.business_unit,
                status='pending',
                priority=priority,
                media_type='document',
                media_url=document_url
            )
            
            # Enviamos el documento
            result = await handler.send_document(user_id, message, document_url)
            
            # Actualizamos el log
            if result.get('success'):
                await sync_to_async(log.mark_as_sent)()
            else:
                await sync_to_async(log.mark_as_failed)(result.get('error'))
            
            return result
            
        except Exception as e:
            logger.error(f"Error enviando documento a {platform}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Backwards-compatibility aliases para evitar ImportError en otros módulos
WhatsAppMessageService = MessageService  # type: ignore
TelegramMessageService = MessageService  # type: ignore
MessengerMessageService = MessageService  # type: ignore
InstagramMessageService = MessageService  # type: ignore
SlackMessageService = MessageService  # type: ignore

# Funciones de utilidad para compatibilidad con código existente

def get_message_service(business_unit: Optional[BusinessUnit] = None) -> MessageService:
    """Obtiene una instancia del servicio de mensajería."""
    if not business_unit:
        business_unit = BusinessUnit.objects.first()
    return MessageService(business_unit)

@message_retry(max_attempts=3)
async def send_message(
    platform: str,
    user_id: str,
    message: str,
    business_unit: Optional[BusinessUnit] = None
) -> Dict[str, Any]:
    """Envía un mensaje al usuario."""
    service = get_message_service(business_unit)
    return await service.send_message(platform, user_id, message)

@message_retry(max_attempts=3)
async def send_message_async(
    platform: str,
    user_id: str,
    message: str,
    business_unit: Optional[BusinessUnit] = None
) -> Dict[str, Any]:
    """Envía un mensaje de forma asíncrona."""
    return await send_message(platform, user_id, message, business_unit)

@message_retry(max_attempts=3)
async def send_menu(
    platform: str,
    user_id: str,
    business_unit: Optional[BusinessUnit] = None
) -> Dict[str, Any]:
    """Envía el menú principal al usuario."""
    service = get_message_service(business_unit)
    return await service.send_menu(platform, user_id)

@message_retry(max_attempts=3)
async def send_options(
    platform: str,
    user_id: str,
    message: str,
    buttons: Optional[List[Dict]] = None,
    business_unit: Optional[BusinessUnit] = None
) -> Dict[str, Any]:
    """Envía un mensaje con opciones interactivas."""
    service = get_message_service(business_unit)
    return await service.send_options(platform, user_id, message, buttons or [])

@message_retry(max_attempts=3)
async def send_smart_options(
    platform: str,
    user_id: str,
    message: str,
    options: List[Dict],
    business_unit: Optional[BusinessUnit] = None
) -> Dict[str, Any]:
    """Envía opciones interactivas de manera optimizada."""
    service = get_message_service(business_unit)
    return await service.send_options(platform, user_id, message, options)

@message_retry(max_attempts=3)
async def send_image(
    platform: str,
    user_id: str,
    message: str,
    image_url: str,
    business_unit: Optional[BusinessUnit] = None
) -> Dict[str, Any]:
    """Envía una imagen al usuario."""
    service = get_message_service(business_unit)
    return await service.send_image(platform, user_id, message, image_url)

@message_retry(max_attempts=3)
async def send_document(
    platform: str,
    user_id: str,
    message: str,
    document_url: str,
    business_unit: Optional[BusinessUnit] = None
) -> Dict[str, Any]:
    """Envía un documento al usuario."""
    service = get_message_service(business_unit)
    return await service.send_document(platform, user_id, message, document_url)
