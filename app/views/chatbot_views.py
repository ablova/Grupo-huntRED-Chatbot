# /home/pablollh/app/views/chatbot_views.py

from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
#from ratelimit.decorators import ratelimit
import json
import logging 
from app.chatbot.chatbot import ChatBotHandler
from app.models import GptApi, Person, BusinessUnit, ChatState, WhatsAppAPI, TelegramAPI, InstagramAPI, MessengerAPI
from app.chatbot.gpt import GPTHandler
from app.chatbot.integrations.services import send_message, send_image, send_menu, send_logo
from asgiref.sync import sync_to_async
from app.ml.ml_model import MatchmakingLearningSystem
from app.chatbot.utils import format_template_response

logger = logging.getLogger(__name__)

@login_required
def candidato_predictions(request, candidato_id):
    """
    Devuelve predicciones de éxito para un candidato en todos sus procesos activos.
    """
    try:
        candidato = get_object_or_404(Person, id=candidato_id)
        ml_system = MatchmakingLearningSystem()
        predictions = ml_system.predict_all_active_processes(candidato)

        # Formatear predicciones para enviar como respuesta del chatbot
        response_text = format_template_response(
            "Hola {nombre}, estas son tus predicciones de éxito: {predicciones}",
            nombre=candidato.name,
            predicciones=", ".join([f"{p['process']}: {p['score']}%" for p in predictions])
        )

        return JsonResponse({'predictions': predictions, 'response_text': response_text})
    except Exception as e:
        logger.error(f"Error obteniendo predicciones para el candidato {candidato_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def candidato_recommendations(request, candidato_id):
    """
    Devuelve recomendaciones de habilidades para un candidato específico.
    """
    try:
        candidato = get_object_or_404(Person, id=candidato_id)
        ml_system = MatchmakingLearningSystem()
        recommendations = ml_system.recommend_skill_improvements(candidato)

        # Formatear recomendaciones para enviar como respuesta del chatbot
        response_text = format_template_response(
            "Hola {nombre}, estas son tus recomendaciones: {recomendaciones}",
            nombre=candidato.name,
            recomendaciones=", ".join(recommendations)
        )

        return JsonResponse({'recommendations': recommendations, 'response_text': response_text})
    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones para el candidato {candidato_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ProcessMessageView(View):
    """
    Vista para procesar mensajes del chatbot.
    """
    async def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            platform = data.get('platform')
            sender_id = data.get('sender_id')
            message = data.get('message')

            # Validar campos requeridos
            if not all([platform, sender_id, message]):
                return JsonResponse({'error': 'Faltan campos requeridos.'}, status=400)

            response = await process_message(platform, sender_id, message)
            return response

        except json.JSONDecodeError as e:
            logger.error(f"Error de decodificación JSON: {e}", exc_info=True)
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}", exc_info=True)
            return JsonResponse({'error': 'Error interno del servidor'}, status=500)

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
                return JsonResponse({'error': 'Se requiere una plataforma.'}, status=400)

            # Validar funciones
            if not functions:
                return JsonResponse({'error': 'Debe seleccionar al menos una función.'}, status=400)

            # Obtener destinatario basado en la plataforma
            recipient = obtener_destinatario(platform, {'whatsapp_number': phone_number})

            responses = []  # Lista para almacenar las respuestas

            # Procesar cada función seleccionada
            for func in functions:
                if func == 'send_message':
                    response = await send_message(platform, recipient, action)
                    responses.append({'function': func, 'response': response})
                elif func == 'send_image':
                    response = await send_image(platform, recipient, action)  # action contiene la URL de la imagen
                    responses.append({'function': func, 'response': response})
                elif func == 'send_menu':
                    response = await send_menu(platform, recipient)
                    responses.append({'function': func, 'response': response})
                elif func == 'enviar_logo':
                    response = await send_logo(platform, recipient)
                    responses.append({'function': func, 'response': response})
                elif func == 'mostrar_vacantes':
                    # Obtener las vacantes almacenadas o disponibles
                    vacantes = await obtener_vacantes_almacenadas()
                    mensaje_vacantes = formatear_vacantes(vacantes)
                    response = await send_message(platform, recipient, mensaje_vacantes)
                    responses.append({'function': func, 'response': response})
                elif func == 'execute_scraping':
                    # Ejecutar el scraping y devolver los resultados
                    business_unit_name = data.get('business_unit', 'amigro')
                    vacantes = await ejecutar_scraping_amigro(business_unit_name)
                    responses.append({'function': func, 'response': vacantes})
                elif func == 'send_buttons':
                    # Implementar lógica para enviar botones
                    botones = [{'title': 'Opción 1'}, {'title': 'Opción 2'}]
                    response = await send_buttons(platform, recipient, action, botones)
                    responses.append({'function': func, 'response': response})
                elif func == 'send_template_message':
                    # Implementar lógica para enviar mensaje de plantilla
                    response = await send_template_message(platform, recipient, template_name=action)
                    responses.append({'function': func, 'response': response})
                elif func == 'send_media_message':
                    # Implementar lógica para enviar mensaje multimedia
                    media_url = action  # URL del archivo multimedia
                    response = await send_media_message(platform, recipient, media_url)
                    responses.append({'function': func, 'response': response})
                elif func == 'send_notification':
                    # Enviar notificación
                    message = action
                    await send_notification_task(recipient, message)
                    responses.append({'function': func, 'response': 'Notificación enviada'})
                else:
                    responses.append({"error": f"Función '{func}' no reconocida."})
                    return JsonResponse({"error": f"Función '{func}' no reconocida."}, status=400)

            return JsonResponse({'status': 'success', 'message': 'Prueba enviada exitosamente', 'responses': responses}, status=200)

        except Exception as e:
            logger.error(f"Error durante las pruebas: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

def obtener_destinatario(platform, variables):
    """
    Obtiene el destinatario basado en la plataforma.
    """
    if platform == 'whatsapp':
        return variables.get('whatsapp_number', '525518490291')  # Número de WhatsApp por defecto
    elif platform == 'telegram':
        return variables.get('telegram_id', '871198362')  # ID de Telegram por defecto
    elif platform == 'messenger':
        return variables.get('messenger_id', '109623338672452')
    elif platform == 'instagram':
        return variables.get('instagram_id', '109623338672452')
    return None

async def send_message_view(request):
    """
    Vista para enviar un mensaje de WhatsApp desde un formulario o API.
    """
    user_id = request.POST.get('user_id')
    message = request.POST.get('message', "Deja que te ayudemos a encontrar el trabajo de tus sueños")
    phone_id = request.POST.get('phone_id')
    business_unit_id = request.POST.get('business_unit', 4)  # Predeterminado: Amigro

    try:
        # Buscar configuración activa
        whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(
            phoneID=phone_id,
            business_unit_id=business_unit_id,
            is_active=True
        ).first)()

        if not whatsapp_api:
            return JsonResponse({"error": "No se encontró una configuración activa para este Business Unit."}, status=400)

        # Enviar mensaje
        response = await send_whatsapp_message(
            user_id=user_id,
            message=message,
            phone_id=whatsapp_api.phoneID,
            business_unit=whatsapp_api.business_unit
        )
        return JsonResponse(response)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

async def generate_invitation_link_view(request):
    """
    Vista para generar un enlace de invitación de WhatsApp.
    """
    phone_number = request.POST.get('phone_number')
    custom_message = request.POST.get('message', "Deja que te ayudemos a encontrar el trabajo de tus sueños")

    if not phone_number:
        return JsonResponse({"error": "Se requiere un número de teléfono."}, status=400)

    try:
        whatsapp_link = generate_whatsapp_link(phone_number, custom_message)
        return JsonResponse({"whatsapp_link": whatsapp_link})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

class ChatGPTView(View):
    async def post(self, request, *args, **kwargs):
        # Obtener el prompt desde la solicitud
        prompt = request.POST.get('prompt', '')

        if not prompt:
            return JsonResponse({'error': 'No se proporcionó un prompt.'}, status=400)

        try:
            # Crear una instancia asíncrona de GPTHandler
            gpt_handler = await GPTHandler.create()

            # Generar la respuesta de GPT
            response_text = await gpt_handler.generate_response(prompt)

            return JsonResponse({'response': response_text})

        except Exception as e:
            # Manejar errores inesperados
            return JsonResponse({'error': 'Ocurrió un error al procesar la solicitud.'}, status=500)