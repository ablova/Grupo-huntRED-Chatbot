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
from .Event import PersonData
from .models import GptApi, SmtpConfig, Pregunta, FlowModel, ChatState, Condicion
from spacytextblob.spacytextblob import SpacyTextBlob
import spacy

logging.basicConfig(filename="logger.log", level=logging.ERROR)

def index(request):
    return render(request, "index.html")

nlp = spacy.load("es_core_news_sm")
nlp.add_pipe('spacytextblob')

def detect_intent(doc):
    intents = {
        "saludo": ["hola", "buenos días", "buenas tardes", "qué tal"],
        "despedida": ["adiós", "hasta luego", "ciao", "adios", "hasta luego", "chao", "hasta la vista", "nos vemos"],
        "ayuda": ["ayuda", "necesito ayuda", "cómo puedo", "busco apoyo", "busco ayuda", "busco orientación"],
        "queja": ["queja", "problema", "no funciona"],
        "informacion": ["información", "quiero saber", "cuánto cuesta", "dónde está", "cómo llegar"],
        "oportunidad": ["oportunidad", "oferta", "posición", "empleo", "chamba", "trabajo", "puesto", "puestos"],
        "familia": ["familia", "pareja", "novio", "novia", "amigo", "amiga", "compañero", "compañera"],
    }
    
    for intent, keywords in intents.items():
        if any(token.text.lower() in keywords for token in doc):
            return intent
    return "desconocido"

def extract_key_info(doc):
    key_info = {}
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            key_info["nombre"] = ent.text
        elif ent.label_ == "DATE":
            key_info["fecha"] = ent.text
    return key_info

def detailed_sentiment(doc):
    return {
        "polarity": doc._.blob.polarity,
        "subjectivity": doc._.blob.subjectivity,
    }

def categorize_question(doc):
    question_words = ["qué", "cómo", "cuándo", "dónde", "por qué", "quién"]
    for token in doc:
        if token.text.lower() in question_words:
            return token.text.lower()
    return None

def detect_topics(doc):
    return [token.text for token in doc if token.pos_ == "NOUN" and token.is_stop == False]

def process_spacy_analysis(analysis, original_message):
    doc = nlp(original_message)
    entities = analysis['entities']
    sentiment = detailed_sentiment(doc)
    intent = detect_intent(doc)
    key_info = extract_key_info(doc)
    question_type = categorize_question(doc)
    topics = detect_topics(doc)

    # Procesamiento basado en la intención
    if intent == "saludo":
        return "¡Hola! ¿En qué puedo ayudarte hoy?"
    elif intent == "despedida":
        return "¡Hasta luego! Espero haber sido de ayuda."
    elif intent == "ayuda":
        return "Estoy aquí para ayudarte. ¿Podrías ser más específico sobre lo que necesitas?"
    elif intent == "queja":
        return "Lamento que estés teniendo problemas. ¿Puedes darme más detalles para poder ayudarte mejor?"

    # Procesamiento basado en el sentimiento
    if sentiment["polarity"] > 0.5:
        return "Me alegra que estés de buen humor. ¿En qué puedo ayudarte hoy?"
    elif sentiment["polarity"] < -0.5:
        return "Lamento que estés pasando por un mal momento. ¿Hay algo en lo que pueda ayudarte?"

    # Procesamiento basado en información clave extraída
    if "nombre" in key_info:
        return f"Entiendo que estás hablando de {key_info['nombre']}. ¿Qué más puedes decirme?"

    # Procesamiento basado en el tipo de pregunta
    if question_type == "cómo":
        return "Parece que necesitas instrucciones. ¿Puedes ser más específico sobre lo que quieres saber?"
    elif question_type == "qué":
        return "Estás buscando información. ¿Sobre qué tema en particular?"
    elif question_type == "cuándo":
        return "Parece que estás preguntando sobre un tiempo o fecha. ¿Puedes dar más contexto?"

    # Procesamiento basado en temas detectados
    if "producto" in topics:
        return "Parece que estás interesado en nuestros productos. ¿Qué te gustaría saber específicamente?"

    # Si no se ha generado una respuesta específica, devolvemos None para usar GPT
    return None

@csrf_exempt
def recv_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            message = data.get('message')
            platform = data.get('platform')
            use_gpt = data.get('use_gpt')

            # Analizar el texto con spaCy
            analysis = analyze_text(message)
            
            # Procesar la respuesta basada en el análisis de spaCy
            response = process_spacy_analysis(analysis, message)
            
            # Si no se pudo generar una respuesta con spaCy y se permite usar GPT, usamos GPT
            if not response and use_gpt == 'yes':
                try:
                    gpt_api = GptApi.objects.first()
                    gpt_response = gpt_message(api_token=gpt_api.api_token, text=message, model=gpt_api.model)
                    response = gpt_response['choices'][0]['message']['content']
                except Exception as e:
                    logging.error(f"Error llamando a GPT: {e}")
                    response = "Lo siento, ocurrió un error al procesar tu solicitud."

            # Enviar la respuesta a la plataforma correspondiente
            if platform == 'telegram':
                send_telegram_message(data['username'], response)
            elif platform == 'whatsapp':
                send_whatsapp_message(data['username'], response)
            elif platform == 'messenger':
                send_messenger_message(data['username'], response)

            return JsonResponse({'status': 'success', 'response': response})
        except json.JSONDecodeError:
            logger.error("Error decodificando JSON del cuerpo de la solicitud")
            return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
        except Person.DoesNotExist:
            logger.error(f"Persona no encontrada para user_id: {user_id}")
            return JsonResponse({'status': 'error', 'message': 'Usuario no encontrado'}, status=404)
        except Exception as e:
            logger.exception(f"Error inesperado procesando el mensaje: {e}")
            return JsonResponse({'status': 'error', 'message': 'Error interno del servidor'}, status=500)

    logger.warning(f"Método no permitido: {request.method}")
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

def send_telegram_message(username, message):
    try:
        telegram_api = TelegramAPI.objects.first()
        if telegram_api:
            telegram_send.delay(username, message, telegram_api.api_key)
        else:
            logging.error("No se encontró configuración de API de Telegram")
    except Exception as e:
        logging.error(f"Error al enviar mensaje de Telegram: {e}")

def send_whatsapp_message(username, message):
    try:
        whatsapp_api = WhatsAppAPI.objects.first()
        if whatsapp_api:
            whatsapp_service = WhatsAppService(whatsapp_api.api_token, whatsapp_api.phone_id, whatsapp_api.version_api)
            whatsapp_service.send_message(username, message)
        else:
            logging.error("No se encontró configuración de API de WhatsApp")
    except Exception as e:
        logging.error(f"Error al enviar mensaje de WhatsApp: {e}")

def send_messenger_message(username, message):
    try:
        messenger_api = MessengerAPI.objects.first()
        if messenger_api:
            messenger_service = MessengerService(messenger_api.access_token)
            messenger_service.send_message(username, message)
        else:
            logging.error("No se encontró configuración de API de Messenger")
    except Exception as e:
        logging.error(f"Error al enviar mensaje de Messenger: {e}")

def setup_email_backend():
    smtp_config = SmtpConfig.objects.first()
    if smtp_config:
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        settings.EMAIL_HOST = smtp_config.host
        settings.EMAIL_PORT = smtp_config.port
        settings.EMAIL_HOST_USER = smtp_config.username
        settings.EMAIL_HOST_PASSWORD = smtp_config.password
        settings.EMAIL_USE_TLS = smtp_config.use_tls
        settings.EMAIL_USE_SSL = smtp_config.use_ssl

def create_pregunta(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        # Si 'Pregunta' tiene relaciones ForeignKey o ManyToMany, se puede optimizar con select_related o prefetch_related
        pregunta = Pregunta.objects.create(name=data['name'])
        return JsonResponse({'id': pregunta.id})


def update_pregunta(request, id):
    if request.method == 'PUT':
        data = json.loads(request.body)
        pregunta = Pregunta.objects.get(id=id)
        pregunta.name = data['name']
        pregunta.save()
        return JsonResponse({'status': 'success'})

def update_position(request, id):
    if request.method == 'PUT':
        data = json.loads(request.body)
        pregunta = Pregunta.objects.get(id=id)
        pregunta.position = data['position']  # Suponiendo que tienes un campo de posición
        pregunta.save()
        return JsonResponse({'status': 'success'})

def delete_pregunta(request, id):
    if request.method == 'DELETE':
        pregunta = Pregunta.objects.get(id=id)
        pregunta.delete()
        return JsonResponse({'status': 'deleted'})

def print_pregunta_y_subpreguntas(pregunta):
    print(f"Pregunta: {pregunta.name}")
    for sub_pregunta in pregunta.sub_preguntas.all():
        print(f"    SubPregunta: {sub_pregunta.name}")
        print_pregunta_y_subpreguntas(sub_pregunta)  # Recursividad para explorar más niveles

@csrf_exempt
def save_flow_structure(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        flowmodel_id = data.get('flowmodel_id')
        flow = get_object_or_404(FlowModel, pk=flowmodel_id)
        flow.flow_data_json = json.dumps(data.get('nodes'))
        flow.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


def load_flow_data(request, flowmodel_id):
    flow = FlowModel.objects.get(pk=flowmodel_id)
    flow_data_json = flow.flow_data_json  # Load the flow structure
    return JsonResponse({'flow_data': flow_data_json})

def edit_flow(request, flowmodel_id):
    flow = get_object_or_404(FlowModel, pk=flowmodel_id)
    context = {
        'flow': flow,
        'questions_json': flow.flow_data_json or "[]"  # Asegúrate de pasar un JSON válido o vacío
    }
    return TemplateResponse(request, "admin/chatbot_flow.html", context)

@csrf_exempt
def save_flow_structure(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        flowmodel_id = data.get('flowmodel_id')
        flow = get_object_or_404(FlowModel, pk=flowmodel_id)
        flow.flow_data_json = json.dumps(data.get('nodes'))
        flow.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def export_chatbot_flow(request):
    if request.method == 'POST':
        flow_data = json.loads(request.body)
        return JsonResponse({'status': 'exported', 'data': flow_data})
    return JsonResponse({'status': 'error'}, status=400)

def load_flow_data(request, flowmodel_id):
    # Carga el modelo del flujo con las preguntas y subpreguntas asociadas
    flow = FlowModel.objects.prefetch_related('preguntas__sub_preguntas').get(pk=flowmodel_id)
    
    # Estructura de las preguntas y subpreguntas
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

import logging
logger = logging.getLogger('telegram')

@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            chat_id = body['message']['chat']['id']
            message = body['message']['text']

            logger.debug(f"Received message from chat_id: {chat_id}")

            user_data, botones, pregunta_actual = PersonData.get(str(chat_id))
            if not user_data:
                respuesta = "¡Bienvenido! Vamos a iniciar con las preguntas."
                PersonData.setter(str(chat_id), "Inicio")
            else:
                respuesta = "Gracias por tu mensaje."

            bot_token = TelegramAPI.objects.first().api_key

            send_telegram_message.delay(chat_id, respuesta, bot_token)

            return JsonResponse({"status": "ok"}, status=200)
        except Exception as e:
            logger.error(f"Error in telegram_webhook: {str(e)}", exc_info=True)
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    else:
        logger.warning(f"Received non-POST request to telegram_webhook")
        return JsonResponse({"status": "Método no permitido"}, status=405)