"""
Generador de respuestas para el chatbot
Ubicación: /app/com/chatbot/services/response/generator.py
Responsabilidad: Generación de respuestas basadas en el contexto y estado

Created: 2025-05-15
Updated: 2025-05-15
"""

from app.com.chatbot.core.state.manager import ChatStateManager
from app.com.utils.gpt import GPTProcessor

class ResponseGenerator:
    def __init__(self):
        self.state_manager = ChatStateManager()
        self.gpt_processor = GPTProcessor()

    def generate_proposal_response(self, state):
        """Genera respuesta para solicitud de propuesta"""
        context = self._get_context(state)
        return self.gpt_processor.generate_response(
            prompt=self._get_proposal_prompt(context),
            temperature=0.7
        )

    def generate_contract_response(self, state):
        """Genera respuesta para solicitud de contrato"""
        context = self._get_context(state)
        return self.gpt_processor.generate_response(
            prompt=self._get_contract_prompt(context),
            temperature=0.5
        )

    def _get_context(self, state):
        """Obtiene contexto para la generación"""
        return {
            'company': state.company_data,
            'bu': state.business_unit,
            'channel': state.channel
        }

    def _get_proposal_prompt(self, context):
        """Genera prompt para propuesta"""
        return f"""
        Basado en los siguientes datos de la empresa:
        {json.dumps(context['company'], indent=2)}

        Genera una propuesta personalizada para {context['bu']} usando el canal {context['channel']}
        """

    def _get_contract_prompt(self, context):
        """Genera prompt para contrato"""
        return f"""
        Basado en los siguientes datos de la empresa:
        {json.dumps(context['company'], indent=2)}

        Genera un contrato personalizado para {context['bu']} usando el canal {context['channel']}
        """
