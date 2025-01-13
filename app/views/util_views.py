# /home/pablollh/app/views/utils_views.py

from django.views import View
from django.http import JsonResponse
from app.tasks import send_message, send_notification_task
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit
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
            send_message.delay(recipient, message)
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
            send_notification_task.delay(recipient, notification)
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

@method_decorator(csrf_exempt, name='dispatch')
class DebugView(View):
    """
    Vista para depuración que muestra información detallada de la solicitud.
    """
    def get(self, request):
        debug_info = {
            'method': request.method,
            'path': request.path,
            'GET_params': dict(request.GET),
            'headers': dict(request.headers),
            'META': {k: str(v) for k, v in request.META.items()},
        }
        return JsonResponse(debug_info)

    def post(self, request):
        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            body = "Invalid JSON"

        debug_info = {
            'method': request.method,
            'path': request.path,
            'POST_params': dict(request.POST),
            'body': body,
            'headers': dict(request.headers),
            'META': {k: str(v) for k, v in request.META.items()},
        }
        return JsonResponse(debug_info)

@method_decorator(csrf_exempt, name='dispatch')
class TriggerErrorView(View):
    """
    Vista que intencionalmente genera un error para probar el sistema de monitoreo de errores.
    """
    def get(self, request):
        error_type = request.GET.get('type', 'default')
        
        if error_type == 'zero_division':
            # Genera un error de división por cero
            1/0
        elif error_type == 'key_error':
            # Genera un KeyError
            empty_dict = {}
            empty_dict['nonexistent_key']
        elif error_type == 'type_error':
            # Genera un TypeError
            'string' + 123
        else:
            # Genera una excepción genérica
            logger.error("Error de prueba generado intencionalmente")
            raise Exception("Este es un error de prueba generado intencionalmente")

        # Este código nunca se ejecutará debido a las excepciones anteriores
        return JsonResponse({"status": "error"})