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
from app.models import BusinessUnit, Person
from app.chatbot.gpt import GPTHandler
from app.chatbot.integrations.services import send_message
from asgiref.sync import sync_to_async
from app.ml.ml_model import MatchmakingLearningSystem
from app.chatbot.utils import format_template_response

logger = logging.getLogger(__name__)

@login_required
def candidato_predictions(request, candidato_id):
    """Devuelve predicciones de éxito para un candidato en todos sus procesos activos."""
    try:
        candidato = get_object_or_404(Person, id=candidato_id)
        return JsonResponse({'predictions': "Funcionalidad futura pendiente"})
    except Exception as e:
        logger.error(f"Error obteniendo predicciones para el candidato {candidato_id}: {e}")
        return JsonResponse({'status': 'error', 'detail': str(e)}, status=500)

@login_required
async def candidato_recommendations(request, candidato_id):
    """Devuelve recomendaciones de habilidades para un candidato específico."""
    try:
        candidato = get_object_or_404(Person, id=candidato_id)
        ml_system = MatchmakingLearningSystem()
        recommendations = await sync_to_async(ml_system.recommend_skill_improvements)(candidato)
        response_text = format_template_response(
            "Hola {nombre}, estas son tus recomendaciones: {recomendaciones}",
            nombre=candidato.name,
            recomendaciones=", ".join(recommendations)
        )
        return JsonResponse({'recommendations': recommendations, 'response_text': response_text})
    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones para el candidato {candidato_id}: {e}")
        return JsonResponse({'status': 'error', 'detail': str(e)}, status=500)

@method_decorator([csrf_exempt], name='dispatch') # se quito #, ratelimit(key='ip', rate='10/m', method='POST')
class ProcessMessageView(View):
    """Vista para procesar mensajes del chatbot."""
    async def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body)
            platform = body.get('platform')
            user_id = body.get('user_id')
            message = body.get('message')
            
            if not all([platform, user_id, message]):
                logger.error(f"Datos incompletos: platform={platform}, user_id={user_id}, message={message}")
                return JsonResponse({'status': 'error', 'message': 'Datos incompletos'}, status=400)
            
            # Procesar mensaje (asumiendo una función existente)
            success = await process_chatbot_message(platform, user_id, message)
            return JsonResponse({'status': 'success' if success else 'error'})
        
        except json.JSONDecodeError:
            logger.error("Error decodificando JSON en ProcessMessageView")
            return JsonResponse({'status': 'error', 'message': 'Formato JSON inválido'}, status=400)
        except Exception as e:
            logger.error(f"Error en ProcessMessageView: {e}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
async def send_test_message(request):
    """Vista para enviar un mensaje de prueba desde la interfaz de administrador."""
    user_id = request.GET.get('user_id')
    message = request.GET.get('message', "Mensaje de prueba")
    try:
        await send_message("whatsapp", user_id, message, "amigro")
        return JsonResponse({"status": "success"})
    except Exception as e:
        logger.error(f"Error enviando mensaje de prueba: {e}")
        return JsonResponse({"status": "error", "detail": str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SendChatbotMessageView(View):
    """Vista para enviar un mensaje a un usuario nuevo o existente, especificando plataforma y BusinessUnit."""
    async def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            platform = data.get('platform')  # e.g., "whatsapp", "telegram"
            message = data.get('message', "Bienvenido a nuestro servicio.")
            business_unit_id = data.get('business_unit_id')  # ID del BusinessUnit
            user_id = data.get('user_id')  # ID del usuario existente (opcional)
            phone_number = data.get('phone_number')  # Número para nuevo usuario (opcional)

            # Validar campos requeridos
            if not platform or not business_unit_id or (not user_id and not phone_number):
                return JsonResponse(
                    {'status': 'error', 'detail': 'Se requieren platform, business_unit_id y al menos user_id o phone_number.'},
                    status=400
                )

            # Obtener BusinessUnit
            business_unit = await sync_to_async(BusinessUnit.objects.get)(id=business_unit_id)
            if not business_unit:
                return JsonResponse({'status': 'error', 'detail': 'BusinessUnit no encontrado.'}, status=404)

            # Determinar el destinatario
            if user_id:
                # Usuario existente
                user = await sync_to_async(Person.objects.filter)(id=user_id).first()
                if not user:
                    return JsonResponse({'status': 'error', 'detail': 'Usuario no encontrado.'}, status=404)
                recipient_id = user.phone
            else:
                # Nuevo usuario
                recipient_id = phone_number
                user, created = await sync_to_async(Person.objects.get_or_create)(
                    phone=phone_number,
                    defaults={'nombre': 'Nuevo Usuario', 'business_unit': business_unit}
                )
                if created:
                    logger.info(f"Nuevo usuario creado: {phone_number} para BU: {business_unit.name}")

            # Enviar mensaje
            await send_message(platform, recipient_id, message, business_unit.name)
            logger.info(f"Mensaje enviado a {recipient_id} en {platform} para BU: {business_unit.name}")

            return JsonResponse({'status': 'success', 'detail': f'Mensaje enviado a {recipient_id}'})
        except json.JSONDecodeError as e:
            logger.error(f"Error de decodificación JSON: {e}", exc_info=True)
            return JsonResponse({'status': 'error', 'detail': 'JSON inválido'}, status=400)
        except BusinessUnit.DoesNotExist:
            return JsonResponse({'status': 'error', 'detail': 'BusinessUnit no encontrado.'}, status=404)
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}", exc_info=True)
            return JsonResponse({'status': 'error', 'detail': str(e)}, status=500)

async def send_message_view(request):
    """Vista para enviar un mensaje de WhatsApp desde un formulario o API."""
    user_id = request.POST.get('user_id')
    message = request.POST.get('message', "Deja que te ayudemos a encontrar el trabajo de tus sueños")
    business_unit_id = request.POST.get('business_unit', 4)
    try:
        business_unit = await sync_to_async(BusinessUnit.objects.get)(id=business_unit_id)
        await send_message("whatsapp", user_id, message, business_unit.name)
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "detail": str(e)}, status=500)

@csrf_exempt
async def generate_invitation_link_view(request):
    """Vista para generar un enlace de invitación de WhatsApp."""
    phone_number = request.POST.get('phone_number')
    custom_message = request.POST.get('message', "Deja que te ayudemos a encontrar el trabajo de tus sueños")
    if not phone_number:
        return JsonResponse({"status": "error", "detail": "Se requiere un número de teléfono."}, status=400)
    try:
        whatsapp_link = f"https://wa.me/{phone_number}?text={custom_message.replace(' ', '%20')}"
        return JsonResponse({"whatsapp_link": whatsapp_link})
    except Exception as e:
        logger.error(f"Error generando enlace de invitación: {e}")
        return JsonResponse({"status": "error", "detail": str(e)}, status=500)

class ChatGPTView(View):
    """Vista para generar respuestas GPT."""
    async def post(self, request, *args, **kwargs):
        prompt = request.POST.get('prompt', '')
        if not prompt:
            return JsonResponse({'status': 'error', 'detail': 'No se proporcionó un prompt.'}, status=400)
        try:
            gpt_handler = GPTHandler()
            await gpt_handler.initialize()
            response_text = await gpt_handler.generate_response(prompt)
            return JsonResponse({'response': response_text})
        except Exception as e:
            return JsonResponse({'status': 'error', 'detail': str(e)}, status=500)