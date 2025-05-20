# app/com/chatbot/__init__.py
# Implementación de lazy loading para evitar dependencias circulares
# durante la inicialización de Django

# Configuración del paquete
default_app_config = 'app.com.chatbot.apps.ChatbotConfig'

# Definimos la variable de clases que se exportarán
# pero no las importamos directamente para evitar problemas de inicialización
__all__ = [
    'Chatbot',
    'ConversationalFlowManager',
    'IntentsHandler',
    'IntentsOptimizer',
    'ContextManager',
    'ResponseGenerator',
    'StateManager'
]

# Función para obtener la clase ChatBotHandler de forma perezosa
def get_chatbot():
    from app.com.chatbot.chatbot import ChatBotHandler
    return ChatBotHandler

# No importamos los módulos directamente durante la inicialización
# para evitar el error AppRegistryNotReady