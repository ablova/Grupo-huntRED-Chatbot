# /home/pablollh/app/views/webhook_views.py

from django.views import View
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from app.chatbot import ChatBotHandler
from app.integrations.instagram import instagram_webhook
from app.integrations.telegram import telegram_webhook
from app.integrations.messenger import messenger_webhook
from app.integrations.whatsapp import whatsapp_webhook
import logging
import json

from app.nlp import SkillExtractor  # Asegúrate de que la importación es correcta
from app.nlp import initialize_phrase_matcher  # Función para inicializar phraseMatcher

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    async def get(self, request, *args, **kwargs):
        try:
            return await whatsapp_webhook(request)
        except Exception as e:
            logger.error(f"Error en WhatsAppWebhook GET: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    async def post(self, request, *args, **kwargs):
        try:
            return await whatsapp_webhook(request)
        except Exception as e:
            logger.error(f"Error en WhatsAppWebhook POST: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(View):
    async def get(self, request, *args, **kwargs):
        try:
            return await telegram_webhook(request)
        except Exception as e:
            logger.error(f"Error en TelegramWebhook GET: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    async def post(self, request, *args, **kwargs):
        try:
            return await telegram_webhook(request)
        except Exception as e:
            logger.error(f"Error en TelegramWebhook POST: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class MessengerWebhookView(View):
    async def get(self, request, *args, **kwargs):
        try:
            return await messenger_webhook(request)
        except Exception as e:
            logger.error(f"Error en MessengerWebhook GET: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    async def post(self, request, *args, **kwargs):
        try:
            return await messenger_webhook(request)
        except Exception as e:
            logger.error(f"Error en MessengerWebhook POST: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class InstagramWebhookView(View):
    async def get(self, request, *args, **kwargs):
        try:
            return await instagram_webhook(request)
        except Exception as e:
            logger.error(f"Error en InstagramWebhook GET: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    async def post(self, request, *args, **kwargs):
        try:
            return await instagram_webhook(request)
        except Exception as e:
            logger.error(f"Error en InstagramWebhook POST: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class JobTrackerUpdateView(View):
    """
    Webhook para recibir actualizaciones de JobTracker.
    """
    async def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            handler = ChatBotHandler()
            await handler.update_candidate_status_from_tracker(data['updates'])
            logger.info("Actualizaciones de JobTracker procesadas correctamente.")
            return JsonResponse({'status': 'success', 'message': 'Actualizaciones procesadas correctamente.'}, status=200)
        except KeyError as e:
            logger.error(f"Clave faltante en el payload de JobTracker: {e}")
            return JsonResponse({'status': 'error', 'message': f"Clave faltante: {e}"}, status=400)
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON: {e}")
            return JsonResponse({'status': 'error', 'message': 'Formato de JSON inválido.'}, status=400)
        except Exception as e:
            logger.error(f"Error procesando actualizaciones de JobTracker: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)