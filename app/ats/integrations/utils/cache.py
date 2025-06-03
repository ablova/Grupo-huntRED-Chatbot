"""
Enhanced caching system for integrations.
Provides a robust caching mechanism with automatic key management and error handling.
"""

from typing import Any, Optional, Dict, List, Union
from django.core.cache import cache
from datetime import datetime, timedelta
import json
import hashlib
from .exceptions import CacheError
from .logging import get_integration_logger

logger = get_integration_logger(__name__)

class IntegrationCache:
    """
    Enhanced caching system for integration data.
    Provides automatic key management, error handling, and logging.
    """
    
    def __init__(self, prefix: str, default_timeout: int = 600):
        """
        Initialize the cache with a prefix and default timeout.
        
        Args:
            prefix: Prefix for all cache keys
            default_timeout: Default cache timeout in seconds
        """
        self.prefix = prefix
        self.default_timeout = default_timeout
        self.logger = logger
    
    def _generate_key(self, key: str) -> str:
        """
        Generate a cache key with the prefix.
        
        Args:
            key: Base key
            
        Returns:
            str: Full cache key with prefix
        """
        return f"{self.prefix}:{key}"
    
    def _generate_hash_key(self, data: Union[str, Dict, List]) -> str:
        """
        Generate a hash key from data.
        
        Args:
            data: Data to hash
            
        Returns:
            str: Hash key
        """
        if isinstance(data, (dict, list)):
            data = json.dumps(data, sort_keys=True)
        return hashlib.md5(str(data).encode()).hexdigest()
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get data from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Any: Cached data or default value
        """
        try:
            full_key = self._generate_key(key)
            data = cache.get(full_key)
            
            if data is None:
                self.logger.debug('cache_miss', {
                    'key': key,
                    'full_key': full_key
                })
                return default
                
            self.logger.debug('cache_hit', {
                'key': key,
                'full_key': full_key
            })
            return data
            
        except Exception as e:
            self.logger.error('cache_get_error', {
                'key': key,
                'error': str(e)
            })
            raise CacheError(f"Error getting cache data: {str(e)}")
    
    async def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        Set data in cache.
        
        Args:
            key: Cache key
            value: Data to cache
            timeout: Optional timeout in seconds
            
        Returns:
            bool: True if data was cached successfully
        """
        try:
            full_key = self._generate_key(key)
            cache.set(full_key, value, timeout or self.default_timeout)
            
            self.logger.debug('cache_set', {
                'key': key,
                'full_key': full_key,
                'timeout': timeout or self.default_timeout
            })
            return True
            
        except Exception as e:
            self.logger.error('cache_set_error', {
                'key': key,
                'error': str(e)
            })
            raise CacheError(f"Error setting cache data: {str(e)}")
    
    async def delete(self, key: str) -> bool:
        """
        Delete data from cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if data was deleted successfully
        """
        try:
            full_key = self._generate_key(key)
            cache.delete(full_key)
            
            self.logger.debug('cache_delete', {
                'key': key,
                'full_key': full_key
            })
            return True
            
        except Exception as e:
            self.logger.error('cache_delete_error', {
                'key': key,
                'error': str(e)
            })
            raise CacheError(f"Error deleting cache data: {str(e)}")
    
    async def get_or_set(self, key: str, default_func: callable, timeout: Optional[int] = None) -> Any:
        """
        Get data from cache or set it if not found.
        
        Args:
            key: Cache key
            default_func: Function to call if key not found
            timeout: Optional timeout in seconds
            
        Returns:
            Any: Cached data or result of default_func
        """
        try:
            data = await self.get(key)
            if data is not None:
                return data
                
            data = default_func()
            await self.set(key, data, timeout)
            return data
            
        except Exception as e:
            self.logger.error('cache_get_or_set_error', {
                'key': key,
                'error': str(e)
            })
            raise CacheError(f"Error in get_or_set: {str(e)}")
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dict[str, Any]: Dictionary of cached data
        """
        try:
            full_keys = [self._generate_key(key) for key in keys]
            data = cache.get_many(full_keys)
            
            # Convert full keys back to original keys
            result = {
                key.replace(f"{self.prefix}:", ""): value
                for key, value in data.items()
            }
            
            self.logger.debug('cache_get_many', {
                'keys': keys,
                'found_keys': list(result.keys())
            })
            return result
            
        except Exception as e:
            self.logger.error('cache_get_many_error', {
                'keys': keys,
                'error': str(e)
            })
            raise CacheError(f"Error getting multiple cache values: {str(e)}")
    
    async def set_many(self, data: Dict[str, Any], timeout: Optional[int] = None) -> bool:
        """
        Set multiple values in cache.
        
        Args:
            data: Dictionary of data to cache
            timeout: Optional timeout in seconds
            
        Returns:
            bool: True if all data was cached successfully
        """
        try:
            full_data = {
                self._generate_key(key): value
                for key, value in data.items()
            }
            cache.set_many(full_data, timeout or self.default_timeout)
            
            self.logger.debug('cache_set_many', {
                'keys': list(data.keys()),
                'timeout': timeout or self.default_timeout
            })
            return True
            
        except Exception as e:
            self.logger.error('cache_set_many_error', {
                'keys': list(data.keys()),
                'error': str(e)
            })
            raise CacheError(f"Error setting multiple cache values: {str(e)}")
    
    async def delete_many(self, keys: List[str]) -> bool:
        """
        Delete multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            bool: True if all data was deleted successfully
        """
        try:
            full_keys = [self._generate_key(key) for key in keys]
            cache.delete_many(full_keys)
            
            self.logger.debug('cache_delete_many', {
                'keys': keys
            })
            return True
            
        except Exception as e:
            self.logger.error('cache_delete_many_error', {
                'keys': keys,
                'error': str(e)
            })
            raise CacheError(f"Error deleting multiple cache values: {str(e)}")
    
    async def clear(self) -> bool:
        """
        Clear all cache data with the prefix.
        
        Returns:
            bool: True if cache was cleared successfully
        """
        try:
            # Get all keys with the prefix
            keys = cache.keys(f"{self.prefix}:*")
            if keys:
                cache.delete_many(keys)
            
            self.logger.debug('cache_clear', {
                'prefix': self.prefix,
                'keys_cleared': len(keys) if keys else 0
            })
            return True
            
        except Exception as e:
            self.logger.error('cache_clear_error', {
                'prefix': self.prefix,
                'error': str(e)
            })
            raise CacheError(f"Error clearing cache: {str(e)}")
    
    async def get_with_metadata(self, key: str) -> Dict[str, Any]:
        """
        Get data from cache with metadata.
        
        Args:
            key: Cache key
            
        Returns:
            Dict[str, Any]: Dictionary with data and metadata
        """
        try:
            full_key = self._generate_key(key)
            data = cache.get(full_key)
            
            if data is None:
                return {
                    'data': None,
                    'exists': False,
                    'timestamp': None
                }
            
            # Get metadata from cache
            meta_key = f"{full_key}:meta"
            metadata = cache.get(meta_key) or {}
            
            return {
                'data': data,
                'exists': True,
                'timestamp': metadata.get('timestamp'),
                'created_at': metadata.get('created_at'),
                'updated_at': metadata.get('updated_at'),
                'hits': metadata.get('hits', 0)
            }
            
        except Exception as e:
            self.logger.error('cache_get_metadata_error', {
                'key': key,
                'error': str(e)
            })
            raise CacheError(f"Error getting cache metadata: {str(e)}")
    
    async def set_with_metadata(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        Set data in cache with metadata.
        
        Args:
            key: Cache key
            value: Data to cache
            timeout: Optional timeout in seconds
            
        Returns:
            bool: True if data was cached successfully
        """
        try:
            full_key = self._generate_key(key)
            meta_key = f"{full_key}:meta"
            
            # Get existing metadata
            metadata = cache.get(meta_key) or {}
            
            # Update metadata
            now = datetime.utcnow().isoformat()
            metadata.update({
                'timestamp': now,
                'updated_at': now,
                'hits': metadata.get('hits', 0) + 1
            })
            
            if 'created_at' not in metadata:
                metadata['created_at'] = now
            
            # Set data and metadata
            cache.set(full_key, value, timeout or self.default_timeout)
            cache.set(meta_key, metadata, timeout or self.default_timeout)
            
            self.logger.debug('cache_set_metadata', {
                'key': key,
                'full_key': full_key,
                'timeout': timeout or self.default_timeout
            })
            return True
            
        except Exception as e:
            self.logger.error('cache_set_metadata_error', {
                'key': key,
                'error': str(e)
            })
            raise CacheError(f"Error setting cache metadata: {str(e)}") 