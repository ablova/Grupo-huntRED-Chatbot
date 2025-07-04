"""
Unified Messaging Engine - Multi-Channel Communication Hub
800+ lines of advanced messaging orchestration
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
from abc import ABC, abstractmethod

import httpx
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioException

from ..config.settings import get_settings
from ..models.base import MessageChannel, MessagePriority, UserRole

settings = get_settings()
logger = logging.getLogger(__name__)


class MessageStatus(Enum):
    """Message delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    RETRYING = "retrying"


class MessageType(Enum):
    """Types of messages"""
    NOTIFICATION = "notification"
    ALERT = "alert"
    PAYSLIP = "payslip"
    REMINDER = "reminder"
    APPROVAL_REQUEST = "approval_request"
    MARKETING = "marketing"
    SYSTEM = "system"


@dataclass
class Message:
    """Universal message structure"""
    id: str
    recipient_id: str
    company_id: str
    message_type: MessageType
    priority: MessagePriority
    subject: str
    content: str
    channels: List[MessageChannel]
    template_id: Optional[str] = None
    template_variables: Dict[str, Any] = field(default_factory=dict)
    attachments: List[Dict[str, str]] = field(default_factory=list)
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    status: MessageStatus = MessageStatus.PENDING


@dataclass
class MessageDelivery:
    """Message delivery attempt record"""
    id: str
    message_id: str
    channel: MessageChannel
    status: MessageStatus
    provider_message_id: Optional[str] = None
    delivery_attempt: int = 1
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    response_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContactInfo:
    """Consolidated contact information"""
    employee_id: str
    company_id: str
    whatsapp_number: Optional[str] = None
    telegram_username: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    slack_user_id: Optional[str] = None
    teams_user_id: Optional[str] = None
    preferred_channel: MessageChannel = MessageChannel.WHATSAPP
    timezone: str = "America/Mexico_City"
    language: str = "es"
    do_not_disturb: bool = False
    do_not_disturb_hours: Dict[str, str] = field(default_factory=dict)


class MessageProvider(ABC):
    """Abstract base class for message providers"""
    
    @abstractmethod
    async def send_message(self, message: Message, contact: ContactInfo) -> MessageDelivery:
        """Send message through this provider"""
        pass
    
    @abstractmethod
    async def get_delivery_status(self, provider_message_id: str) -> MessageStatus:
        """Get delivery status from provider"""
        pass
    
    @abstractmethod
    def supports_channel(self, channel: MessageChannel) -> bool:
        """Check if provider supports the channel"""
        pass


class WhatsAppProvider(MessageProvider):
    """WhatsApp Business API provider using Twilio"""
    
    def __init__(self):
        self.client = TwilioClient(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
    
    async def send_message(self, message: Message, contact: ContactInfo) -> MessageDelivery:
        """Send WhatsApp message"""
        delivery = MessageDelivery(
            id=str(uuid.uuid4()),
            message_id=message.id,
            channel=MessageChannel.WHATSAPP,
            status=MessageStatus.PENDING
        )
        
        try:
            # Get company WhatsApp number
            from_number = await self._get_company_whatsapp_number(message.company_id)
            to_number = contact.whatsapp_number or contact.phone_number
            
            if not to_number:
                delivery.status = MessageStatus.FAILED
                delivery.error_message = "No WhatsApp number available"
                delivery.failed_at = datetime.now()
                return delivery
            
            # Send message
            twilio_message = self.client.messages.create(
                body=message.content,
                from_=f"whatsapp:{from_number}",
                to=f"whatsapp:{to_number}"
            )
            
            delivery.provider_message_id = twilio_message.sid
            delivery.status = MessageStatus.SENT
            delivery.sent_at = datetime.now()
            delivery.response_data = {
                "twilio_sid": twilio_message.sid,
                "status": twilio_message.status
            }
            
            logger.info(f"WhatsApp message sent: {twilio_message.sid}")
            
        except TwilioException as e:
            delivery.status = MessageStatus.FAILED
            delivery.error_message = str(e)
            delivery.failed_at = datetime.now()
            logger.error(f"WhatsApp send error: {e}")
        
        return delivery
    
    async def get_delivery_status(self, provider_message_id: str) -> MessageStatus:
        """Get WhatsApp delivery status from Twilio"""
        try:
            message = self.client.messages(provider_message_id).fetch()
            
            status_map = {
                "accepted": MessageStatus.PENDING,
                "queued": MessageStatus.PENDING,
                "sending": MessageStatus.PENDING,
                "sent": MessageStatus.SENT,
                "delivered": MessageStatus.DELIVERED,
                "read": MessageStatus.READ,
                "failed": MessageStatus.FAILED,
                "undelivered": MessageStatus.FAILED
            }
            
            return status_map.get(message.status, MessageStatus.PENDING)
            
        except Exception as e:
            logger.error(f"Error getting WhatsApp status: {e}")
            return MessageStatus.FAILED
    
    def supports_channel(self, channel: MessageChannel) -> bool:
        return channel == MessageChannel.WHATSAPP
    
    async def _get_company_whatsapp_number(self, company_id: str) -> str:
        """Get company's WhatsApp Business number"""
        # Mock implementation - would query company settings
        return "+14155238886"  # Twilio sandbox number


class TelegramProvider(MessageProvider):
    """Telegram Bot provider"""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def send_message(self, message: Message, contact: ContactInfo) -> MessageDelivery:
        """Send Telegram message"""
        delivery = MessageDelivery(
            id=str(uuid.uuid4()),
            message_id=message.id,
            channel=MessageChannel.TELEGRAM,
            status=MessageStatus.PENDING
        )
        
        try:
            if not contact.telegram_username:
                delivery.status = MessageStatus.FAILED
                delivery.error_message = "No Telegram username available"
                delivery.failed_at = datetime.now()
                return delivery
            
            # Get chat ID from username (simplified)
            chat_id = await self._get_chat_id(contact.telegram_username)
            
            if not chat_id:
                delivery.status = MessageStatus.FAILED
                delivery.error_message = "Could not find Telegram chat"
                delivery.failed_at = datetime.now()
                return delivery
            
            # Send message
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": message.content,
                        "parse_mode": "Markdown"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    delivery.provider_message_id = str(result["result"]["message_id"])
                    delivery.status = MessageStatus.SENT
                    delivery.sent_at = datetime.now()
                    delivery.response_data = result
                else:
                    delivery.status = MessageStatus.FAILED
                    delivery.error_message = f"HTTP {response.status_code}: {response.text}"
                    delivery.failed_at = datetime.now()
            
        except Exception as e:
            delivery.status = MessageStatus.FAILED
            delivery.error_message = str(e)
            delivery.failed_at = datetime.now()
            logger.error(f"Telegram send error: {e}")
        
        return delivery
    
    async def get_delivery_status(self, provider_message_id: str) -> MessageStatus:
        """Telegram doesn't provide detailed delivery status"""
        return MessageStatus.SENT
    
    def supports_channel(self, channel: MessageChannel) -> bool:
        return channel == MessageChannel.TELEGRAM
    
    async def _get_chat_id(self, username: str) -> Optional[str]:
        """Get Telegram chat ID from username"""
        # Simplified implementation - would maintain user mapping
        return "123456789"


class SMSProvider(MessageProvider):
    """SMS provider using Twilio"""
    
    def __init__(self):
        self.client = TwilioClient(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
    
    async def send_message(self, message: Message, contact: ContactInfo) -> MessageDelivery:
        """Send SMS message"""
        delivery = MessageDelivery(
            id=str(uuid.uuid4()),
            message_id=message.id,
            channel=MessageChannel.SMS,
            status=MessageStatus.PENDING
        )
        
        try:
            if not contact.phone_number:
                delivery.status = MessageStatus.FAILED
                delivery.error_message = "No phone number available"
                delivery.failed_at = datetime.now()
                return delivery
            
            # Send SMS
            twilio_message = self.client.messages.create(
                body=message.content[:160],  # SMS length limit
                from_=settings.TWILIO_PHONE_NUMBER,
                to=contact.phone_number
            )
            
            delivery.provider_message_id = twilio_message.sid
            delivery.status = MessageStatus.SENT
            delivery.sent_at = datetime.now()
            delivery.response_data = {
                "twilio_sid": twilio_message.sid,
                "status": twilio_message.status
            }
            
        except TwilioException as e:
            delivery.status = MessageStatus.FAILED
            delivery.error_message = str(e)
            delivery.failed_at = datetime.now()
            logger.error(f"SMS send error: {e}")
        
        return delivery
    
    async def get_delivery_status(self, provider_message_id: str) -> MessageStatus:
        """Get SMS delivery status"""
        try:
            message = self.client.messages(provider_message_id).fetch()
            
            status_map = {
                "accepted": MessageStatus.PENDING,
                "queued": MessageStatus.PENDING,
                "sending": MessageStatus.PENDING,
                "sent": MessageStatus.SENT,
                "delivered": MessageStatus.DELIVERED,
                "failed": MessageStatus.FAILED,
                "undelivered": MessageStatus.FAILED
            }
            
            return status_map.get(message.status, MessageStatus.PENDING)
            
        except Exception as e:
            logger.error(f"Error getting SMS status: {e}")
            return MessageStatus.FAILED
    
    def supports_channel(self, channel: MessageChannel) -> bool:
        return channel == MessageChannel.SMS


class EmailProvider(MessageProvider):
    """Email provider"""
    
    async def send_message(self, message: Message, contact: ContactInfo) -> MessageDelivery:
        """Send email message"""
        delivery = MessageDelivery(
            id=str(uuid.uuid4()),
            message_id=message.id,
            channel=MessageChannel.EMAIL,
            status=MessageStatus.PENDING
        )
        
        try:
            if not contact.email:
                delivery.status = MessageStatus.FAILED
                delivery.error_message = "No email address available"
                delivery.failed_at = datetime.now()
                return delivery
            
            # Mock email sending - would integrate with FastAPI-Mail or similar
            await self._send_email(
                to=contact.email,
                subject=message.subject,
                content=message.content,
                attachments=message.attachments
            )
            
            delivery.status = MessageStatus.SENT
            delivery.sent_at = datetime.now()
            delivery.provider_message_id = str(uuid.uuid4())
            
        except Exception as e:
            delivery.status = MessageStatus.FAILED
            delivery.error_message = str(e)
            delivery.failed_at = datetime.now()
            logger.error(f"Email send error: {e}")
        
        return delivery
    
    async def get_delivery_status(self, provider_message_id: str) -> MessageStatus:
        """Email delivery status (simplified)"""
        return MessageStatus.DELIVERED
    
    def supports_channel(self, channel: MessageChannel) -> bool:
        return channel == MessageChannel.EMAIL
    
    async def _send_email(self, to: str, subject: str, content: str, 
                         attachments: List[Dict[str, str]]):
        """Send email (mock implementation)"""
        logger.info(f"Sending email to {to}: {subject}")


class SlackProvider(MessageProvider):
    """Slack provider"""
    
    def __init__(self):
        self.bot_token = settings.SLACK_BOT_TOKEN
    
    async def send_message(self, message: Message, contact: ContactInfo) -> MessageDelivery:
        """Send Slack message"""
        delivery = MessageDelivery(
            id=str(uuid.uuid4()),
            message_id=message.id,
            channel=MessageChannel.SLACK,
            status=MessageStatus.PENDING
        )
        
        try:
            if not contact.slack_user_id:
                delivery.status = MessageStatus.FAILED
                delivery.error_message = "No Slack user ID available"
                delivery.failed_at = datetime.now()
                return delivery
            
            # Send Slack message
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {self.bot_token}"},
                    json={
                        "channel": contact.slack_user_id,
                        "text": message.content,
                        "username": "huntRED Bot"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        delivery.provider_message_id = result["ts"]
                        delivery.status = MessageStatus.SENT
                        delivery.sent_at = datetime.now()
                        delivery.response_data = result
                    else:
                        delivery.status = MessageStatus.FAILED
                        delivery.error_message = result.get("error", "Unknown Slack error")
                        delivery.failed_at = datetime.now()
                else:
                    delivery.status = MessageStatus.FAILED
                    delivery.error_message = f"HTTP {response.status_code}"
                    delivery.failed_at = datetime.now()
            
        except Exception as e:
            delivery.status = MessageStatus.FAILED
            delivery.error_message = str(e)
            delivery.failed_at = datetime.now()
            logger.error(f"Slack send error: {e}")
        
        return delivery
    
    async def get_delivery_status(self, provider_message_id: str) -> MessageStatus:
        """Slack delivery status (simplified)"""
        return MessageStatus.DELIVERED
    
    def supports_channel(self, channel: MessageChannel) -> bool:
        return channel == MessageChannel.SLACK


class TeamsProvider(MessageProvider):
    """Microsoft Teams provider"""
    
    async def send_message(self, message: Message, contact: ContactInfo) -> MessageDelivery:
        """Send Teams message"""
        delivery = MessageDelivery(
            id=str(uuid.uuid4()),
            message_id=message.id,
            channel=MessageChannel.TEAMS,
            status=MessageStatus.PENDING
        )
        
        try:
            if not contact.teams_user_id:
                delivery.status = MessageStatus.FAILED
                delivery.error_message = "No Teams user ID available"
                delivery.failed_at = datetime.now()
                return delivery
            
            # Mock Teams message sending
            # Would integrate with Microsoft Graph API
            delivery.status = MessageStatus.SENT
            delivery.sent_at = datetime.now()
            delivery.provider_message_id = str(uuid.uuid4())
            
            logger.info(f"Teams message sent to {contact.teams_user_id}")
            
        except Exception as e:
            delivery.status = MessageStatus.FAILED
            delivery.error_message = str(e)
            delivery.failed_at = datetime.now()
            logger.error(f"Teams send error: {e}")
        
        return delivery
    
    async def get_delivery_status(self, provider_message_id: str) -> MessageStatus:
        """Teams delivery status (simplified)"""
        return MessageStatus.DELIVERED
    
    def supports_channel(self, channel: MessageChannel) -> bool:
        return channel == MessageChannel.TEAMS


class MessageRouter:
    """Routes messages to appropriate channels based on priority and rules"""
    
    @staticmethod
    def determine_channels(message: Message, contact: ContactInfo,
                          company_settings: Dict[str, Any]) -> List[MessageChannel]:
        """Determine which channels to use for a message"""
        available_channels = []
        
        # Add available channels based on contact info
        if contact.whatsapp_number:
            available_channels.append(MessageChannel.WHATSAPP)
        if contact.telegram_username:
            available_channels.append(MessageChannel.TELEGRAM)
        if contact.phone_number:
            available_channels.append(MessageChannel.SMS)
        if contact.email:
            available_channels.append(MessageChannel.EMAIL)
        if contact.slack_user_id:
            available_channels.append(MessageChannel.SLACK)
        if contact.teams_user_id:
            available_channels.append(MessageChannel.TEAMS)
        
        # If specific channels requested, filter to those
        if message.channels:
            available_channels = [ch for ch in available_channels if ch in message.channels]
        
        # Apply routing rules based on priority and type
        if message.priority == MessagePriority.CRITICAL:
            # Critical messages: use all available channels
            return available_channels
        elif message.priority == MessagePriority.HIGH:
            # High priority: use preferred + one backup
            channels = [contact.preferred_channel]
            if len(available_channels) > 1:
                backup = next((ch for ch in available_channels if ch != contact.preferred_channel), None)
                if backup:
                    channels.append(backup)
            return channels
        else:
            # Normal/Low priority: use preferred channel only
            if contact.preferred_channel in available_channels:
                return [contact.preferred_channel]
            elif available_channels:
                return [available_channels[0]]
            else:
                return []
    
    @staticmethod
    def should_send_now(message: Message, contact: ContactInfo) -> bool:
        """Check if message should be sent now based on DND and scheduling"""
        # Check if scheduled for future
        if message.scheduled_for and message.scheduled_for > datetime.now():
            return False
        
        # Check if expired
        if message.expires_at and message.expires_at < datetime.now():
            return False
        
        # Check do not disturb
        if contact.do_not_disturb:
            # Critical messages override DND
            if message.priority == MessagePriority.CRITICAL:
                return True
            
            # Check DND hours
            if contact.do_not_disturb_hours:
                current_hour = datetime.now().hour
                start_hour = int(contact.do_not_disturb_hours.get("start", "22"))
                end_hour = int(contact.do_not_disturb_hours.get("end", "8"))
                
                if start_hour > end_hour:  # Overnight DND (e.g., 22:00 - 08:00)
                    if current_hour >= start_hour or current_hour <= end_hour:
                        return False
                else:  # Same day DND
                    if start_hour <= current_hour <= end_hour:
                        return False
        
        return True


class MessageTemplate:
    """Message template management"""
    
    TEMPLATES = {
        "payslip_ready": {
            "subject": "Tu recibo de nómina está listo",
            "content": "Hola {employee_name},\n\nTu recibo de nómina del período {period} está disponible.\n\nMonto neto: ${net_amount:,.2f}\n\nPuedes descargarlo desde la app.",
            "supported_channels": [MessageChannel.WHATSAPP, MessageChannel.EMAIL, MessageChannel.SMS]
        },
        "overtime_approved": {
            "subject": "Horas extra aprobadas",
            "content": "Tu solicitud de {hours} horas extra para {date} ha sido aprobada.\n\nMonto estimado: ${amount:,.2f}",
            "supported_channels": [MessageChannel.WHATSAPP, MessageChannel.TELEGRAM, MessageChannel.EMAIL]
        },
        "overtime_rejected": {
            "subject": "Solicitud de horas extra rechazada",
            "content": "Tu solicitud de horas extra para {date} ha sido rechazada.\n\nMotivo: {reason}",
            "supported_channels": [MessageChannel.WHATSAPP, MessageChannel.EMAIL]
        },
        "vacation_reminder": {
            "subject": "Recordatorio: días de vacaciones pendientes",
            "content": "Tienes {days} días de vacaciones pendientes que vencen el {expiry_date}.\n\n¿Deseas programar tus vacaciones?",
            "supported_channels": [MessageChannel.WHATSAPP, MessageChannel.EMAIL]
        },
        "birthday_wishes": {
            "subject": "¡Feliz cumpleaños!",
            "content": "🎉 ¡Feliz cumpleaños {employee_name}! 🎂\n\nTodo el equipo de {company_name} te desea un día maravilloso.",
            "supported_channels": [MessageChannel.WHATSAPP, MessageChannel.SLACK, MessageChannel.TEAMS]
        }
    }
    
    @classmethod
    def render_template(cls, template_id: str, variables: Dict[str, Any]) -> Tuple[str, str]:
        """Render message template with variables"""
        template = cls.TEMPLATES.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        try:
            subject = template["subject"].format(**variables)
            content = template["content"].format(**variables)
            return subject, content
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
    
    @classmethod
    def get_supported_channels(cls, template_id: str) -> List[MessageChannel]:
        """Get supported channels for a template"""
        template = cls.TEMPLATES.get(template_id)
        if not template:
            return []
        return template.get("supported_channels", [])


class UnifiedMessagingEngine:
    """Main Unified Messaging Engine"""
    
    def __init__(self):
        self.providers = {
            MessageChannel.WHATSAPP: WhatsAppProvider(),
            MessageChannel.TELEGRAM: TelegramProvider(),
            MessageChannel.SMS: SMSProvider(),
            MessageChannel.EMAIL: EmailProvider(),
            MessageChannel.SLACK: SlackProvider(),
            MessageChannel.TEAMS: TeamsProvider()
        }
        
        self.router = MessageRouter()
        self.template = MessageTemplate()
        self.retry_attempts = 3
        self.retry_delay = timedelta(minutes=5)
    
    async def send_message(self, message: Message) -> Dict[str, Any]:
        """Send message through unified messaging system"""
        try:
            # Get recipient contact info
            contact = await self._get_contact_info(message.recipient_id, message.company_id)
            if not contact:
                return {"success": False, "error": "Contact not found"}
            
            # Render template if specified
            if message.template_id:
                try:
                    subject, content = self.template.render_template(
                        message.template_id, message.template_variables
                    )
                    message.subject = subject
                    message.content = content
                except ValueError as e:
                    return {"success": False, "error": str(e)}
            
            # Get company settings
            company_settings = await self._get_company_settings(message.company_id)
            
            # Determine channels to use
            channels = self.router.determine_channels(message, contact, company_settings)
            if not channels:
                return {"success": False, "error": "No available channels"}
            
            # Check if should send now
            if not self.router.should_send_now(message, contact):
                # Schedule for later
                await self._schedule_message(message)
                return {"success": True, "status": "scheduled", "message_id": message.id}
            
            # Send through each channel
            deliveries = []
            for channel in channels:
                provider = self.providers.get(channel)
                if provider and provider.supports_channel(channel):
                    delivery = await provider.send_message(message, contact)
                    deliveries.append(delivery)
                    
                    # Save delivery record
                    await self._save_delivery(delivery)
            
            # Update message status
            if any(d.status == MessageStatus.SENT for d in deliveries):
                message.status = MessageStatus.SENT
            else:
                message.status = MessageStatus.FAILED
            
            await self._save_message(message)
            
            return {
                "success": True,
                "message_id": message.id,
                "deliveries": len(deliveries),
                "channels_used": [d.channel.value for d in deliveries]
            }
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {"success": False, "error": "System error occurred"}
    
    async def send_bulk_message(self, recipients: List[str], message_template: Dict[str, Any],
                              company_id: str) -> Dict[str, Any]:
        """Send message to multiple recipients"""
        try:
            results = {
                "total_recipients": len(recipients),
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            # Create messages for each recipient
            messages = []
            for recipient_id in recipients:
                message = Message(
                    id=str(uuid.uuid4()),
                    recipient_id=recipient_id,
                    company_id=company_id,
                    message_type=MessageType(message_template.get("type", "notification")),
                    priority=MessagePriority(message_template.get("priority", "normal")),
                    subject=message_template.get("subject", ""),
                    content=message_template.get("content", ""),
                    channels=[MessageChannel(ch) for ch in message_template.get("channels", [])],
                    template_id=message_template.get("template_id"),
                    template_variables=message_template.get("template_variables", {})
                )
                messages.append(message)
            
            # Send messages concurrently (in batches to avoid overwhelming)
            batch_size = 10
            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                tasks = [self.send_message(msg) for msg in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        results["failed"] += 1
                        results["errors"].append(str(result))
                    elif result.get("success"):
                        results["successful"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(result.get("error", "Unknown error"))
            
            return results
            
        except Exception as e:
            logger.error(f"Error sending bulk messages: {e}")
            return {"success": False, "error": "System error occurred"}
    
    async def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Get comprehensive message status"""
        try:
            # Get message
            message = await self._get_message(message_id)
            if not message:
                return {"error": "Message not found"}
            
            # Get all deliveries
            deliveries = await self._get_message_deliveries(message_id)
            
            # Update delivery statuses from providers
            for delivery in deliveries:
                if delivery.provider_message_id and delivery.status == MessageStatus.SENT:
                    provider = self.providers.get(delivery.channel)
                    if provider:
                        updated_status = await provider.get_delivery_status(
                            delivery.provider_message_id
                        )
                        if updated_status != delivery.status:
                            delivery.status = updated_status
                            await self._update_delivery_status(delivery)
            
            return {
                "message_id": message_id,
                "status": message.status.value,
                "created_at": message.created_at.isoformat(),
                "deliveries": [
                    {
                        "channel": d.channel.value,
                        "status": d.status.value,
                        "sent_at": d.sent_at.isoformat() if d.sent_at else None,
                        "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
                        "error": d.error_message
                    }
                    for d in deliveries
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting message status: {e}")
            return {"error": "System error occurred"}
    
    async def retry_failed_messages(self) -> Dict[str, Any]:
        """Retry failed message deliveries"""
        try:
            # Get failed deliveries that can be retried
            failed_deliveries = await self._get_retryable_deliveries()
            
            retried = 0
            successful = 0
            
            for delivery in failed_deliveries:
                if delivery.delivery_attempt >= self.retry_attempts:
                    continue
                
                # Get original message and contact
                message = await self._get_message(delivery.message_id)
                if not message:
                    continue
                
                contact = await self._get_contact_info(message.recipient_id, message.company_id)
                if not contact:
                    continue
                
                # Retry sending
                provider = self.providers.get(delivery.channel)
                if provider:
                    new_delivery = await provider.send_message(message, contact)
                    new_delivery.delivery_attempt = delivery.delivery_attempt + 1
                    
                    await self._save_delivery(new_delivery)
                    retried += 1
                    
                    if new_delivery.status == MessageStatus.SENT:
                        successful += 1
            
            return {
                "retried": retried,
                "successful": successful,
                "failed": retried - successful
            }
            
        except Exception as e:
            logger.error(f"Error retrying messages: {e}")
            return {"error": "System error occurred"}
    
    async def get_messaging_analytics(self, company_id: str,
                                    start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get messaging analytics for a company"""
        try:
            # Mock implementation - would query actual database
            return {
                "company_id": company_id,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "total_messages": 1250,
                "successful_deliveries": 1180,
                "failed_deliveries": 70,
                "delivery_rate": 94.4,
                "by_channel": {
                    "whatsapp": {"sent": 850, "delivered": 820, "rate": 96.5},
                    "email": {"sent": 250, "delivered": 240, "rate": 96.0},
                    "sms": {"sent": 100, "delivered": 85, "rate": 85.0},
                    "telegram": {"sent": 50, "delivered": 35, "rate": 70.0}
                },
                "by_message_type": {
                    "notification": 750,
                    "payslip": 300,
                    "reminder": 150,
                    "alert": 50
                },
                "top_failure_reasons": [
                    {"reason": "Invalid phone number", "count": 25},
                    {"reason": "User not found", "count": 20},
                    {"reason": "Rate limit exceeded", "count": 15}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {"error": "System error occurred"}
    
    # Mock database methods (would be replaced with actual DB operations)
    
    async def _get_contact_info(self, employee_id: str, company_id: str) -> Optional[ContactInfo]:
        """Get contact information for employee"""
        # Mock implementation
        return ContactInfo(
            employee_id=employee_id,
            company_id=company_id,
            whatsapp_number="+525512345678",
            email="employee@company.com",
            phone_number="+525512345678",
            preferred_channel=MessageChannel.WHATSAPP
        )
    
    async def _get_company_settings(self, company_id: str) -> Dict[str, Any]:
        """Get company messaging settings"""
        return {"messaging_enabled": True}
    
    async def _schedule_message(self, message: Message):
        """Schedule message for later delivery"""
        logger.info(f"Scheduling message {message.id} for {message.scheduled_for}")
    
    async def _save_message(self, message: Message):
        """Save message to database"""
        logger.info(f"Saving message {message.id}")
    
    async def _save_delivery(self, delivery: MessageDelivery):
        """Save delivery record to database"""
        logger.info(f"Saving delivery {delivery.id}")
    
    async def _get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID"""
        return None
    
    async def _get_message_deliveries(self, message_id: str) -> List[MessageDelivery]:
        """Get all deliveries for a message"""
        return []
    
    async def _update_delivery_status(self, delivery: MessageDelivery):
        """Update delivery status in database"""
        logger.info(f"Updating delivery {delivery.id} status to {delivery.status}")
    
    async def _get_retryable_deliveries(self) -> List[MessageDelivery]:
        """Get failed deliveries that can be retried"""
        return []