# /home/pablo/app/views/utils_views.py

from django.views import View
from django.http import JsonResponse
from app.tasks import send_notification_task
from django.shortcuts import render
from app.com.utils.salario import calcular_neto, calcular_bruto, obtener_tipo_cambio
from app.com.chatbot.integrations.services import send_message
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
#from ratelimit.decorators import ratelimit
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
    



def calcular_salario(request):
    # Variables iniciales para el cálculo
    salario_bruto = None
    salario_neto = None
    resultado = None
    error = None
    
    # Si el formulario fue enviado
    if request.method == 'POST':
        try:
            salario_bruto = float(request.POST.get('salario_bruto', 0))
            salario_neto = float(request.POST.get('salario_neto', 0))
            tipo_trabajador = request.POST.get('tipo_trabajador', 'asalariado')
            incluye_prestaciones = 'incluye_prestaciones' in request.POST
            monto_vales = float(request.POST.get('monto_vales', 0))
            fondo_ahorro = 'fondo_ahorro' in request.POST
            porcentaje_fondo = float(request.POST.get('porcentaje_fondo', 0.13))  # Default 13%
            credito_infonavit = float(request.POST.get('credito_infonavit', 0))
            pension_alimenticia = float(request.POST.get('pension_alimenticia', 0))
            aplicar_subsidio = 'aplicar_subsidio' in request.POST
            moneda = request.POST.get('moneda', 'MXN')
            tipo_cambio = float(request.POST.get('tipo_cambio', 1.0))

            if salario_bruto:
                # Calcular neto desde bruto
                resultado = calcular_neto(
                    salario_bruto,
                    tipo_trabajador=tipo_trabajador,
                    incluye_prestaciones=incluye_prestaciones,
                    monto_vales=monto_vales,
                    fondo_ahorro=fondo_ahorro,
                    porcentaje_fondo=porcentaje_fondo,
                    credito_infonavit=credito_infonavit,
                    pension_alimenticia=pension_alimenticia,
                    aplicar_subsidio=aplicar_subsidio,
                    moneda=moneda,
                    tipo_cambio=tipo_cambio
                )
            elif salario_neto:
                # Calcular bruto desde neto
                resultado = calcular_bruto(
                    salario_neto,
                    tipo_trabajador=tipo_trabajador,
                    incluye_prestaciones=incluye_prestaciones,
                    monto_vales=monto_vales,
                    fondo_ahorro=fondo_ahorro,
                    porcentaje_fondo=porcentaje_fondo,
                    credito_infonavit=credito_infonavit,
                    pension_alimenticia=pension_alimenticia,
                    aplicar_subsidio=aplicar_subsidio,
                    moneda=moneda,
                    tipo_cambio=tipo_cambio
                )
        except ValueError:
            error = "Por favor ingrese valores válidos."
    
    # Renderizamos el resultado en la plantilla
    return render(request, 'home.html', {'resultado': resultado, 'error': error})