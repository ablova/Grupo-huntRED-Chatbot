# app/com/chatbot/__init__.py
# Removed manual lazy_imports registration as ModuleRegistry handles this automatically

# Establecer el paquete actual
# Registrar módulos de chatbot para lazy loading
# ... (previous manual registrations removed)

# Exports for chatbot module
from .chatbot import Chatbot
from .conversational_flow_manager import ConversationalFlowManager
from .intents_handler import IntentsHandler
from .intents_optimizer import IntentsOptimizer
from .context_manager import ContextManager
from .response_generator import ResponseGenerator
from .state_manager import StateManager

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