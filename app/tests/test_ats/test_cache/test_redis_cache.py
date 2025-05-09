import unittest
from unittest.mock import patch, MagicMock
from app.ml.core.scheduling.cache import RedisCache

class TestRedisCache(unittest.TestCase):
    def setUp(self):
        self.cache = RedisCache()

    def test_cache_set_get(self):
        """Test de set y get"""
        key = "test_key"
        value = {"data": "test"}
        
        # Set value
        self.cache.set(key, value)
        
        # Get value
        result = self.cache.get(key)
        self.assertEqual(result, value)

    def test_cache_expiry(self):
        """Test de expiración"""
        key = "test_key_expiry"
        value = {"data": "test"}
        
        # Set with expiry
        self.cache.set(key, value, expiry=1)
        
        # Get immediately
        result = self.cache.get(key)
        self.assertEqual(result, value)
        
        # Wait and get again (should be expired)
        import time
        time.sleep(2)
        result = self.cache.get(key)
        self.assertIsNone(result)

    def test_cache_delete(self):
        """Test de eliminación"""
        key = "test_key_delete"
        value = {"data": "test"}
        
        # Set value
        self.cache.set(key, value)
        
        # Delete value
        self.cache.delete(key)
        
        # Verify deletion
        result = self.cache.get(key)
        self.assertIsNone(result)

    def test_cache_clear(self):
        """Test de limpieza"""
        # Set multiple values
        self.cache.set("key1", {"data": "test1"})
        self.cache.set("key2", {"data": "test2"})
        
        # Clear cache
        self.cache.clear()
        
        # Verify all keys are gone
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))

if __name__ == '__main__':
    unittest.main()
