"""
huntRED® v2 - Webhook Handlers
Multi-channel webhook processing for WhatsApp, Telegram, Messenger
Migrated from original system with enhanced multi-tenant support
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import hashlib
import hmac

from .engine import ChatbotEngine, MessageChannel

# Configure logger
logger = logging.getLogger('huntred.webhooks')

class WebhookValidator:
    """Validate webhook authenticity"""
    
    @staticmethod
    def validate_whatsapp_webhook(payload: str, signature: str, verify_token: str) -> bool:
        """Validate WhatsApp webhook signature"""
        try:
            expected_signature = hmac.new(
                verify_token.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(f"sha256={expected_signature}", signature)
        except Exception as e:
            logger.error(f"WhatsApp webhook validation error: {e}")
            return False
    
    @staticmethod
    def validate_telegram_webhook(token: str, provided_token: str) -> bool:
        """Validate Telegram webhook token"""
        return hmac.compare_digest(token, provided_token)

class WhatsAppWebhookHandler:
    """Handle WhatsApp Business API webhooks"""
    
    def __init__(self, chatbot_engine: ChatbotEngine):
        self.chatbot_engine = chatbot_engine
        self.supported_message_types = [
            'text', 'audio', 'video', 'image', 'document', 'location', 'contacts'
        ]
    
    async def handle_webhook(self, webhook_data: Dict[str, Any], company_id: str) -> Dict[str, Any]:
        """
        Process incoming WhatsApp webhook
        
        Args:
            webhook_data: Webhook payload from WhatsApp
            company_id: Company ID for multi-tenant routing
            
        Returns:
            Processing result
        """
        try:
            logger.info(f"Processing WhatsApp webhook for company {company_id}")
            
            # Extract webhook data
            if 'entry' not in webhook_data:
                logger.warning("Invalid webhook format: missing 'entry'")
                return {"status": "error", "message": "Invalid webhook format"}
            
            results = []
            
            for entry in webhook_data['entry']:
                if 'changes' not in entry:
                    continue
                    
                for change in entry['changes']:
                    if change['field'] != 'messages':
                        continue
                    
                    value = change.get('value', {})
                    
                    # Process messages
                    if 'messages' in value:
                        for message in value['messages']:
                            result = await self._process_message(message, company_id, value)
                            results.append(result)
                    
                    # Process status updates
                    if 'statuses' in value:
                        for status in value['statuses']:
                            await self._process_status_update(status, company_id)
            
            return {
                "status": "success",
                "processed_messages": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _process_message(self, message: Dict[str, Any], company_id: str, webhook_value: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual WhatsApp message"""
        try:
            message_id = message.get('id', '')
            from_number = message.get('from', '')
            timestamp = message.get('timestamp', '')
            message_type = message.get('type', 'text')
            
            logger.info(f"Processing WhatsApp message {message_id} from {from_number}")
            
            # Extract message content based on type
            content = await self._extract_message_content(message, message_type)
            
            if not content:
                logger.warning(f"No content extracted from message {message_id}")
                return {"status": "skipped", "reason": "No content"}
            
            # Process with chatbot engine
            response = await self.chatbot_engine.process_message(
                user_id=from_number,
                company_id=company_id,
                message=content,
                channel=MessageChannel.WHATSAPP
            )
            
            # Send response back via unified messaging
            await self._send_response(from_number, response, company_id)
            
            return {
                "status": "processed",
                "message_id": message_id,
                "from": from_number,
                "content": content[:100],  # Truncate for logging
                "response_sent": True
            }
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp message: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _extract_message_content(self, message: Dict[str, Any], message_type: str) -> str:
        """Extract content from different message types"""
        try:
            if message_type == 'text':
                return message.get('text', {}).get('body', '')
            
            elif message_type == 'audio':
                return "[Mensaje de audio recibido]"
            
            elif message_type == 'video':
                return "[Video recibido]"
            
            elif message_type == 'image':
                caption = message.get('image', {}).get('caption', '')
                return f"[Imagen recibida] {caption}".strip()
            
            elif message_type == 'document':
                filename = message.get('document', {}).get('filename', 'documento')
                return f"[Documento recibido: {filename}]"
            
            elif message_type == 'location':
                location = message.get('location', {})
                lat = location.get('latitude', 0)
                lon = location.get('longitude', 0)
                return f"[Ubicación compartida: {lat}, {lon}]"
            
            elif message_type == 'contacts':
                return "[Contacto compartido]"
            
            elif message_type == 'interactive':
                # Handle button/list replies
                interactive = message.get('interactive', {})
                if 'button_reply' in interactive:
                    return interactive['button_reply'].get('title', '')
                elif 'list_reply' in interactive:
                    return interactive['list_reply'].get('title', '')
            
            else:
                logger.warning(f"Unsupported message type: {message_type}")
                return f"[Mensaje de tipo {message_type} no soportado]"
                
        except Exception as e:
            logger.error(f"Error extracting message content: {e}")
            return ""
    
    async def _process_status_update(self, status: Dict[str, Any], company_id: str):
        """Process message status updates (delivered, read, etc.)"""
        try:
            message_id = status.get('id', '')
            recipient_id = status.get('recipient_id', '')
            status_type = status.get('status', '')
            timestamp = status.get('timestamp', '')
            
            logger.debug(f"Status update: {message_id} -> {status_type}")
            
            # Here you could update message delivery status in database
            # For now, just log it
            
        except Exception as e:
            logger.error(f"Error processing status update: {e}")
    
    async def _send_response(self, recipient: str, message: str, company_id: str):
        """Send response via unified messaging system"""
        try:
            from ..services.unified_messaging import UnifiedMessagingEngine, Message, MessageType, MessagePriority, MessageChannel
            
            messaging_engine = UnifiedMessagingEngine()
            
            message_obj = Message(
                id="",
                recipient_id=recipient,
                company_id=company_id,
                message_type=MessageType.RESPONSE,
                priority=MessagePriority.HIGH,
                subject="WhatsApp Response",
                content=message,
                channels=[MessageChannel.WHATSAPP]
            )
            
            await messaging_engine.send_message(message_obj)
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp response: {e}")

class TelegramWebhookHandler:
    """Handle Telegram Bot API webhooks"""
    
    def __init__(self, chatbot_engine: ChatbotEngine):
        self.chatbot_engine = chatbot_engine
    
    async def handle_webhook(self, webhook_data: Dict[str, Any], company_id: str) -> Dict[str, Any]:
        """
        Process incoming Telegram webhook
        
        Args:
            webhook_data: Webhook payload from Telegram
            company_id: Company ID for multi-tenant routing
            
        Returns:
            Processing result
        """
        try:
            logger.info(f"Processing Telegram webhook for company {company_id}")
            
            # Handle different update types
            if 'message' in webhook_data:
                return await self._process_message(webhook_data['message'], company_id)
            
            elif 'callback_query' in webhook_data:
                return await self._process_callback_query(webhook_data['callback_query'], company_id)
            
            elif 'edited_message' in webhook_data:
                return await self._process_edited_message(webhook_data['edited_message'], company_id)
            
            else:
                logger.info("Unsupported Telegram update type")
                return {"status": "skipped", "reason": "Unsupported update type"}
                
        except Exception as e:
            logger.error(f"Error processing Telegram webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _process_message(self, message: Dict[str, Any], company_id: str) -> Dict[str, Any]:
        """Process Telegram message"""
        try:
            message_id = message.get('message_id', '')
            chat = message.get('chat', {})
            user = message.get('from', {})
            
            chat_id = str(chat.get('id', ''))
            user_id = str(user.get('id', ''))
            username = user.get('username', user.get('first_name', 'Usuario'))
            
            # Extract message content
            content = ""
            if 'text' in message:
                content = message['text']
            elif 'photo' in message:
                caption = message.get('caption', '')
                content = f"[Foto enviada] {caption}".strip()
            elif 'document' in message:
                filename = message.get('document', {}).get('file_name', 'documento')
                content = f"[Documento enviado: {filename}]"
            elif 'voice' in message:
                content = "[Mensaje de voz enviado]"
            elif 'video' in message:
                content = "[Video enviado]"
            elif 'location' in message:
                location = message['location']
                content = f"[Ubicación compartida: {location.get('latitude', 0)}, {location.get('longitude', 0)}]"
            else:
                content = "[Mensaje multimedia]"
            
            if not content:
                return {"status": "skipped", "reason": "No content"}
            
            logger.info(f"Processing Telegram message from {username} ({user_id}): {content[:50]}")
            
            # Process with chatbot engine
            response = await self.chatbot_engine.process_message(
                user_id=user_id,
                company_id=company_id,
                message=content,
                channel=MessageChannel.TELEGRAM
            )
            
            # Send response back
            await self._send_response(chat_id, response, company_id)
            
            return {
                "status": "processed",
                "message_id": message_id,
                "chat_id": chat_id,
                "user_id": user_id,
                "username": username,
                "content": content[:100],
                "response_sent": True
            }
            
        except Exception as e:
            logger.error(f"Error processing Telegram message: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _process_callback_query(self, callback_query: Dict[str, Any], company_id: str) -> Dict[str, Any]:
        """Process Telegram callback query (inline button press)"""
        try:
            query_id = callback_query.get('id', '')
            user = callback_query.get('from', {})
            data = callback_query.get('data', '')
            
            user_id = str(user.get('id', ''))
            username = user.get('username', user.get('first_name', 'Usuario'))
            
            logger.info(f"Processing Telegram callback query from {username}: {data}")
            
            # Process callback data as message
            response = await self.chatbot_engine.process_message(
                user_id=user_id,
                company_id=company_id,
                message=data,
                channel=MessageChannel.TELEGRAM
            )
            
            # Answer callback query
            await self._answer_callback_query(query_id, "Procesado ✅", company_id)
            
            # Send response message
            if 'message' in callback_query:
                chat_id = str(callback_query['message']['chat']['id'])
                await self._send_response(chat_id, response, company_id)
            
            return {
                "status": "processed",
                "query_id": query_id,
                "user_id": user_id,
                "data": data,
                "response_sent": True
            }
            
        except Exception as e:
            logger.error(f"Error processing Telegram callback query: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _process_edited_message(self, message: Dict[str, Any], company_id: str) -> Dict[str, Any]:
        """Process edited Telegram message"""
        # For now, treat edited messages the same as new messages
        return await self._process_message(message, company_id)
    
    async def _send_response(self, chat_id: str, message: str, company_id: str):
        """Send response via unified messaging system"""
        try:
            from ..services.unified_messaging import UnifiedMessagingEngine, Message, MessageType, MessagePriority, MessageChannel
            
            messaging_engine = UnifiedMessagingEngine()
            
            message_obj = Message(
                id="",
                recipient_id=chat_id,
                company_id=company_id,
                message_type=MessageType.RESPONSE,
                priority=MessagePriority.HIGH,
                subject="Telegram Response",
                content=message,
                channels=[MessageChannel.TELEGRAM]
            )
            
            await messaging_engine.send_message(message_obj)
            
        except Exception as e:
            logger.error(f"Error sending Telegram response: {e}")
    
    async def _answer_callback_query(self, query_id: str, text: str, company_id: str):
        """Answer Telegram callback query"""
        try:
            # This would normally call Telegram API directly
            logger.info(f"Answering callback query {query_id}: {text}")
            
        except Exception as e:
            logger.error(f"Error answering callback query: {e}")

class MessengerWebhookHandler:
    """Handle Facebook Messenger webhooks"""
    
    def __init__(self, chatbot_engine: ChatbotEngine):
        self.chatbot_engine = chatbot_engine
    
    async def handle_webhook(self, webhook_data: Dict[str, Any], company_id: str) -> Dict[str, Any]:
        """Process incoming Messenger webhook"""
        try:
            logger.info(f"Processing Messenger webhook for company {company_id}")
            
            if 'entry' not in webhook_data:
                return {"status": "error", "message": "Invalid webhook format"}
            
            results = []
            
            for entry in webhook_data['entry']:
                if 'messaging' not in entry:
                    continue
                
                for messaging_event in entry['messaging']:
                    result = await self._process_messaging_event(messaging_event, company_id)
                    results.append(result)
            
            return {
                "status": "success",
                "processed_events": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error processing Messenger webhook: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _process_messaging_event(self, event: Dict[str, Any], company_id: str) -> Dict[str, Any]:
        """Process individual Messenger event"""
        try:
            sender_id = event.get('sender', {}).get('id', '')
            recipient_id = event.get('recipient', {}).get('id', '')
            timestamp = event.get('timestamp', 0)
            
            # Handle different event types
            if 'message' in event:
                return await self._process_message(event['message'], sender_id, company_id)
            
            elif 'postback' in event:
                return await self._process_postback(event['postback'], sender_id, company_id)
            
            else:
                return {"status": "skipped", "reason": "Unsupported event type"}
                
        except Exception as e:
            logger.error(f"Error processing Messenger event: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _process_message(self, message: Dict[str, Any], sender_id: str, company_id: str) -> Dict[str, Any]:
        """Process Messenger message"""
        try:
            message_id = message.get('mid', '')
            
            # Extract content
            content = ""
            if 'text' in message:
                content = message['text']
            elif 'attachments' in message:
                attachment = message['attachments'][0]
                attachment_type = attachment.get('type', 'unknown')
                content = f"[{attachment_type.title()} recibido]"
            
            if not content:
                return {"status": "skipped", "reason": "No content"}
            
            # Process with chatbot engine
            response = await self.chatbot_engine.process_message(
                user_id=sender_id,
                company_id=company_id,
                message=content,
                channel=MessageChannel.MESSENGER
            )
            
            # Send response
            await self._send_response(sender_id, response, company_id)
            
            return {
                "status": "processed",
                "message_id": message_id,
                "sender_id": sender_id,
                "content": content[:100],
                "response_sent": True
            }
            
        except Exception as e:
            logger.error(f"Error processing Messenger message: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _process_postback(self, postback: Dict[str, Any], sender_id: str, company_id: str) -> Dict[str, Any]:
        """Process Messenger postback (button press)"""
        try:
            payload = postback.get('payload', '')
            title = postback.get('title', '')
            
            # Process postback as message
            response = await self.chatbot_engine.process_message(
                user_id=sender_id,
                company_id=company_id,
                message=payload or title,
                channel=MessageChannel.MESSENGER
            )
            
            # Send response
            await self._send_response(sender_id, response, company_id)
            
            return {
                "status": "processed",
                "sender_id": sender_id,
                "payload": payload,
                "title": title,
                "response_sent": True
            }
            
        except Exception as e:
            logger.error(f"Error processing Messenger postback: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _send_response(self, recipient_id: str, message: str, company_id: str):
        """Send response via unified messaging system"""
        try:
            from ..services.unified_messaging import UnifiedMessagingEngine, Message, MessageType, MessagePriority, MessageChannel
            
            messaging_engine = UnifiedMessagingEngine()
            
            message_obj = Message(
                id="",
                recipient_id=recipient_id,
                company_id=company_id,
                message_type=MessageType.RESPONSE,
                priority=MessagePriority.HIGH,
                subject="Messenger Response",
                content=message,
                channels=[MessageChannel.SLACK]  # Using SLACK as placeholder for MESSENGER
            )
            
            await messaging_engine.send_message(message_obj)
            
        except Exception as e:
            logger.error(f"Error sending Messenger response: {e}")

class WebhookRouter:
    """Route webhooks to appropriate handlers"""
    
    def __init__(self, chatbot_engine: ChatbotEngine):
        self.chatbot_engine = chatbot_engine
        self.handlers = {
            'whatsapp': WhatsAppWebhookHandler(chatbot_engine),
            'telegram': TelegramWebhookHandler(chatbot_engine),
            'messenger': MessengerWebhookHandler(chatbot_engine)
        }
    
    async def route_webhook(self, platform: str, webhook_data: Dict[str, Any], company_id: str) -> Dict[str, Any]:
        """Route webhook to appropriate handler"""
        try:
            if platform not in self.handlers:
                logger.error(f"Unsupported platform: {platform}")
                return {"status": "error", "message": f"Unsupported platform: {platform}"}
            
            handler = self.handlers[platform]
            result = await handler.handle_webhook(webhook_data, company_id)
            
            logger.info(f"Webhook processed for {platform} in company {company_id}: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Error routing webhook for {platform}: {e}")
            return {"status": "error", "message": str(e)}