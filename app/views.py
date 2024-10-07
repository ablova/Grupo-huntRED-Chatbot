# /home/amigro/app/views.py

import json
import logging
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.response import TemplateResponse
from django.conf import settings
from .nlp_utils import analyze_text
from .gpt import gpt_message
from app.integrations.services import send_message as smg   
from .models import GptApi, SmtpConfig, Pregunta, FlowModel, ChatState, Condicion, Etapa, Person
import spacy

logging.basicConfig(filename="logger.log", level=logging.ERROR)

# Configuración de spaCy
nlp = spacy.load("es_core_news_sm")

# Vista para la página principal
def index(request):
    return render(request, "index.html")

# Función para crear preguntas
@csrf_exempt
def create_pregunta(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        pregunta = Pregunta.objects.create(name=data['name'])
        return JsonResponse({'id': pregunta.id})

# Función para actualizar preguntas
@csrf_exempt
def update_pregunta(request, id):
    if request.method == 'PUT':
        data = json.loads(request.body)
        pregunta = Pregunta.objects.get(id=id)
        pregunta.name = data['name']
        pregunta.save()
        return JsonResponse({'status': 'success'})

# Función para actualizar posiciones de preguntas
@csrf_exempt
def update_position(request, id):
    if request.method == 'PUT':
        data = json.loads(request.body)
        pregunta = Pregunta.objects.get(id=id)
        pregunta.position = data['position']  # Suponiendo que tienes un campo de posición
        pregunta.save()
        return JsonResponse({'status': 'success'})

# Función para eliminar preguntas
@csrf_exempt
def delete_pregunta(request, id):
    if request.method == 'DELETE':
        pregunta = Pregunta.objects.get(id=id)
        pregunta.delete()
        return JsonResponse({'status': 'deleted'})

# Función para imprimir pregunta y subpreguntas (recursiva)
def print_pregunta_y_subpreguntas(pregunta):
    print(f"Pregunta: {pregunta.name}")
    for sub_pregunta in pregunta.sub_preguntas.all():
        print(f"    SubPregunta: {sub_pregunta.name}")
        print_pregunta_y_subpreguntas(sub_pregunta)  # Recursividad para explorar más

# Cargar datos del flujo
def load_flow_data(request, flowmodel_id):
    """
    Carga los datos del flujo en formato JSON.
    """
    flow = get_object_or_404(FlowModel, pk=flowmodel_id)
    flow_data_json = flow.flow_data_json  # Carga los datos del flujo en formato JSON
    return JsonResponse({'flow_data': flow_data_json})

# Vista para editar el flujo del chatbot
def edit_flow(request, flowmodel_id):
    flow = get_object_or_404(FlowModel, pk=flowmodel_id)
    context = {
        'flow': flow,
        'questions_json': flow.flow_data_json or "[]"  # Asegúrate de pasar los datos en formato JSON o vacío
    }
    return TemplateResponse(request, "admin/chatbot_flow.html", context)

# Guardar la estructura del flujo
@csrf_exempt
def save_flow_structure(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        flowmodel_id = data.get('flowmodel_id')
        flow = get_object_or_404(FlowModel, pk=flowmodel_id)
        flow.flow_data_json = json.dumps(data.get('nodes'))  # Guardar la estructura del flujo en formato JSON
        flow.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# Exportar el flujo del chatbot
@csrf_exempt
def export_chatbot_flow(request):
    if request.method == 'POST':
        flow_data = json.loads(request.body)
        return JsonResponse({'status': 'exported', 'data': flow_data})
    return JsonResponse({'status': 'error'}, status=400)

# Función para cargar preguntas y subpreguntas asociadas al flujo
def load_flow_questions_data(request, flowmodel_id):
    flow = FlowModel.objects.prefetch_related('preguntas__sub_preguntas').get(pk=flowmodel_id)
    
    flow_structure = {
        'flow_data': flow.flow_data_json,  # JSON del flujo
        'preguntas': [
            {
                'id': pregunta.id,
                'name': pregunta.name,
                'sub_preguntas': [
                    {'id': sub_pregunta.id, 'name': sub_pregunta.name}
                    for sub_pregunta in pregunta.sub_preguntas.all()
                ]
            }
            for pregunta in flow.preguntas.all()
        ]
    }

    return JsonResponse(flow_structure)

# Función para recibir mensajes del chatbot
@csrf_exempt
def recv_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            message = data.get('message')
            platform = data.get('platform')
            use_gpt = data.get('use_gpt')

            analysis = analyze_text(message)
            response = process_spacy_analysis(analysis, message)

            if not response and use_gpt == 'yes':
                try:
                    gpt_api = GptApi.objects.first()
                    gpt_response = gpt_message(api_token=gpt_api.api_token, text=message, model=gpt_api.model)
                    response = gpt_response['choices'][0]['message']['content']
                except Exception as e:
                    logging.error(f"Error llamando a GPT: {e}")
                    response = "Lo siento, ocurrió un error al procesar tu solicitud."

            if platform == 'telegram':
                send_telegram_message(data['username'], response)
            elif platform == 'whatsapp':
                send_whatsapp_message(data['username'], response)
            elif platform == 'messenger':
                send_messenger_message(data['username'], response)

            return JsonResponse({'status': 'success', 'response': response})
        except json.JSONDecodeError:
            logger.error("Error decodificando JSON")
            return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return JsonResponse({'status': 'error', 'message': 'Error interno del servidor'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

# Enviar mensaje de prueba
@csrf_exempt
def send_test_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            platform = data.get('platform')
            message = data.get('message')

            if platform == 'whatsapp':
                # Lógica para WhatsApp
                pass
            elif platform == 'telegram':
                # Lógica para Telegram
                pass
            elif platform == 'messenger':
                # Lógica para Messenger
                pass

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)

# Función para enviar mensajes
@csrf_exempt
def send_message(request):
    """
    Envía un mensaje a través de una plataforma específica.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message')
            platform = data.get('platform')

            # Lógica de envío de mensajes basada en la plataforma
            if platform == 'whatsapp':
                # Envía un mensaje por WhatsApp (lógica necesaria)
                response = f"Mensaje enviado a WhatsApp: {message}"
            elif platform == 'telegram':
                # Envía un mensaje por Telegram (lógica necesaria)
                response = f"Mensaje enviado a Telegram: {message}"
            elif platform == 'messenger':
                # Envía un mensaje por Messenger (lógica necesaria)
                response = f"Mensaje enviado a Messenger: {message}"
            elif platform == 'instagram':
                # Envía un mensaje por Instagram (lógica necesaria)
                response = f"Mensaje enviado a Instagram: {message}"
            else:
                return JsonResponse({'error': 'Plataforma no soportada.'}, status=400)

            return JsonResponse({'status': 'success', 'response': response})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
