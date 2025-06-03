from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.core.cache import cache
from app.models import BusinessUnit, Person

class BaseHandler(ABC):
    """
    Clase base para todos los handlers de integración
    """
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.cache_timeout = 600  # 10 minutos

    @abstractmethod
    async def handle_message(self, message: Dict[str, Any]) -> bool:
        """
        Maneja un mensaje entrante
        """
        pass

    @abstractmethod
    async def send_message(self, user_id: str, message: str, options: Optional[list] = None) -> bool:
        """
        Envía un mensaje al usuario
        """
        pass

    @abstractmethod
    async def send_image(self, user_id: str, message: str, image_url: str) -> bool:
        """
        Envía una imagen al usuario
        """
        pass

    @abstractmethod
    async def send_document(self, user_id: str, file_url: str, caption: str) -> bool:
        """
        Envía un documento al usuario
        """
        pass

    @abstractmethod
    async def send_menu(self, user_id: str) -> bool:
        """
        Envía el menú al usuario
        """
        pass

    @abstractmethod
    async def send_options(self, user_id: str, message: str, buttons: Optional[list] = None) -> bool:
        """
        Envía opciones al usuario
        """
        pass

    async def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos del usuario desde la caché o los busca
        """
        cache_key = f"user_data_{self.__class__.__name__}_{user_id}"
        user_data = cache.get(cache_key)
        
        if not user_data:
            user_data = await self.fetch_user_data(user_id)
            if user_data:
                cache.set(cache_key, user_data, self.cache_timeout)
        
        return user_data

    @abstractmethod
    async def fetch_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca los datos del usuario en la plataforma
        """
        pass

    async def invalidate_cache(self, user_id: str) -> None:
        """
        Invalida la caché del usuario
        """
        cache_key = f"user_data_{self.__class__.__name__}_{user_id}"
        cache.delete(cache_key) 