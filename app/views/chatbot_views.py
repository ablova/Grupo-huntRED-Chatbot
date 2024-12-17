# /home/amigro/app/views/chatbot_views.py

from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import logging

from app.chatbot import ChatBotHandler
from app.models import GptApi, Pregunta
from app.gpt import gpt_message
from app.integrations.services import send_message, send_image, send_menu, send_logo
from asgiref.sync import sync_to_async
from app.ml_model import MatchmakingLearningSystem

@login_required
def candidato_predictions(request, candidato_id):
    """
    Devuelve predicciones de éxito para un candidato en todos sus procesos activos.
    """
    try:
        candidato = get_object_or_404(Person, id=candidato_id)
        ml_system = MatchmakingLearningSystem()
        predictions = ml_system.predict_all_active_processes(candidato)
        return JsonResponse({'predictions': predictions})
    except Exception as e:
        logger.error(f"Error obteniendo predicciones para el candidato {candidato_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)
logger = logging.getLogger(__name__)

@login_required
def candidato_recommendations(request, candidato_id):
    """
    Devuelve recomendaciones de habilidades para un candidato específico.
    """
    try:
        candidato = get_object_or_404(Person, id=candidato_id)
        ml_system = MatchmakingLearningSystem()
        recommendations = ml_system.recommend_skill_improvements(candidato)
        return JsonResponse({'recommendations': recommendations})
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
            use_gpt = data.get('use_gpt', 'no')

            if not platform or not sender_id or not message:
                return JsonResponse({'error': 'Missing required fields.'}, status=400)

            response = await process_message(platform, sender_id, message, use_gpt)
            return response

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}", exc_info=True)
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return JsonResponse({'error': 'Internal Server Error'}, status=500)

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
                elif func == 'enviar_whatsapp_plantilla':
                    whatsapp_api = await sync_to_async(WhatsAppAPI.objects.first)()
                    response = await registro_amigro(recipient, whatsapp_api.api_token, whatsapp_api.phoneID, whatsapp_api.v_api, {})
                    responses.append({'function': func, 'response': response})
                elif func == 'send_question':
                    if question_id:
                        question = await sync_to_async(Pregunta.objects.get)(id=question_id)
                        response_text = question.content
                        response = await send_message(platform, recipient, response_text)
                        responses.append({'function': func, 'response': response})
                    else:
                        return JsonResponse({"error": "Se requiere el ID de la pregunta para 'Enviar Pregunta'."}, status=400)
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
                elif func == 'execute_scraping':
                    # Ejecutar el scraping y devolver los resultados
                    vacantes = await ejecutar_scraping_amigro()
                    responses.append({'function': func, 'response': vacantes})
                elif func == 'send_notification':
                    # Enviar notificación
                    message = action
                    await send_notification_task(recipient, message)
                    responses.append({'function': func, 'response': 'Notificación enviada'})
                elif func == 'follow_up_interview':
                    # Seguir con la entrevista
                    await follow_up_notifications_task(recipient)
                    responses.append({'function': func, 'response': 'Seguimiento de entrevista enviado'})
                elif func == 'get_location':
                    # Solicitar ubicación al usuario
                    await request_location(platform, recipient)
                    responses.append({'function': func, 'response': 'Solicitud de ubicación enviada'})
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