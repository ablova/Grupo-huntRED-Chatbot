"""
Manejo de intenciones del chatbot
Ubicación: /app/com/chatbot/core/intents/handler.py
Responsabilidad: Procesamiento y manejo de intenciones del usuario

Created: 2025-05-15
Updated: 2025-05-15
"""

from app.com.chatbot.nlp import NLPProcessor
from app.com.chatbot.chat_state_manager import ChatStateManager
from app.com.chatbot.components.response_generator import ResponseGenerator

class IntentHandler:
    def __init__(self):
        self.nlp_processor = NLPProcessor()
        self.state_manager = ChatStateManager()
        self.response_generator = ResponseGenerator()

    def process_intent(self, message, channel):
        """Procesa la intención del mensaje"""
        intent = self.nlp_processor.extract_intent(message)
        state = self.state_manager.get_state(channel)
        response = self._handle_intent(intent, state)
        return response

    def _handle_intent(self, intent, state):
        """Maneja la intención específica"""
        if intent == 'proposal_request':
            return self._handle_proposal_request(state)
        elif intent == 'contract_request':
            return self._handle_contract_request(state)
        # ... otros manejadores de intención

    def _handle_proposal_request(self, state):
        """Maneja la solicitud de propuesta"""
        return self.response_generator.generate_proposal_response(state)

    def _handle_contract_request(self, state):
        """Maneja la solicitud de contrato"""
        return self.response_generator.generate_contract_response(state)
