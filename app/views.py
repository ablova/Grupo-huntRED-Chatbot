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
from app.integrations.services import send_message
from .models import GptApi, SmtpConfig, Pregunta, FlowModel, ChatState, Condicion, Etapa, Person
import spacy


logger = logging.getLogger(__name__)

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

# Nueva función para procesar mensajes sin necesidad de request
def process_message(platform, sender_id, message, use_gpt):
    """
    Procesa un mensaje entrante y responde a través de la plataforma correspondiente.
    Args:
        platform (str): La plataforma (whatsapp, telegram, etc.)
        sender_id (str): El ID del remitente del mensaje.
        message (str): El mensaje de texto recibido.
        use_gpt (str): Indicador para usar GPT o no ('yes' o 'no').
    """
    try:
        # Analizar el mensaje usando la función NLP
        analysis = analyze_text(message)

        # Respuesta inicial con SpaCy
        response = process_spacy_analysis(analysis, message)

        # Si no hay respuesta y está activado el uso de GPT, llamar a GPT
        if not response and use_gpt == 'yes':
            gpt_api = GptApi.objects.first()
            gpt_response = gpt_message(api_token=gpt_api.api_token, text=message, model=gpt_api.model)
            response = gpt_response['choices'][0]['message']['content']

        # Enviar la respuesta usando la plataforma
        send_message(platform, sender_id, response)

        return JsonResponse({'status': 'success', 'response': response})

    except Exception as e:
        logger.error(f"Error procesando el mensaje: {e}")
        return JsonResponse({'status': 'error'}, status=500)

# Función para recibir mensajes del chatbot
@csrf_exempt
def recv_message(request):
    """
    Recibe un mensaje desde cualquier plataforma y lo procesa.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            message = data.get('message')
            platform = data.get('platform')
            use_gpt = data.get('use_gpt')

            # Analizar el texto
            analysis = analyze_text(message)

            # Procesar la respuesta con spaCy
            response = process_spacy_analysis(analysis, message)

            # Si no hay respuesta con spaCy y GPT está habilitado, usar GPT
            if not response and use_gpt == 'yes':
                gpt_api = GptApi.objects.first()
                gpt_response = gpt_message(api_token=gpt_api.api_token, text=message, model=gpt_api.model)
                response = gpt_response['choices'][0]['message']['content']

            # Enviar la respuesta a la plataforma correspondiente
            send_message(platform, data['username'], response)

            return JsonResponse({'status': 'success', 'response': response})

        except json.JSONDecodeError:
            logger.error("Error decodificando JSON")
            return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
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
                # Llamada a tu función de WhatsApp
                from app.integrations.whatsapp import send_whatsapp_message
                whatsapp_api = WhatsAppAPI.objects.first()  # Obtener la API desde la base de datos
                if whatsapp_api:
                    send_whatsapp_message('525518490291', message, whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api)
                else:
                    raise Exception("Configuración de WhatsApp no encontrada")

            elif platform == 'telegram':
                # Llamada a tu función de Telegram
                from app.integrations.telegram import send_telegram_message
                telegram_api = TelegramAPI.objects.first()
                if telegram_api:
                    send_telegram_message('871198362', message, telegram_api.api_key)
                else:
                    raise Exception("Configuración de Telegram no encontrada")

            elif platform == 'messenger':
                # Llamada a tu función de Messenger
                from app.integrations.messenger import send_messenger_message
                messenger_api = MessengerAPI.objects.first()
                if messenger_api:
                    send_messenger_message('123456789', message, messenger_api.page_access_token)
                else:
                    raise Exception("Configuración de Messenger no encontrada")

            elif platform == 'instagram':
                # Llamada a tu función de Instagram
                from app.integrations.instagram import send_instagram_message
                instagram_api = InstagramAPI.objects.first()
                if instagram_api:
                    send_instagram_message('instagram_id', message, instagram_api.access_token)
                else:
                    raise Exception("Configuración de Instagram no encontrada")

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)

