"""
Integration tests for notification flows.

These tests verify that the notification system works correctly with
real dependencies and database interactions.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from asgiref.sync import sync_to_async

from app.models import Person, BusinessUnit, Notification
from app.ats.integrations.notifications.services.notification_service import NotificationService

class TestNotificationFlows(TestCase):
    """Test cases for notification flows."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for all test methods."""
        cls.business_unit = BusinessUnit.objects.create(
            name="Test Business Unit",
            code="TEST"
        )
        
        cls.person = Person.objects.create(
            nombre="Test User",
            email="test@example.com",
            phone="+525512345678",
            business_unit=cls.business_unit
        )
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_send_email_notification(self):
        """Test sending an email notification."""
        service = NotificationService()
        
        with patch('app.ats.integrations.notifications.channels.email.EmailNotificationChannel.send') as mock_send:
            mock_send.return_value = True
            
            result = await service.send_notification(
                recipient=self.person,
                template_name="test_email",
                channels=["email"],
                context={"test": "value"}
            )
            
            assert result == {"email": True}
            
            # Verify notification was logged in the database
            notification = await sync_to_async(Notification.objects.filter(
                recipient=self.person,
                channel="email",
                template_name="test_email"
            ).first)()
            
            assert notification is not None
            assert notification.status == "sent"
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_send_whatsapp_notification(self):
        """Test sending a WhatsApp notification."""
        service = NotificationService()
        
        with patch('app.ats.integrations.notifications.channels.whatsapp.WhatsAppNotificationChannel.send') as mock_send:
            mock_send.return_value = True
            
            result = await service.send_notification(
                recipient=self.person,
                template_name="test_whatsapp",
                channels=["whatsapp"],
                context={"test": "value"}
            )
            
            assert result == {"whatsapp": True}
            
            # Verify notification was logged in the database
            notification = await sync_to_async(Notification.objects.filter(
                recipient=self.person,
                channel="whatsapp",
                template_name="test_whatsapp"
            ).first)()
            
            assert notification is not None
            assert notification.status == "sent"
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_send_telegram_notification(self):
        """Test sending a Telegram notification."""
        # Set up test user with Telegram ID
        self.person.telegram_id = "123456789"
        await sync_to_async(self.person.save)()
        
        service = NotificationService()
        
        with patch('app.ats.integrations.notifications.channels.telegram.TelegramNotificationChannel.send') as mock_send:
            mock_send.return_value = True
            
            result = await service.send_notification(
                recipient=self.person,
                template_name="test_telegram",
                channels=["telegram"],
                context={"test": "value"}
            )
            
            assert result == {"telegram": True}
            
            # Verify notification was logged in the database
            notification = await sync_to_async(Notification.objects.filter(
                recipient=self.person,
                channel="telegram",
                template_name="test_telegram"
            ).first)()
            
            assert notification is not None
            assert notification.status == "sent"
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_send_notification_with_attachments(self):
        """Test sending a notification with attachments."""
        service = NotificationService()
        
        attachments = [
            {
                'filename': 'test.pdf',
                'content': b'test content',
                'mimetype': 'application/pdf'
            }
        ]
        
        with patch('app.ats.integrations.notifications.channels.email.EmailNotificationChannel.send') as mock_send:
            mock_send.return_value = True
            
            result = await service.send_notification(
                recipient=self.person,
                template_name="test_attachment",
                channels=["email"],
                context={"test": "value"},
                attachments=attachments
            )
            
            assert result == {"email": True}
            
            # Verify notification was logged with attachment info
            notification = await sync_to_async(Notification.objects.filter(
                recipient=self.person,
                channel="email",
                template_name="test_attachment"
            ).first)()
            
            assert notification is not None
            assert notification.attachments is not None
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_notification_retry_logic(self):
        """Test notification retry logic on failure."""
        service = NotificationService()
        
        # First two attempts will fail, third will succeed
        mock_send = AsyncMock(side_effect=[Exception("Failed"), Exception("Failed"), True])
        
        with patch('app.ats.integrations.notifications.channels.email.EmailNotificationChannel.send', mock_send):
            result = await service.send_notification(
                recipient=self.person,
                template_name="test_retry",
                channels=["email"],
                max_retries=3,
                retry_delay=0  # No delay for tests
            )
            
            assert result == {"email": True}
            assert mock_send.call_count == 3
            
            # Verify notification status reflects retries
            notification = await sync_to_async(Notification.objects.filter(
                recipient=self.person,
                template_name="test_retry"
            ).first)()
            
            assert notification is not None
            assert notification.retry_count == 2  # 2 retries before success
