# /home/pablo/app/pagos/views/payment_views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse
from app.pagos.models import Pago
from app.pagos.gateways import PaymentGateway
from app.pagos.services import PaymentService

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
            payment_service = PaymentService(request.user)
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
            payment_service = PaymentService()
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
        payment_service = PaymentService(request.user)
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
