# /home/pablo/app/ats/chatbot/flow/conversational_flow_manager.py
"""
Gestiona los flujos conversacionales del chatbot.
Implementado siguiendo las reglas globales de Grupo huntRED® para optimización.
"""
from typing import Any, Callable, Dict


# No importamos register_module para evitar dependencia circular con import_config.py
# Registración ahora manejada por ModuleRegistry en app/module_registry.py

class ConversationalFlowManager:
    def __init__(self):
        self.flows = {}

    def register_flow(self, name: str, flow: Callable) -> None:
        """Register a conversational flow."""
        self.flows[name] = flow

    def get_flow(self, name: str) -> Callable:
        """Get a registered flow."""
        return self.flows.get(name)

    def process_message(self, message: str, context: dict) -> Any:
        """Process a message through the appropriate flow."""
        # Implement flow processing logic
        pass
