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

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    def post(self, request, *args, **kwargs):
        # Verificar la firma o token de seguridad aquí
        return whatsapp_webhook(request)

@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(View):
    def post(self, request, *args, **kwargs):
        return telegram_webhook(request)

@method_decorator(csrf_exempt, name='dispatch')
class MessengerWebhookView(View):
    def post(self, request, *args, **kwargs):
        return messenger_webhook(request)

@method_decorator(csrf_exempt, name='dispatch')
class InstagramWebhookView(View):
    def get(self, request, *args, **kwargs):
        return instagram_webhook(request)
    
    def post(self, request, *args, **kwargs):
        return instagram_webhook(request)
    
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
            return JsonResponse({'status': 'success', 'message': 'Actualizaciones procesadas correctamente.'}, status=200)
        except Exception as e:
            logger.error(f"Error procesando actualizaciones de JobTracker: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)