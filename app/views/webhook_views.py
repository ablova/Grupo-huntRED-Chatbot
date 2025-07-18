# /home/pablo/app/views/webhook_views.py

from django.views import View
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
#from ratelimit.decorators import ratelimit
from app.ats.chatbot.core.chatbot import ChatBotHandler
from app.ats.integrations.channels.instagram import instagram_webhook
from app.ats.integrations.channels.telegram import telegram_webhook
from app.ats.integrations.channels.messenger import messenger_webhook
from app.ats.integrations.channels.whatsapp import whatsapp_webhook
import logging
import json

#from app.ats.chatbot.nlp.nlp import get_skill_extractor # Asegúrate de que la importación es correcta


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
        bot_name = kwargs.get('bot_name', None)
        if not bot_name:
            return JsonResponse({'status': 'error', 'message': 'Bot name no proporcionado'}, status=400)
        logger.info(f"📩 Webhook de Telegram (GET) activado para {bot_name}")
        return await telegram_webhook(request, bot_name)

    async def post(self, request, *args, **kwargs):
        bot_name = kwargs.get('bot_name', None)
        if not bot_name:
            return JsonResponse({'status': 'error', 'message': 'Bot name no proporcionado'}, status=400)
        logger.info(f"📩 Webhook de Telegram (POST) activado para {bot_name}")
        try:
            return await telegram_webhook(request, bot_name)
        except Exception as e:
            logger.error(f"❌ Error en TelegramWebhook POST: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class MessengerWebhookView(View):
    async def get(self, request, *args, **kwargs):
        page_id = kwargs.get('page_id')
        if not page_id:
            logger.error("GET request sin page_id")
            return JsonResponse({'status': 'error', 'message': 'page_id no proporcionado'}, status=400)
        
        try:
            return await messenger_webhook(request, page_id)
        except Exception as e:
            logger.error(f"Error en MessengerWebhook GET para page_id {page_id}: {e}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    async def post(self, request, *args, **kwargs):
        page_id = kwargs.get('page_id')  # Extraer page_id de la URL
        try:
            return await messenger_webhook(request, page_id)
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