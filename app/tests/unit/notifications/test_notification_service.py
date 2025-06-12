"""
Unit tests for the NotificationService class.

These tests verify the core functionality of the notification service
in isolation using mocks for external dependencies.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from django.test import TestCase

from app.ats.integrations.notifications.services.notification_service import NotificationService
from app.models import Person, BusinessUnit

class TestNotificationService(TestCase):
    """Test cases for NotificationService."""
    
    def setUp(self):
        """Set up test data."""
        self.person = Person.objects.create(
            nombre="Test User",
            email="test@example.com",
            phone="+525512345678"
        )
        self.business_unit = BusinessUnit.objects.create(
            name="Test BU",
            code="TEST"
        )
        self.notification_service = NotificationService()
    
    @patch('app.ats.integrations.notifications.services.notification_service.NotificationService._get_channel')
    async def test_send_notification_single_channel(self, mock_get_channel):
        """Test sending a notification through a single channel."""
        # Setup mock channel
        mock_channel = AsyncMock()
        mock_channel.send.return_value = True
        mock_get_channel.return_value = mock_channel
        
        # Test sending notification
        result = await self.notification_service.send_notification(
            recipient=self.person,
            template_name="test_template",
            channels=["email"]
        )
        
        # Verify results
        assert result == {"email": True}
        mock_channel.send.assert_called_once()
    
    @patch('app.ats.integrations.notifications.services.notification_service.NotificationService._get_channel')
    async def test_send_notification_multiple_channels(self, mock_get_channel):
        """Test sending a notification through multiple channels."""
        # Setup mock channel
        mock_channel = AsyncMock()
        mock_channel.send.return_value = True
        mock_get_channel.return_value = mock_channel
        
        # Test sending notification
        result = await self.notification_service.send_notification(
            recipient=self.person,
            template_name="test_template",
            channels=["email", "whatsapp"]
        )
        
        # Verify results
        assert result == {"email": True, "whatsapp": True}
        assert mock_channel.send.call_count == 2
    
    @patch('app.ats.integrations.notifications.services.notification_service.NotificationService._get_channel')
    async def test_send_notification_with_fallback(self, mock_get_channel):
        """Test sending a notification with fallback channels."""
        # Setup mock channels
        mock_primary = AsyncMock()
        mock_primary.send.side_effect = Exception("Channel error")
        
        mock_fallback = AsyncMock()
        mock_fallback.send.return_value = True
        
        def get_channel_side_effect(channel_name):
            if channel_name == "primary":
                return mock_primary
            return mock_fallback
            
        mock_get_channel.side_effect = get_channel_side_effect
        
        # Test sending notification with fallback
        result = await self.notification_service.send_notification(
            recipient=self.person,
            template_name="test_template",
            channels=["primary"],
            fallback_channels={"primary": ["email"]}
        )
        
        # Verify results
        assert result == {"primary": False, "email": True}
        mock_primary.send.assert_called_once()
        mock_fallback.send.assert_called_once()
    
    @patch('app.ats.integrations.notifications.services.notification_service.NotificationService._get_channel')
    async def test_send_notification_with_attachments(self, mock_get_channel):
        """Test sending a notification with attachments."""
        # Setup mock channel
        mock_channel = AsyncMock()
        mock_channel.send.return_value = True
        mock_get_channel.return_value = mock_channel
        
        # Test sending notification with attachments
        attachments = [
            {
                'filename': 'test.pdf',
                'content': b'test content',
                'mimetype': 'application/pdf'
            }
        ]
        
        result = await self.notification_service.send_notification(
            recipient=self.person,
            template_name="test_template",
            channels=["email"],
            attachments=attachments
        )
        
        # Verify results
        assert result == {"email": True}
        args, kwargs = mock_channel.send.call_args
        assert 'attachments' in kwargs
        assert kwargs['attachments'] == attachments

    @patch('app.ats.integrations.notifications.services.notification_service.NotificationService._get_channel')
    async def test_send_notification_with_context(self, mock_get_channel):
        """Test sending a notification with context variables."""
        # Setup mock channel
        mock_channel = AsyncMock()
        mock_channel.send.return_value = True
        mock_get_channel.return_value = mock_channel
        
        # Test sending notification with context
        context = {
            'user': {'name': 'Test User'},
            'offer': {'id': 123}
        }
        
        result = await self.notification_service.send_notification(
            recipient=self.person,
            template_name="test_template",
            channels=["email"],
            context=context
        )
        
        # Verify results
        assert result == {"email": True}
        args, kwargs = mock_channel.send.call_args
        assert 'context' in kwargs
        assert kwargs['context'] == context
        
    @patch('app.ats.integrations.notifications.services.notification_service.NotificationService._get_channel')
    async def test_send_notification_with_business_unit(self, mock_get_channel):
        """Test sending a notification with a specific business unit."""
        # Setup mock channel
        mock_channel = AsyncMock()
        mock_channel.send.return_value = True
        mock_get_channel.return_value = mock_channel
        
        # Test sending notification with business unit
        result = await self.notification_service.send_notification(
            recipient=self.person,
            template_name="test_template",
            channels=["email"],
            business_unit=self.business_unit
        )
        
        # Verify results
        assert result == {"email": True}
        args, kwargs = mock_channel.send.call_args
        assert 'business_unit' in kwargs
        assert kwargs['business_unit'] == self.business_unit
