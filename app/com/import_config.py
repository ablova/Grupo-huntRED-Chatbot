from typing import Any, Callable
from app.import_config import register_module

# Register essential modules at startup
register_module('chatbot', 'app.com.chatbot.chatbot.Chatbot')
register_module('conversational_flow_manager', 'app.com.chatbot.conversational_flow_manager.ConversationalFlowManager')

# Getters for lazy loading
def get_chatbot():
    """Get Chatbot instance."""
    from app.com.chatbot.chatbot import Chatbot
    return Chatbot

def get_conversational_flow_manager():
    """Get ConversationalFlowManager instance."""
    from app.com.chatbot.conversational_flow_manager import ConversationalFlowManager
    return ConversationalFlowManager
