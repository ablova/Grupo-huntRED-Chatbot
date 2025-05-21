# /home/pablo/app/com/chatbot/integrations/message_sender.py
"""
Message sending utilities for chatbot integrations.
This module contains functions for sending messages through different platforms
without creating circular imports.
"""
import logging
from typing import Optional, List, Dict, Any
from django.conf import settings
from asgiref.sync import sync_to_async

logger = logging.getLogger('chatbot')

# Import the message service at runtime to avoid circular imports
def get_message_service():
    from app.com.chatbot.integrations.services import MessageService
    from app.models import BusinessUnit
    
    # Get the default business unit or handle appropriately
    business_unit = BusinessUnit.objects.first()  # Or get the appropriate BU
    return MessageService(business_unit)

# Wrapper functions for message sending

def send_message(platform: str, user_id: str, message: str, business_unit_name: str = None):
    """Send a message to the specified user on the given platform."""
    service = get_message_service()
    return service.send_message(platform, user_id, message)

async def send_message_async(platform: str, user_id: str, message: str, business_unit_name: str = None):
    """Send a message asynchronously."""
    return await sync_to_async(send_message)(platform, user_id, message, business_unit_name)

def send_menu(platform: str, user_id: str, business_unit_name: str = None):
    """Send the main menu to the user."""
    service = get_message_service()
    return service.send_menu(platform, user_id)

def send_options(platform: str, user_id: str, message: str, buttons=None, business_unit_name: str = None):
    """Send a message with interactive buttons."""
    service = get_message_service()
    return service.send_options(platform, user_id, message, buttons or [])

def send_smart_options(platform: str, user_id: str, message: str, options: List[Dict], business_unit_name: str = None):
    """Send smart options to the user."""
    service = get_message_service()
    return service.send_smart_options(platform, user_id, message, options)

def send_image(platform: str, user_id: str, message: str, image_url: str, business_unit_name: str = None):
    """Send an image to the user."""
    service = get_message_service()
    return service.send_image(platform, user_id, message, image_url)
