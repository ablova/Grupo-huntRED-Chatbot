"""
Tests for the offer letter notification service.

These tests verify the functionality of the offer letter notification service,
including sending notifications for different offer letter events and handling
signed document delivery.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from django.test import TestCase
from asgiref.sync import sync_to_async
import os
import tempfile

from app.models import Person, Vacante, BusinessUnit, CartaOferta
from app.ats.services.notifications.offer_letter_notifications import (
    send_offer_letter_notification,
    send_signed_document
)

class TestOfferLetterNotifications(TestCase):
    """Test cases for offer letter notifications."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for all test methods."""
        cls.business_unit = BusinessUnit.objects.create(
            name="Test Business Unit",
            code="TEST"
        )
        
        cls.candidate = Person.objects.create(
            nombre="Test Candidate",
            email="candidate@example.com",
            phone="+525512345678",
            business_unit=cls.business_unit
        )
        
        cls.vacancy = Vacante.objects.create(
            titulo="Test Vacancy",
            descripcion="Test Description",
            business_unit=cls.business_unit
        )
        
        cls.offer_letter = CartaOferta.objects.create(
            user=cls.candidate,
            vacancy=cls.vacancy,
            salary=50000.00,
            benefits="Test Benefits",
            start_date="2025-01-01",
            end_date="2025-12-31",
            status="pending"
        )
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_send_offer_letter_notification(self):
        """Test sending an offer letter notification."""
        # Mock the notification service
        with patch('app.ats.services.notifications.offer_letter_notifications.get_notification_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.send_notification.return_value = {"email": True, "whatsapp": True}
            mock_get_service.return_value = mock_service
            
            # Send the notification
            result = await send_offer_letter_notification(
                offer_letter=self.offer_letter,
                notification_type="offer_sent",
                context={"additional": "context"}
            )
            
            # Verify the result
            assert result == {"email": True, "whatsapp": True}
            
            # Verify the notification service was called with the correct parameters
            mock_service.send_notification.assert_awaited_once()
            args, kwargs = mock_service.send_notification.await_args
            
            assert kwargs['recipient'] == self.candidate
            assert kwargs['notification_type'] == 'offer_letter_offer_sent'
            assert 'offer_letter' in kwargs['context']
            assert kwargs['context']['additional'] == 'context'
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_send_offer_letter_notification_with_specific_channels(self):
        """Test sending an offer letter notification with specific channels."""
        # Mock the notification service
        with patch('app.ats.services.notifications.offer_letter_notifications.get_notification_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.send_notification.return_value = {"email": True}
            mock_get_service.return_value = mock_service
            
            # Send the notification with specific channels
            result = await send_offer_letter_notification(
                offer_letter=self.offer_letter,
                notification_type="reminder",
                channels=["email"]
            )
            
            # Verify the result
            assert result == {"email": True}
            
            # Verify the notification service was called with the correct channels
            args, kwargs = mock_service.send_notification.await_args
            assert kwargs['channels'] == ["email"]
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_send_signed_document(self):
        """Test sending a signed document."""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(b"Test PDF content")
            temp_file_path = temp_file.name
        
        try:
            # Mock the notification service
            with patch('app.ats.services.notifications.offer_letter_notifications.get_notification_service') as mock_get_service:
                mock_service = AsyncMock()
                mock_service.send_notification.return_value = {"email": True}
                mock_get_service.return_value = mock_service
                
                # Send the signed document
                result = await send_signed_document(
                    offer_letter=self.offer_letter,
                    document_path=temp_file_path
                )
                
                # Verify the result
                assert result == {"email": True}
                
                # Verify the notification service was called with the correct parameters
                args, kwargs = mock_service.send_notification.await_args
                
                assert kwargs['recipient'] == self.candidate
                assert kwargs['notification_type'] == 'offer_letter_signed_document'
                assert 'offer_letter' in kwargs['context']
                assert 'attachments' in kwargs
                assert len(kwargs['attachments']) == 1
                assert kwargs['attachments'][0]['filename'] == os.path.basename(temp_file_path)
                
                # Verify the document was only sent via email
                assert kwargs['channels'] == ['email']
                
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_send_notification_with_metadata_update(self):
        """Test that notification metadata is updated after sending."""
        # Mock the notification service
        with patch('app.ats.services.notifications.offer_letter_notifications.get_notification_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.send_notification.return_value = {"email": True, "whatsapp": True}
            mock_get_service.return_value = mock_service
            
            # Initial state
            assert not self.offer_letter.notification_metadata
            
            # Send the notification
            await send_offer_letter_notification(
                offer_letter=self.offer_letter,
                notification_type="offer_sent"
            )
            
            # Refresh the offer letter from the database
            await sync_to_async(self.offer_letter.refresh_from_db)()
            
            # Verify the metadata was updated
            assert 'offer_sent' in self.offer_letter.notification_metadata
            assert self.offer_letter.notification_metadata['offer_sent']['success'] is True
            assert 'sent_at' in self.offer_letter.notification_metadata['offer_sent']
            assert 'channels' in self.offer_letter.notification_metadata['offer_sent']
    
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_force_resend_notification(self):
        """Test forcing resend of a notification that was already sent."""
        # Mock the notification service
        with patch('app.ats.services.notifications.offer_letter_notifications.get_notification_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.send_notification.return_value = {"email": True}
            mock_get_service.return_value = mock_service
            
            # Set up initial notification metadata
            self.offer_letter.notification_metadata = {
                "offer_sent": {
                    "sent_at": "2025-01-01T00:00:00Z",
                    "channels": ["email"],
                    "success": True
                }
            }
            await sync_to_async(self.offer_letter.save)()
            
            # Send the notification without force_send
            result1 = await send_offer_letter_notification(
                offer_letter=self.offer_letter,
                notification_type="offer_sent"
            )
            
            # Should not call send_notification (returns empty dict)
            assert result1 == {}
            mock_service.send_notification.assert_not_called()
            
            # Now force resend
            result2 = await send_offer_letter_notification(
                offer_letter=self.offer_letter,
                notification_type="offer_sent",
                force_send=True
            )
            
            # Should call send_notification
            assert result2 == {"email": True}
            mock_service.send_notification.assert_called_once()
            
            # Verify the metadata was updated with new timestamp
            await sync_to_async(self.offer_letter.refresh_from_db)()
            assert 'offer_sent' in self.offer_letter.notification_metadata
            assert self.offer_letter.notification_metadata['offer_sent']['sent_at'] != "2025-01-01T00:00:00Z"
