# /home/pablo/app/com/pagos/views/payment_views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from app.ats.pagos.models import Pago
from app.ats.pagos.gateways import PaymentGateway
from app.ats.pagos.services import PagoService
from app.ats.empleadores.models import Empleador
from app.ats.vacantes.models import Vacante

@login_required
def payment_list(request):
    """Lista de pagos realizados."""
    payments = Pago.objects.filter(usuario=request.user)
    return render(request, 'pagos/payment_list.html', {'payments': payments})

@login_required
def initiate_payment(request):
    """Inicia un nuevo pago."""
    if request.method == 'POST':
        amount = float(request.POST.get('amount'))
        currency = request.POST.get('currency', 'MXN')
        description = request.POST.get('description', 'Pago general')
        gateway = request.POST.get('gateway', 'stripe')

        try:
            payment_service = PagoService(request.user)
            payment = payment_service.create_payment(amount, currency, description, gateway)
            return JsonResponse({'success': True, 'payment': payment})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return render(request, 'pagos/initiate_payment.html')

@csrf_exempt
@require_http_methods(['POST'])
def webhook_payment_status(request):
    """Webhook para actualización de estado de pagos."""
    if request.method == 'POST':
        try:
            # Validar firma y procesar webhook
            payment_service = PagoService()
            result = payment_service.process_webhook(request)
            return JsonResponse({'success': True, 'result': result})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return HttpResponseBadRequest('Método no permitido')

@login_required
def refund_payment(request, payment_id):
    """Procesa un reembolso de pago."""
    payment = get_object_or_404(Pago, id=payment_id, usuario=request.user)
    
    try:
        payment_service = PagoService(request.user)
        result = payment_service.refund_payment(payment)
        return JsonResponse({'success': True, 'result': result})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def payment_history(request):
    """Historial de pagos del usuario."""
    payments = Pago.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    return render(request, 'pagos/payment_history.html', {'payments': payments})

@login_required
def payment_details(request, payment_id):
    """Detalles específicos de un pago."""
    payment = get_object_or_404(Pago, id=payment_id, usuario=request.user)
    return render(request, 'pagos/payment_details.html', {'payment': payment})

@login_required
@require_http_methods(['GET', 'POST'])
def create_payment(request):
    """
    Crea un nuevo pago.
    GET: Muestra el formulario de creación
    POST: Procesa el formulario y crea el pago
    """
    if request.method == 'GET':
        # Obtener empleadores y vacantes para el formulario
        empleadores = Empleador.objects.filter(business_unit=request.user.business_unit)
        vacantes = Vacante.objects.filter(business_unit=request.user.business_unit)
        
        return render(request, 'pagos/crear_pago.html', {
            'empleadores': empleadores,
            'vacantes': vacantes
        })
    
    try:
        # Obtener datos del request
        empleador_id = request.POST.get('empleador_id')
        vacante_id = request.POST.get('vacante_id')
        monto = float(request.POST.get('monto'))
        moneda = request.POST.get('moneda', 'MXN')
        metodo = request.POST.get('metodo')
        
        # Crear servicio de pagos
        service = PagoService(business_unit=request.user.business_unit)
        
        # Crear pago
        response = service.crear_pago(
            empleador_id=empleador_id,
            vacante_id=vacante_id,
            monto=monto,
            moneda=moneda,
            metodo=metodo
        )
        
        if response['success']:
            return JsonResponse({
                'success': True,
                'pago_id': response['pago'].id,
                'redirect_url': response['gateway_response'].get('redirect_url')
            })
        
        return JsonResponse({
            'success': False,
            'error': response['error']
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(['POST'])
def execute_payment(request, pago_id):
    """
    Ejecuta un pago existente.
    """
    try:
        # Obtener pago
        pago = get_object_or_404(Pago, id=pago_id)
        
        # Verificar permisos
        if not request.user.has_perm('pagos.execute_payment', pago):
            raise PermissionDenied
        
        # Crear servicio de pagos
        service = PagoService(business_unit=request.user.business_unit)
        
        # Ejecutar pago
        response = service.ejecutar_pago(pago_id)
        
        if response['success']:
            return JsonResponse({
                'success': True,
                'pago_id': response['pago'].id
            })
        
        return JsonResponse({
            'success': False,
            'error': response['error']
        })
        
    except PermissionDenied:
        return JsonResponse({
            'success': False,
            'error': 'No tienes permiso para ejecutar este pago'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_http_methods(['POST'])
def create_payout(request):
    """
    Crea un payout para múltiples pagos.
    """
    try:
        # Obtener IDs de pagos
        pago_ids = request.POST.getlist('pago_ids[]')
        
        # Obtener pagos
        pagos = Pago.objects.filter(id__in=pago_ids)
        
        # Verificar permisos
        for pago in pagos:
            if not request.user.has_perm('pagos.create_payout', pago):
                raise PermissionDenied
        
        # Crear servicio de pagos
        service = PagoService(business_unit=request.user.business_unit)
        
        # Crear payout
        response = service.crear_payout(pagos)
        
        if response['success']:
            return JsonResponse({
                'success': True,
                'payout_id': response['payout_id']
            })
        
        return JsonResponse({
            'success': False,
            'error': response['error']
        })
        
    except PermissionDenied:
        return JsonResponse({
            'success': False,
            'error': 'No tienes permiso para crear payouts'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_http_methods(['POST'])
def process_webhook(request):
    """
    Procesa un webhook de pago.
    Esta vista está exenta de CSRF ya que los webhooks de los gateways de pago
    no pueden incluir el token CSRF.
    """
    try:
        # Verificar IP del remitente si está configurada
        if hasattr(settings, 'ALLOWED_WEBHOOK_IPS'):
            client_ip = request.META.get('REMOTE_ADDR')
            if client_ip not in settings.ALLOWED_WEBHOOK_IPS:
                return JsonResponse({
                    'success': False,
                    'error': 'IP no autorizada'
                }, status=403)
        
        # Obtener datos del webhook
        request_body = request.POST.dict()
        
        # Crear servicio de pagos
        service = PagoService()
        
        # Procesar webhook
        response = service.procesar_webhook(request_body)
        
        if response['success']:
            return JsonResponse({
                'success': True,
                'pago_id': response['pago'].id
            })
        
        return JsonResponse({
            'success': False,
            'error': response['error']
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
