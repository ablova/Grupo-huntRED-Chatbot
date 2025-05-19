# app/com/chatbot/__init__.py
# Removed manual lazy_imports registration as ModuleRegistry handles this automatically

# Establecer el paquete actual
# Registrar módulos de chatbot para lazy loading
# ... (previous manual registrations removed)

# Exports for chatbot module
from app.com.chatbot.chatbot import Chatbot
from app.com.chatbot.conversational_flow_manager import ConversationalFlowManager
from app.com.chatbot.intents_handler import IntentsHandler
from app.com.chatbot.intents_optimizer import IntentsOptimizer
from app.com.chatbot.context_manager import ContextManager
from app.com.chatbot.response_generator import ResponseGenerator
from app.com.chatbot.state_manager import StateManager

__all__ = [
    'Chatbot',
    'ConversationalFlowManager',
    'IntentsHandler',
    'IntentsOptimizer',
    'ContextManager',
    'ResponseGenerator',
    'StateManager'
]

__all__ = ['Chatbot']