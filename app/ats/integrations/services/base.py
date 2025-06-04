"""
Clase base para servicios de integración

Esta clase proporciona una interfaz común para la implementación de servicios
en diferentes plataformas de integración.
"""

import logging
import asyncio
import time
import json
from typing import Optional, Dict, Any, List, Union, Tuple
from django.core.cache import cache
from django.conf import settings
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

class RateLimiter:
    """Clase para manejar límites de tasa"""
    
    def __init__(self, max_requests: int, time_window: int):
        """
        Inicializa el limitador de tasa
        
        Args:
            max_requests: Máximo de requests permitidos
            time_window: Ventana de tiempo en segundos
        """
        self.max_requests = max_requests
        self.time_window = time_window
        
    async def acquire(self, key: str) -> bool:
        """
        Intenta adquirir un permiso para hacer una request
        
        Args:
            key: Clave única para el limitador
            
        Returns:
            bool: True si se adquirió el permiso
        """
        current = int(time.time())
        window_key = f"{key}:{current // self.time_window}"
        
        # Obtener contador actual
        count = cache.get(window_key, 0)
        
        if count >= self.max_requests:
            return False
            
        # Incrementar contador
        cache.set(window_key, count + 1, timeout=self.time_window)
        return True

class CircuitBreaker:
    """Clase para manejar circuit breakers"""
    
    def __init__(self, failure_threshold: int, reset_timeout: int):
        """
        Inicializa el circuit breaker
        
        Args:
            failure_threshold: Umbral de fallos antes de abrir
            reset_timeout: Tiempo de espera antes de resetear
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure = None
        self.is_open = False
        
    def record_success(self):
        """Registra un éxito"""
        self.failures = 0
        self.is_open = False
        
    def record_failure(self):
        """Registra un fallo"""
        self.failures += 1
        self.last_failure = time.time()
        
        if self.failures >= self.failure_threshold:
            self.is_open = True
            
    def can_execute(self) -> bool:
        """
        Verifica si se puede ejecutar una operación
        
        Returns:
            bool: True si se puede ejecutar
        """
        if not self.is_open:
            return True
            
        # Verificar si ha pasado el tiempo de reset
        if self.last_failure and time.time() - self.last_failure >= self.reset_timeout:
            self.is_open = False
            self.failures = 0
            return True
            
        return False

class DistributedCache:
    """Clase para manejar caché distribuido"""
    
    def __init__(self, default_timeout: int = 3600):
        """
        Inicializa el caché distribuido
        
        Args:
            default_timeout: Tiempo de expiración por defecto
        """
        self.default_timeout = default_timeout
        
    async def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del caché
        
        Args:
            key: Clave del valor
            
        Returns:
            Optional[Any]: Valor en caché o None
        """
        return cache.get(key)
        
    async def set(self, key: str, value: Any, timeout: Optional[int] = None):
        """
        Guarda un valor en caché
        
        Args:
            key: Clave del valor
            value: Valor a guardar
            timeout: Tiempo de expiración
        """
        cache.set(key, value, timeout or self.default_timeout)
        
    async def delete(self, key: str):
        """
        Elimina un valor del caché
        
        Args:
            key: Clave del valor
        """
        cache.delete(key)
        
    async def get_or_set(self, key: str, default: Any, timeout: Optional[int] = None) -> Any:
        """
        Obtiene un valor del caché o lo establece si no existe
        
        Args:
            key: Clave del valor
            default: Valor por defecto
            timeout: Tiempo de expiración
            
        Returns:
            Any: Valor en caché o default
        """
        value = await self.get(key)
        if value is None:
            await self.set(key, default, timeout)
            return default
        return value

class BaseService(ABC):
    """Clase base para servicios de integración"""
    
    def __init__(self, business_unit: Any):
        """
        Initialize the service with a business unit.
        
        Args:
            business_unit: The business unit this service is associated with
        """
        self.business_unit = business_unit
        self.cache_timeout = 600  # 10 minutes default
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.rate_limiter = RateLimiter(
            max_requests=getattr(settings, 'SERVICE_RATE_LIMIT', 100),
            time_window=getattr(settings, 'SERVICE_RATE_WINDOW', 60)
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=getattr(settings, 'SERVICE_FAILURE_THRESHOLD', 5),
            reset_timeout=getattr(settings, 'SERVICE_RESET_TIMEOUT', 60)
        )
        self.cache = DistributedCache(
            default_timeout=getattr(settings, 'SERVICE_CACHE_TIMEOUT', 3600)
        )
        
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the service and establish necessary connections.
        Must be implemented by subclasses.
        
        Returns:
            bool: True if initialization was successful
        """
        pass
    
    @abstractmethod
    async def get_api_instance(self) -> Any:
        """
        Get the API instance for the platform.
        Must be implemented by subclasses.
        
        Returns:
            Any: The API instance
        """
        pass
    
    @abstractmethod
    async def send_message(self, platform: str, user_id: str, message: str) -> bool:
        """
        Send a text message to a user.
        Must be implemented by subclasses.
        
        Args:
            platform: The platform identifier
            user_id: The user's ID
            message: The message to send
            
        Returns:
            bool: True if message was sent successfully
        """
        pass
    
    @abstractmethod
    async def send_image(self, platform: str, user_id: str, message: str, image_url: str) -> bool:
        """
        Send an image with optional caption to a user.
        Must be implemented by subclasses.
        
        Args:
            platform: The platform identifier
            user_id: The user's ID
            message: Optional caption for the image
            image_url: URL of the image to send
            
        Returns:
            bool: True if image was sent successfully
        """
        pass
    
    @abstractmethod
    async def send_document(self, platform: str, user_id: str, message: str, document_url: str) -> bool:
        """
        Send a document with optional caption to a user.
        Must be implemented by subclasses.
        
        Args:
            platform: The platform identifier
            user_id: The user's ID
            message: Optional caption for the document
            document_url: URL of the document to send
            
        Returns:
            bool: True if document was sent successfully
        """
        pass
    
    @abstractmethod
    async def send_menu(self, platform: str, user_id: str) -> bool:
        """
        Send the main menu to a user.
        Must be implemented by subclasses.
        
        Args:
            platform: The platform identifier
            user_id: The user's ID
            
        Returns:
            bool: True if menu was sent successfully
        """
        pass
    
    @abstractmethod
    async def send_options(self, platform: str, user_id: str, message: str, buttons: List[Dict[str, str]]) -> bool:
        """
        Send a message with interactive buttons to a user.
        Must be implemented by subclasses.
        
        Args:
            platform: The platform identifier
            user_id: The user's ID
            message: The message to send
            buttons: List of button configurations
            
        Returns:
            bool: True if options were sent successfully
        """
        pass

    async def get_cached_data(self, key: str) -> Optional[Any]:
        """
        Get data from cache with error handling.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached data or None if not found
        """
        try:
            return await self.cache.get(key)
        except Exception as e:
            self.logger.error(f"Error getting cached data for key {key}: {str(e)}")
            return None

    async def set_cached_data(self, key: str, data: Any, timeout: Optional[int] = None) -> bool:
        """
        Set data in cache with error handling.
        
        Args:
            key: Cache key
            data: Data to cache
            timeout: Optional timeout in seconds
            
        Returns:
            bool: True if data was cached successfully
        """
        try:
            await self.cache.set(key, data, timeout or self.cache_timeout)
            return True
        except Exception as e:
            self.logger.error(f"Error setting cached data for key {key}: {str(e)}")
            return False

    async def invalidate_cache(self, key: str) -> bool:
        """
        Invalidate cached data with error handling.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if cache was invalidated successfully
        """
        try:
            await self.cache.delete(key)
            return True
        except Exception as e:
            self.logger.error(f"Error invalidating cache for key {key}: {str(e)}")
            return False

    async def log_message_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Log message events with standardized format.
        
        Args:
            event_type: Type of event (e.g., 'message_sent', 'message_received')
            data: Event data
        """
        try:
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'business_unit': getattr(self.business_unit, 'name', str(self.business_unit)),
                'data': data
            }
            self.logger.info(f"Message event: {json.dumps(log_data)}")
        except Exception as e:
            self.logger.error(f"Error logging message event: {str(e)}")

    def rate_limit(self, key: str):
        """
        Decorator para aplicar rate limiting a métodos
        
        Args:
            key: Clave para el rate limiter
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                if not await self.rate_limiter.acquire(key):
                    raise Exception("Rate limit exceeded")
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def circuit_break(self):
        """
        Decorator para aplicar circuit breaker a métodos
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                if not self.circuit_breaker.can_execute():
                    raise Exception("Circuit breaker is open")
                try:
                    result = await func(*args, **kwargs)
                    self.circuit_breaker.record_success()
                    return result
                except Exception as e:
                    self.circuit_breaker.record_failure()
                    raise
            return wrapper
        return decorator

    def cached(self, key_prefix: str, timeout: Optional[int] = None):
        """
        Decorator para cachear resultados de métodos
        
        Args:
            key_prefix: Prefijo para la clave de caché
            timeout: Tiempo de expiración
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Generar clave única
                key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"
                
                # Intentar obtener de caché
                cached_result = await self.cache.get(key)
                if cached_result is not None:
                    return cached_result
                    
                # Ejecutar método
                result = await func(*args, **kwargs)
                
                # Guardar en caché
                await self.cache.set(key, result, timeout)
                
                return result
            return wrapper
        return decorator

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