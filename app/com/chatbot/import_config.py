"""
Configuración centralizada de importaciones diferidas para prevenir dependencias circulares.
"""

def get_chat_state_manager():
    """Función diferida para obtener ChatStateManager."""
    from app.com.chatbot.chat_state_manager import ChatStateManager
    return ChatStateManager

def get_intent_processor():
    """Función diferida para obtener IntentProcessor."""
    from app.com.chatbot.intents_handler import IntentProcessor
    return IntentProcessor

def get_whatsapp_handler():
    """Función diferida para obtener WhatsAppHandler."""
    from app.com.chatbot.integrations.whatsapp import WhatsAppHandler
    return WhatsAppHandler

def get_fetch_whatsapp_user_data():
    """Función diferida para obtener fetch_whatsapp_user_data."""
    from app.com.chatbot.integrations.whatsapp import fetch_whatsapp_user_data
    return fetch_whatsapp_user_data

def get_telegram_handler():
    """Función diferida para obtener TelegramHandler."""
    from app.com.chatbot.integrations.telegram import TelegramHandler
    return TelegramHandler

def get_slack_handler():
    """Función diferida para obtener SlackHandler."""
    from app.com.chatbot.integrations.slack import SlackHandler
    return SlackHandler

def get_message_service():
    """Función diferida para obtener MessageService."""
    from app.com.chatbot.integrations.services import MessageService
    return MessageService

def get_gamification_service():
    """Función diferida para obtener GamificationService."""
    from app.com.chatbot.integrations.services import GamificationService
    return GamificationService
