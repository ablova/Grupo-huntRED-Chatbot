# /home/amigro/app/views.py

# Importaciones estándar de Python
import json
import logging

# Librerías de terceros
import spacy
import graphviz
from asgiref.sync import sync_to_async

# Importaciones de Django
from django.conf import settings
from django.views import View
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from app.models import BusinessUnit, ChatState

@staff_member_required
def interacciones_por_unidad(request):
    data = []
    units = BusinessUnit.objects.all()
    for unit in units:
        count = ChatState.objects.filter(platform__icontains=unit.name.lower()).count()
        data.append({'unidad': unit.name, 'interacciones': count})
    return render(request, 'admin/estadisticas/interacciones.html', {'data': data})

# Importaciones de utilidades y funciones internas
from .nlp_utils import analyze_text
from .gpt import gpt_message
from app.chatbot import ChatBotHandler

# Importaciones de integraciones
from app.integrations.services import (
    send_message, send_image, send_menu,
    send_logo, render_dynamic_content
)
from app.integrations.whatsapp import (
    registro_amigro, nueva_posicion_amigro
)
from app.wordpress_integration import (
    login, register, solicitud, consult
)

# Importaciones de modelos
from .models import (
    GptApi, SmtpConfig, Pregunta,
    FlowModel, ChatState, Condicion,
    Etapa, Person, BusinessUnit, WhatsAppAPI, TelegramAPI, MessengerAPI, InstagramAPI
)

logger = logging.getLogger(__name__)

# Configuración de spaCy
nlp = spacy.load("es_core_news_sm")

# Vista para la página principal
def index(request):
    return render(request, "index.html")
# SECCIÓN PARA EL VISUALIZADOR
# Vista para cargar los datos del flujo desde el modelo
def load_flow(request):
    flowmodel_id = request.GET.get('flowmodel_id')
    if flowmodel_id:
        try:
            flow = FlowModel.objects.get(id=flowmodel_id)
            flow_data = flow.flow_data_json
            return JsonResponse({'nodes': flow_data['nodes'], 'links': flow_data['links']})
        except FlowModel.DoesNotExist:
            return JsonResponse({'error': 'Flow not found'}, status=404)
    return JsonResponse({'error': 'No flowmodel_id provided'}, status=400)

@csrf_exempt
def create_pregunta(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            next_si = Pregunta.objects.get(id=data.get('next_si')) if data.get('next_si') else None
            next_no = Pregunta.objects.get(id=data.get('next_no')) if data.get('next_no') else None
            
            pregunta = Pregunta.objects.create(
                name=data.get('name', "Nombre por defecto"),
                content=data.get('content', ""),
                next_si=next_si,
                next_no=next_no,
                # Otros campos según tu necesidad
            )
            return JsonResponse({'id': pregunta.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def update_pregunta(request, id):
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            pregunta = get_object_or_404(Pregunta, id=id)
            pregunta.name = data.get('name', pregunta.name)
            pregunta.content = data.get('content', pregunta.content)
            pregunta.next_si = Pregunta.objects.get(id=data.get('next_si')) if data.get('next_si') else None
            pregunta.next_no = Pregunta.objects.get(id=data.get('next_no')) if data.get('next_no') else None
            pregunta.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def delete_pregunta(request, id):
    if request.method == 'DELETE':
        pregunta = get_object_or_404(Pregunta, id=id)
        pregunta.delete()
        return JsonResponse({'status': 'deleted'})

# Función para actualizar posiciones de preguntas
@csrf_exempt
def update_position(request, id):
    if request.method == 'PUT':
        data = json.loads(request.body)
        pregunta = get_object_or_404(Pregunta, id=id)
        pregunta.position = data.get('position', pregunta.position)
        pregunta.save()
        return JsonResponse({'status': 'success'})

# Función para imprimir pregunta (recursiva)
def print_pregunta(pregunta):
    print(f"Pregunta: {pregunta.name}")
    if pregunta.next_si:
        print(f"    Siguiente (Si): {pregunta.next_si.name}")
    if pregunta.next_no:
        print(f"    Siguiente (No): {pregunta.next_no.name}")

# Cargar datos del flujo
def load_flow_data(request, flowmodel_id):
    flow = get_object_or_404(FlowModel, pk=flowmodel_id)
    flow_data_json = flow.flow_data_json
    return JsonResponse({'flow_data': flow_data_json})

# Vista para editar el flujo del chatbot
@login_required
def edit_flow(request, flowmodel_id):
    flow = get_object_or_404(FlowModel, pk=flowmodel_id)
    flows = FlowModel.objects.all()
    context = {
        'flow': flow,
        'flows': flows,
        'questions_json': flow.flow_data_json or "[]",
        'csrf_token': get_token(request),  # Añade el token CSRF si es necesario
    }
    logger.info(f"Accediendo a edit_flow con ID: {flowmodel_id}")
    return TemplateResponse(request, "admin/chatbot_flow.html", context)

# Guardar la estructura del flujo
@csrf_exempt
def save_flow_structure(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            flowmodel_id = data.get('flowmodel_id')
            flow = get_object_or_404(FlowModel, id=flowmodel_id)
            flow.flow_data_json = json.dumps({
                'nodes': data.get('nodes', []),
                'links': data.get('links', [])
            })
            flow.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Error al guardar el flujo: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

# Exportar el flujo del chatbot
@csrf_exempt
def export_chatbot_flow(request):
    if request.method == 'POST':
        flow_data = json.loads(request.body)
        return JsonResponse({'status': 'exported', 'data': flow_data})
    return JsonResponse({'status': 'error'}, status=400)

# Función para cargar preguntas asociadas al flujo
def load_flow_questions_data(request, flowmodel_id):
    try:
        # Obtén el flujo y sus preguntas asociadas
        flow = FlowModel.objects.prefetch_related('preguntas').get(pk=flowmodel_id)

        # Construir la estructura del flujo
        flow_structure = {
            'flow_data': flow.flow_data_json,  # JSON del flujo
            'preguntas': [
                {
                    'id': pregunta.id,
                    'name': pregunta.name,
                    'content': pregunta.content,
                    'next_si': pregunta.next_si.id if pregunta.next_si else None,
                    'next_no': pregunta.next_no.id if pregunta.next_no else None,
                }
                for pregunta in flow.preguntas.all()
            ]
        }

        return JsonResponse(flow_structure, safe=False)
    except FlowModel.DoesNotExist:
        return JsonResponse({'error': 'FlowModel not found'}, status=404)

# Nueva función para procesar mensajes sin necesidad de request
def process_message(platform, sender_id, message, use_gpt):
    """
    Procesa un mensaje entrante y responde a través de la plataforma correspondiente.
    
    Args:
        platform (str): La plataforma (whatsapp, telegram, etc.).
        sender_id (str): El ID del remitente del mensaje.
        message (str): El mensaje de texto recibido.
        use_gpt (str): Indicador para usar GPT o no ('yes' o 'no').

    Returns:
        JsonResponse: Estado de éxito o error con la respuesta generada.
    """
    try:
        logger.info(f"Procesando mensaje de {platform} para {sender_id}: '{message}'")

        # Analizar el mensaje usando la función NLP
        analysis = analyze_text(message)
        logger.debug(f"Análisis del mensaje: {analysis}")

        # Respuesta inicial con SpaCy
        response = process_spacy_analysis(analysis, message)
        logger.debug(f"Respuesta de SpaCy: {response}")

        # Si no hay respuesta y está activado el uso de GPT, llamar a GPT
        if not response and use_gpt.lower() == 'yes':
            gpt_api = GptApi.objects.first()
            if not gpt_api:
                logger.error("No se encontró configuración para GptApi.")
                return JsonResponse({'status': 'error', 'message': 'GPT API no configurada'}, status=500)

            logger.info("Llamando a GPT para generar respuesta.")
            gpt_response = gpt_message(api_token=gpt_api.api_token, text=message, model=gpt_api.model)

            # Validar la respuesta de GPT
            if 'choices' in gpt_response and gpt_response['choices']:
                response_content = gpt_response['choices'][0]['message']['content']
                response = response_content.strip()
                logger.debug(f"Respuesta de GPT: {response}")
            else:
                logger.error("Respuesta inválida de GPT.")
                response = "Lo siento, no pude generar una respuesta en este momento."

        # Validar que la respuesta sea texto antes de enviarla
        if not isinstance(response, str) or not response:
            logger.error(f"Respuesta inválida: {response}")
            response = "Lo siento, ocurrió un error al procesar tu mensaje."

        # Enviar la respuesta usando la plataforma
        logger.info(f"Enviando respuesta a {sender_id} en {platform}: '{response}'")
        send_message(platform, sender_id, response)

        return JsonResponse({'status': 'success', 'response': response})

    except Exception as e:
        logger.exception(f"Error procesando el mensaje: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# Nueva función para pruebas de chatbot
@csrf_exempt
async def send_test_message(request):
    """
    Maneja las pruebas de acciones del chatbot enviadas desde el frontend.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            platform = data.get('platform')
            action = data.get('action')
            functions = data.get('functions', [])
            phone_number = data.get('phone_number', '525518490291')
            question_id = data.get('question_id')

            handler = ChatBotHandler()

            # Validar plataforma
            if not platform:
                return JsonResponse({'error': 'Platform is required.'}, status=400)

            # Validar funciones
            if not functions:
                return JsonResponse({'error': 'At least one function must be selected.'}, status=400)

            # Obtener destinatario basado en la plataforma
            recipient = obtener_destinatario(platform, {'whatsapp_number': phone_number})

            # Procesar cada función seleccionada
            for func in functions:
                if func == 'send_message':
                    await send_message(platform, recipient, action)
                elif func == 'send_image':
                    await send_image(platform, recipient, action)
                elif func == 'send_menu':
                    await send_menu(platform, recipient)
                elif func == 'enviar_logo':
                    await send_logo(platform, recipient)
                elif func == 'mostrar_vacantes':
                    # Aquí puedes implementar la lógica para mostrar vacantes
                    await send_message(platform, recipient, "Aquí están las vacantes disponibles...")
                elif func == 'enviar_whatsapp_plantilla':
                    whatsapp_api = await sync_to_async(WhatsAppAPI.objects.first)()
                    await registro_amigro(recipient, whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api, {})
                elif func == 'send_question':
                    if question_id:
                        question = await sync_to_async(Pregunta.objects.get)(id=question_id)
                        response = render_dynamic_content(question.content, {})
                        await send_message(platform, recipient, response)
                    else:
                        return JsonResponse({"error": "Question ID is required for 'send_question' function."}, status=400)
                else:
                    return JsonResponse({"error": f"Function '{func}' not recognized."}, status=400)

            return JsonResponse({'status': 'success', 'message': 'Test sent successfully'}, status=200)

        except Exception as e:
            logger.error(f"Error during testing: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

# Función auxiliar para enviar imágenes
async def enviar_imagen(platform, variables, image_url):
    """
    Send image via platform.
    """
    recipient = obtener_destinatario(platform, variables)
    if recipient:
        await send_image(platform, recipient, image_url)

# Función auxiliar para enviar menús
async def enviar_menu(platform, variables, _):
    """
    Send menu via platform.
    """
    recipient = obtener_destinatario(platform, variables)
    if recipient:
        await send_menu(platform, recipient)

# Función para obtener destinatario basado en la plataforma
def obtener_destinatario(platform, variables):
    """
    Retrieve recipient information based on the platform.
    """
    if platform == 'whatsapp':
        return variables.get('whatsapp_number', '525518490291')  # Default WhatsApp number
    elif platform == 'telegram':
        return variables.get('telegram_id', '871198362')  # Default Telegram ID
    elif platform == 'messenger':
        return variables.get('messenger_id', '109623338672452')
    elif platform == 'instagram':
        return variables.get('instagram_id', '109623338672452')
    return None

def login_view(request):
    """
    Vista para autenticar a un usuario en WordPress desde la interfaz de Django.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        login_status = login(username, password)
        if login_status:
            return JsonResponse({"status": "success"})
        else:
            return JsonResponse({"status": "error", "message": "Login failed."})

def submit_application(request, job_id):
    """
    Enviar solicitud a una vacante específica.
    """
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")
        solicitud_response = solicitud("https://amigro.org/solicitud/", name, email, message, job_id)
        return JsonResponse({"status": "success", "message": solicitud_response})
    
def test_scraping_view(request):
    bu_name = request.GET.get("business_unit", "amigro")
    business_unit = BusinessUnit.objects.get(name=bu_name)
    vacantes = consult(page=1, url="https://amigro.org/job-listings/", business_unit=business_unit)
    return JsonResponse({"vacantes": vacantes})

def send_test_notification(request):
    try:
        config = Configuracion.objects.first()
        if not config or not config.is_test_mode:
            return JsonResponse({'error': 'Modo de prueba desactivado'}, status=400)

        test_number = config.test_phone_number
        test_message = "Esta es una notificación de prueba desde el sistema Amigro."
        send_whatsapp_msg(test_number, test_message)
        
        return JsonResponse({'status': 'success'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class CreateFlowView(View):
    def post(self, request):
        logger.debug(f"Headers recibidos: {request.headers}")
        logger.debug(f"Body recibido: {request.body}")
        try:
            data = json.loads(request.body)
            name = data.get('nombre')  # Cambiado de 'name' a 'nombre' para coincidir con tu JSON
            description = data.get('description')
            flow_data = data.get('flow_data')

            if not name or not flow_data:
                return JsonResponse({'success': False, 'error': 'Nombre y datos del flujo son requeridos.'}, status=400)

            # Crear el flujo
            flow = FlowModel.objects.create(
                name=name, 
                description=description, 
                flow_data_json=json.dumps(flow_data)  # Convertir a string JSON
            )

            # Generar diagrama si es necesario
            diagram_path = self.generate_flow_diagram(flow)

            return JsonResponse({
                'success': True, 
                'flow_id': flow.id, 
                'diagram_path': diagram_path,
                'message': 'Flujo creado exitosamente'
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    def generate_flow_diagram(self, flow):
        try:
            dot = graphviz.Digraph()
            flow_data = json.loads(flow.flow_data_json)
            
            # Crear nodos
            for node in flow_data.get('nodes', []):
                dot.node(str(node), str(node))
            
            # Crear conexiones
            for edge in flow_data.get('edges', []):
                if len(edge) == 2:
                    dot.edge(str(edge[0]), str(edge[1]))
            
            file_path = f'/home/amigro/flow_diagrams/flow_{flow.id}'
            dot.render(file_path, format='png', cleanup=True)
            
            return f'{file_path}.png'
        except Exception as e:
            logger.error(f'Error al generar el diagrama: {e}')
            return None

