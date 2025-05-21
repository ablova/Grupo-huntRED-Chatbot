import pytest
from django.test import TestCase
from asgiref.sync import async_to_sync
from app.models import BusinessUnit
from app.com.chatbot.integrations.services import MessageService

class TestMessageService(TestCase):
    def setUp(self):
        self.business_unit = BusinessUnit.objects.create(
            name="test_unit",
            description="Test business unit"
        )
        self.service = MessageService(self.business_unit)

    def test_get_api_instance(self):
        """Test obtención de instancia de API"""
        api_instance = async_to_sync(self.service.get_api_instance)("whatsapp")
        assert api_instance is not None

    def test_send_message(self):
        """Test envío de mensaje"""
        result = async_to_sync(self.service.send_message)(
            "whatsapp",
            "test_user",
            "Test message"
        )
        assert result is True

    def test_rate_limiting(self):
        """Test limitación de tasa"""
        from app.com.chatbot.components.rate_limiter import RateLimiter
        
        limiter = RateLimiter(max_requests=1, time_window=1)
        
        # Primer intento debería pasar
        assert limiter.check_rate_limit("test_user") is True
        
        # Segundo intento debería fallar
        assert limiter.check_rate_limit("test_user") is False

    def test_message_caching(self):
        """Test caché de mensajes"""
        from app.com.chatbot.integrations.services import cache
        
        cache_key = "test_message_cache"
        message = "Test message"
        
        # Guardar en caché
        cache.set(cache_key, message, timeout=60)
        
        # Recuperar de caché
        cached_message = cache.get(cache_key)
        assert cached_message == message
