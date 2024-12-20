# /home/pablollh/app/views/utils_views.py

from django.views import View
from django.http import JsonResponse
from app.tasks import send_test_message_task, send_test_notification_task
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import httpx
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class SendTestMessageView(View):
    """
    Vista para enviar un mensaje de prueba.
    """
    def get(self, request):
        recipient = request.GET.get('recipient')
        message = request.GET.get('message', 'Este es un mensaje de prueba.')
        if recipient:
            send_test_message_task.delay(recipient, message)
            return JsonResponse({"status": "message en cola para envío"}, status=200)
        else:
            return JsonResponse({"error": "Falta el parámetro 'recipient'."}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class SendTestNotificationView(View):
    """
    Vista para enviar una notificación de prueba.
    """
    def get(self, request):
        recipient = request.GET.get('recipient')
        notification = request.GET.get('notification', 'Esta es una notificación de prueba.')
        if recipient:
            send_test_notification_task.delay(recipient, notification)
            return JsonResponse({"status": "notificación en cola para envío"}, status=200)
        else:
            return JsonResponse({"error": "Falta el parámetro 'recipient'."}, status=400)
        
async def fetch_external_data(request):
    """
    Vista para obtener datos de una API externa.
    """
    response = await httpx.get('https://api.external.com/data')
    data = response.json()
    return JsonResponse(data)