# /home/amigro/app/views.py

import json
import logging
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.response import TemplateResponse
from django.conf import settings
from .nlp_utils import analyze_text
from .gpt import gpt_message
from .models import GptApi, FlowModel, ChatState, Pregunta, Person
from app.integrations.services import send_message as smg

# Configuración del logger
logger = logging.getLogger(__name__)

# Configuración de la API de spacy
nlp = spacy.load("es_core_news_sm")
nlp.add_pipe('spacytextblob')


def index(request):
    return render(request, "index.html")


def recv_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            message = data.get('message')
            platform = data.get('platform')
            use_gpt = data.get('use_gpt', 'yes')

            analysis = analyze_text(message)
            response = process_spacy_analysis(analysis, message)

            if not response and use_gpt == 'yes':
                gpt_api = GptApi.objects.first()
                gpt_response = gpt_message(
                    api_token=gpt_api.api_token,
                    text=message,
                    model=gpt_api.model,
                )
                response = gpt_response['choices'][0]['message']['content']

            smg(platform, data['user_id'], response)

            return JsonResponse({'status': 'success', 'response': response})

        except Exception as e:
            logger.exception(f"Error procesando mensaje: {e}")
            return JsonResponse({'status': 'error', 'message': 'Error interno del servidor'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
