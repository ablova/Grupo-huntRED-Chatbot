# app/ats/integrations/notifications/core/service.py
"""
Core notification service for the Grupo huntRED® Chatbot.

This module provides the main NotificationService class that handles all
notification delivery through various channels.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from django.utils import timezone
from asgiref.sync import sync_to_async

from app.models import Person, Notification, BusinessUnit
from app.ats.integrations.notifications.channels import get_channel_class

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service for sending notifications through various channels.
    
    This service handles the delivery of notifications through multiple channels
    (email, WhatsApp, Telegram, etc.) with support for fallback channels and retries.
    """
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    async def send_notification(
        self,
        recipient: Person,
        template_name: str,
        channels: List[str] = None,
        context: Optional[Dict] = None,
        attachments: Optional[List[Dict]] = None,
        business_unit: Optional[BusinessUnit] = None,
        notification_type: Optional[str] = None,
        force_send: bool = False,
        **kwargs
    ) -> Dict[str, bool]:
        """
        Send a notification to the recipient through the specified channels.
        
        Args:
            recipient: The recipient of the notification
            template_name: Name of the template to use
            channels: List of channel names to use (e.g., ['email', 'whatsapp'])
            context: Context variables for the template
            attachments: List of file attachments
            business_unit: Optional business unit for the notification
            notification_type: Type of notification for tracking purposes
            force_send: If True, send even if a similar notification was recently sent
            
        Returns:
            Dict mapping channel names to success status (True/False)
        """
        if context is None:
            context = {}
            
        if channels is None:
            channels = ['email']  # Default channel
            
        results = {}
        
        for channel_name in channels:
            try:
                channel_class = get_channel_class(channel_name)
                if not channel_class:
                    logger.warning(f"Channel {channel_name} not found for notification {template_name}")
                    results[channel_name] = False
                    continue
                # Instantiate channel with provided BU or fallback to recipient's BU
                bu = business_unit or getattr(recipient, 'business_unit', None) or BusinessUnit.objects.first()
                try:
                    channel = channel_class(bu) if bu else channel_class()
                except Exception as inst_err:
                    logger.error(f"Error instantiating {channel_name} channel: {inst_err}")
                    results[channel_name] = False
                    continue
                if not channel:
                    logger.warning(f"Channel {channel_name} not found"
                                 f" for notification {template_name}")
                    results[channel_name] = False
                    continue
                
                # Check if we should skip this notification
                if not force_send and await self._should_skip_notification(
                    recipient, template_name, channel_name, notification_type
                ):
                    results[channel_name] = False
                    continue
                
                # Try to send the notification with retries
                success = await self._send_with_retry(
                    channel=channel,
                    recipient=recipient,
                    template_name=template_name,
                    context=context,
                    attachments=attachments,
                    business_unit=business_unit,
                    notification_type=notification_type
                )
                
                results[channel_name] = success
                
                # Log the notification
                await self._log_notification(
                    recipient=recipient,
                    channel=channel_name,
                    template_name=template_name,
                    status='sent' if success else 'failed',
                    notification_type=notification_type,
                    business_unit=business_unit
                )
                
            except Exception as e:
                logger.error(
                    f"Error sending {template_name} notification "
                    f"to {recipient} via {channel_name}: {str(e)}",
                    exc_info=True
                )
                results[channel_name] = False
                
                # Log the failed notification
                await self._log_notification(
                    recipient=recipient,
                    channel=channel_name,
                    template_name=template_name,
                    status='error',
                    error_message=str(e),
                    notification_type=notification_type,
                    business_unit=business_unit
                )
        
        return results
    
    async def _send_with_retry(
        self,
        channel,
        recipient: Person,
        template_name: str,
        context: Dict,
        attachments: List[Dict],
        business_unit: Optional[BusinessUnit],
        notification_type: Optional[str],
        retry_count: int = 0
    ) -> bool:
        """
        Send a notification with retry logic.
        
        Args:
            channel: The channel to use for sending
            recipient: The recipient of the notification
            template_name: Name of the template to use
            context: Context variables for the template
            attachments: List of file attachments
            business_unit: Optional business unit
            notification_type: Type of notification
            retry_count: Current retry attempt
            
        Returns:
            bool: True if sending was successful, False otherwise
        """
        try:
            return await channel.send(
                recipient=recipient,
                template_name=template_name,
                context=context,
                attachments=attachments,
                business_unit=business_unit,
                notification_type=notification_type
            )
        except Exception as e:
            if retry_count < self.max_retries:
                logger.warning(
                    f"Retry {retry_count + 1}/{self.max_retries} for "
                    f"{template_name} to {recipient} via {channel.name}"
                )
                await asyncio.sleep(self.retry_delay * (retry_count + 1))
                return await self._send_with_retry(
                    channel=channel,
                    recipient=recipient,
                    template_name=template_name,
                    context=context,
                    attachments=attachments,
                    business_unit=business_unit,
                    notification_type=notification_type,
                    retry_count=retry_count + 1
                )
            logger.error(
                f"Failed to send {template_name} to {recipient} "
                f"via {channel.name} after {self.max_retries} retries: {str(e)}",
                exc_info=True
            )
            return False
    
    @staticmethod
    async def _should_skip_notification(
        recipient: Person,
        template_name: str,
        channel_name: str,
        notification_type: Optional[str]
    ) -> bool:
        """
        Check if we should skip sending this notification.
        
        This can be used to implement rate limiting or deduplication.
        """
        # Skip if we've sent this notification recently
        # TODO: Implement rate limiting logic
        return False
    
    @staticmethod
    async def _log_notification(
        recipient: Person,
        channel: str,
        template_name: str,
        status: str,
        error_message: Optional[str] = None,
        notification_type: Optional[str] = None,
        business_unit: Optional[BusinessUnit] = None
    ) -> None:
        """
        Log a notification to the database.
        """
        try:
            notification = Notification(
                recipient=recipient,
                channel=channel,
                template_name=template_name,
                status=status,
                error_message=error_message,
                notification_type=notification_type,
                business_unit=business_unit,
                sent_at=timezone.now()
            )
            await sync_to_async(notification.save)()
        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}", exc_info=True)

# Singleton instance
notification_service = NotificationService()

def get_notification_service() -> NotificationService:
    """Get the global notification service instance."""
    return notification_service
