# app/com/chatbot/__init__.py
# Removed manual lazy_imports registration as ModuleRegistry handles this automatically

# Establecer el paquete actual
# Registrar módulos de chatbot para lazy loading
# ... (previous manual registrations removed)

# Exports for chatbot module
from .chatbot import Chatbot

__all__ = ['Chatbot']