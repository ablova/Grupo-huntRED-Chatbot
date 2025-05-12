from typing import Any, Callable
from app.import_config import register_module

# Register at startup
register_module('conversational_flow_manager', 'app.com.chatbot.conversational_flow_manager.ConversationalFlowManager')

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
