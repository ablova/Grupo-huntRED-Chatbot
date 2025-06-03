"""
Base service class for all integration services.
Provides common functionality and interface for all platform-specific services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from django.core.cache import cache
import logging
import json
from datetime import datetime
from app.models import BusinessUnit, Person

logger = logging.getLogger(__name__)

class BaseService(ABC):
    """
    Base service class that defines the interface for all integration services.
    Provides common functionality for message handling, caching, and error management.
    """
    
    def __init__(self, business_unit: Any):
        """
        Initialize the service with a business unit.
        
        Args:
            business_unit: The business unit this service is associated with
        """
        self.business_unit = business_unit
        self.cache_timeout = 600  # 10 minutes default
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
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
            return cache.get(key)
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
            cache.set(key, data, timeout or self.cache_timeout)
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
            cache.delete(key)
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

    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Handle errors with standardized format and logging.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
        """
        try:
            error_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'error_type': error.__class__.__name__,
                'error_message': str(error),
                'business_unit': getattr(self.business_unit, 'name', str(self.business_unit)),
                'context': context
            }
            self.logger.error(f"Service error: {json.dumps(error_data)}")
        except Exception as e:
            self.logger.error(f"Error handling error: {str(e)}")

class MessageService(BaseService):
    """
    Service for handling message-related operations.
    Extends BaseService with message-specific functionality.
    """
    
    @abstractmethod
    async def send_smart_options(self, platform: str, user_id: str, message: str, options: List[Dict[str, Any]]) -> bool:
        """
        Send smart options to a user.
        Must be implemented by subclasses.
        
        Args:
            platform: The platform identifier
            user_id: The user's ID
            message: The message to send
            options: List of smart options
            
        Returns:
            bool: True if options were sent successfully
        """
        pass

class UserDataService(BaseService):
    """
    Service for handling user data operations.
    Extends BaseService with user data-specific functionality.
    """
    
    @abstractmethod
    async def fetch_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user data from the platform.
        Must be implemented by subclasses.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Optional[Dict[str, Any]]: User data or None if not found
        """
        pass
    
    @abstractmethod
    async def update_user_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """
        Update user data on the platform.
        Must be implemented by subclasses.
        
        Args:
            user_id: The user's ID
            data: Data to update
            
        Returns:
            bool: True if update was successful
        """
        pass 