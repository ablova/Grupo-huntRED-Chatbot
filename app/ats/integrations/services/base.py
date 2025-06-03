import logging
import asyncio
import time
from typing import Optional, Dict, Any, List, Union, Tuple
from django.core.cache import cache
from tenacity import retry, stop_after_attempt, wait_exponential
from abc import ABC, abstractmethod
from datetime import datetime

from app.models import (
    BusinessUnit, ConfiguracionBU, WhatsAppAPI, TelegramAPI, SlackAPI,
    InstagramAPI, MessengerAPI, ChatState, Person
)

logger = logging.getLogger('integrations')

# Constantes globales
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10.0
CACHE_TIMEOUT = 600  # 10 minutos
whatsapp_semaphore = asyncio.Semaphore(10)

class UserDataFetcher(ABC):
    """
    Clase base para obtener datos de usuarios de diferentes plataformas
    """
    @abstractmethod
    async def fetch(self, user_id: str, api_instance: Any, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        pass

class WhatsAppUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: WhatsAppAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        # Implementación específica para WhatsApp
        pass

class TelegramUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: TelegramAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        # Implementación específica para Telegram
        pass

class MessengerUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: MessengerAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        # Implementación específica para Messenger
        pass

class InstagramUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: InstagramAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        # Implementación específica para Instagram
        pass

class SlackUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: SlackAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        # Implementación específica para Slack
        pass

class Button:
    """
    Clase para representar botones en mensajes
    """
    def __init__(self, title: str, payload: Optional[str] = None, url: Optional[str] = None):
        self.title = title
        self.payload = payload
        self.url = url

    @classmethod
    def from_dict(cls, button_dict: Dict) -> 'Button':
        return cls(
            title=button_dict.get('title', ''),
            payload=button_dict.get('payload'),
            url=button_dict.get('url')
        )

async def apply_rate_limit(platform: str, user_id: str, message: dict) -> bool:
    """
    Aplica límites de tasa para mensajes
    """
    cache_key = f"rate_limit:{platform}:{user_id}"
    last_message_time = cache.get(cache_key)
    
    if last_message_time:
        time_since_last = time.time() - last_message_time
        if time_since_last < 1.0:  # 1 segundo mínimo entre mensajes
            return False
            
    cache.set(cache_key, time.time(), CACHE_TIMEOUT)
    return True

async def get_business_unit(name: Optional[str] = None) -> Optional[BusinessUnit]:
    """
    Obtiene una unidad de negocio por nombre
    """
    try:
        if name:
            return await sync_to_async(BusinessUnit.objects.get)(name=name)
        return await sync_to_async(BusinessUnit.objects.first)()
    except BusinessUnit.DoesNotExist:
        return None

def run_async(func, *args, **kwargs):
    """
    Ejecuta una función asíncrona en un nuevo event loop
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(func(*args, **kwargs))
    finally:
        loop.close()

async def reset_chat_state(user_id: str, business_unit: BusinessUnit, platform: Optional[str] = None):
    """
    Reinicia el estado del chat para un usuario
    """
    try:
        if platform:
            await sync_to_async(ChatState.objects.filter)(
                user_id=user_id,
                business_unit=business_unit,
                platform=platform
            ).delete()
        else:
            await sync_to_async(ChatState.objects.filter)(
                user_id=user_id,
                business_unit=business_unit
            ).delete()
    except Exception as e:
        logger.error(f"Error reseteando estado del chat: {str(e)}") 