"""
AURA GPT Assistant

- Explica resultados de AURA usando GPT
- Sugiere acciones o próximos pasos en lenguaje natural
- Disponible para consultores, admins, clientes y candidatos
"""

from .base import AuraBaseView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views import View
from django.http import JsonResponse
import json

# Suponiendo que tienes un wrapper en app/com/chatbot/gpt.py
from app.com.chatbot.gpt import explain_aura_result, suggest_next_action

class AuraGPTAssistantView(AuraBaseView):
    """
    Vista para obtener explicaciones y sugerencias de GPT sobre resultados de AURA.
    """
    @method_decorator(csrf_exempt)
    @method_decorator(require_POST)
    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body.decode('utf-8'))
            result = body.get('aura_result')
            mode = body.get('mode', 'explain')  # 'explain' o 'suggest'
            if not result:
                return self.render_error('No se proporcionó resultado de AURA')
            if mode == 'explain':
                gpt_response = explain_aura_result(result)
            else:
                gpt_response = suggest_next_action(result)
            return self.render_response({'gpt_response': gpt_response})
        except Exception as e:
            return self.render_error(f'Error procesando la solicitud: {str(e)}') 