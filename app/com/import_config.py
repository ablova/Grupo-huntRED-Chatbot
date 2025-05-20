# /home/pablo/app/com/import_config.py
#
# NOTA: Este archivo está obsoleto y se mantiene temporalmente para compatibilidad.
# El registro de módulos ahora es gestionado automáticamente por ModuleRegistry en app/module_registry.py
#
# Siguiendo las reglas globales de Grupo huntRED®:
# - No Redundancies: Verificar antes de añadir funciones que no existan en el código
# - Modularity: Escribir código modular, reutilizable; evitar duplicar funcionalidad
# - Code Consistency: Seguir estándares de Django

# AHORA EL REGISTRO ES AUTOMÁTICO:
# Los módulos deben ser importados directamente usando importaciones estándar:
# from app.com.chatbot.chatbot import Chatbot
# from app.com.chatbot.conversational_flow_manager import ConversationalFlowManager

# Getters for lazy loading
def get_chatbot():
    """Get Chatbot instance."""
    from app.com.chatbot.chatbot import Chatbot
    return Chatbot

def get_conversational_flow_manager():
    """Get ConversationalFlowManager instance."""
    from app.com.chatbot.conversational_flow_manager import ConversationalFlowManager
    return ConversationalFlowManager
