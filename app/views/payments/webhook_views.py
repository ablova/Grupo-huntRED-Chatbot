"""
Vistas para el procesamiento de webhooks de proveedores de pago.
Este módulo implementa los endpoints para recibir y procesar webhooks
de diferentes proveedores como Stripe y PayPal.
"""
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import json
import hmac
import hashlib
import logging
import time
from asgiref.sync import async_to_sync

from app.tasks.payments import process_payment_webhook
from app.models import WebhookLog
from app.utils.rbac import RBAC

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def stripe_webhook_handler(request):
    """
    Endpoint para recibir y procesar webhooks de Stripe.
    
    Esta función verifica la firma del webhook y envía el payload
    para procesamiento asíncrono mediante una tarea de Celery.
    """
    start_time = time.time()
    webhook_id = None
    
    try:
        # Extraer payload
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not sig_header:
            logger.warning("Missing Stripe signature header")
            return HttpResponse(status=400)
            
        # Registrar webhook en base de datos
        webhook_log = WebhookLog.objects.create(
            provider='stripe',
            payload=payload.decode('utf-8'),
            headers=json.dumps({k: v for k, v in request.META.items() if k.startswith('HTTP_')}),
            ip_address=request.META.get('REMOTE_ADDR', '')
        )
        webhook_id = webhook_log.id
        
        # Verificar firma del webhook
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            event_type = event.type
        except ValueError as e:
            logger.error(f"Invalid Stripe payload: {str(e)}")
            webhook_log.status = 'error'
            webhook_log.error_message = f"Invalid payload: {str(e)}"
            webhook_log.save(update_fields=['status', 'error_message'])
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid Stripe signature: {str(e)}")
            webhook_log.status = 'error'
            webhook_log.error_message = f"Invalid signature: {str(e)}"
            webhook_log.save(update_fields=['status', 'error_message'])
            return HttpResponse(status=400)
            
        # Actualizar registro con tipo de evento
        webhook_log.event_type = event_type
        webhook_log.save(update_fields=['event_type'])
        
        # Enviar a procesamiento asíncrono
        process_payment_webhook.delay(
            payload=json.loads(payload),
            provider='stripe',
            event_type=event_type,
            signature=sig_header
        )
        
        # Actualizar registro de webhook
        processing_time = time.time() - start_time
        webhook_log.processing_time = processing_time
        webhook_log.status = 'queued'
        webhook_log.save(update_fields=['processing_time', 'status'])
        
        logger.info(f"Stripe webhook {event_type} queued for processing in {processing_time:.3f}s")
        
        # Devolver respuesta exitosa a Stripe
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Error in Stripe webhook handler: {str(e)}", exc_info=True)
        
        # Actualizar registro de webhook si existe
        if webhook_id:
            try:
                webhook_log = WebhookLog.objects.get(id=webhook_id)
                webhook_log.status = 'error'
                webhook_log.error_message = str(e)
                webhook_log.save(update_fields=['status', 'error_message'])
            except Exception as inner_e:
                logger.error(f"Error updating webhook log: {str(inner_e)}")
                
        return HttpResponse(status=500)
        

@csrf_exempt
@require_POST
def paypal_webhook_handler(request):
    """
    Endpoint para recibir y procesar webhooks de PayPal.
    
    Esta función verifica la autenticidad del webhook y envía el payload
    para procesamiento asíncrono mediante una tarea de Celery.
    """
    start_time = time.time()
    webhook_id = None
    
    try:
        # Extraer payload
        payload = request.body
        auth_algo = request.META.get('HTTP_PAYPAL_AUTH_ALGO')
        cert_url = request.META.get('HTTP_PAYPAL_CERT_URL')
        transmission_id = request.META.get('HTTP_PAYPAL_TRANSMISSION_ID')
        transmission_sig = request.META.get('HTTP_PAYPAL_TRANSMISSION_SIG')
        transmission_time = request.META.get('HTTP_PAYPAL_TRANSMISSION_TIME')
        
        if not all([auth_algo, cert_url, transmission_id, transmission_sig, transmission_time]):
            logger.warning("Missing PayPal verification headers")
            return HttpResponse(status=400)
            
        # Registrar webhook en base de datos
        webhook_log = WebhookLog.objects.create(
            provider='paypal',
            payload=payload.decode('utf-8'),
            headers=json.dumps({k: v for k, v in request.META.items() if k.startswith('HTTP_')}),
            ip_address=request.META.get('REMOTE_ADDR', '')
        )
        webhook_id = webhook_log.id
        
        # Parsear el payload
        event_data = json.loads(payload)
        event_type = event_data.get('event_type', 'unknown')
        
        # Actualizar registro con tipo de evento
        webhook_log.event_type = event_type
        webhook_log.save(update_fields=['event_type'])
        
        # Enviar a procesamiento asíncrono
        process_payment_webhook.delay(
            payload=event_data,
            provider='paypal',
            event_type=event_type,
            signature={
                'auth_algo': auth_algo,
                'cert_url': cert_url,
                'transmission_id': transmission_id,
                'transmission_sig': transmission_sig,
                'transmission_time': transmission_time
            }
        )
        
        # Actualizar registro de webhook
        processing_time = time.time() - start_time
        webhook_log.processing_time = processing_time
        webhook_log.status = 'queued'
        webhook_log.save(update_fields=['processing_time', 'status'])
        
        logger.info(f"PayPal webhook {event_type} queued for processing in {processing_time:.3f}s")
        
        # Devolver respuesta exitosa a PayPal
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Error in PayPal webhook handler: {str(e)}", exc_info=True)
        
        # Actualizar registro de webhook si existe
        if webhook_id:
            try:
                webhook_log = WebhookLog.objects.get(id=webhook_id)
                webhook_log.status = 'error'
                webhook_log.error_message = str(e)
                webhook_log.save(update_fields=['status', 'error_message'])
            except Exception as inner_e:
                logger.error(f"Error updating webhook log: {str(inner_e)}")
                
        return HttpResponse(status=500)


@csrf_exempt
@require_POST
def process_webhook(request, provider):
    """
    Endpoint genérico para procesar webhooks de cualquier proveedor.
    
    Args:
        provider: Nombre del proveedor (stripe, paypal, etc.)
    """
    start_time = time.time()
    webhook_id = None
    
    try:
        # Extraer payload
        payload = request.body
        
        # Registrar webhook en base de datos
        webhook_log = WebhookLog.objects.create(
            provider=provider,
            payload=payload.decode('utf-8'),
            headers=json.dumps({k: v for k, v in request.META.items() if k.startswith('HTTP_')}),
            ip_address=request.META.get('REMOTE_ADDR', '')
        )
        webhook_id = webhook_log.id
        
        # Parsear el payload
        event_data = json.loads(payload)
        event_type = event_data.get('event_type', event_data.get('type', 'unknown'))
        
        # Actualizar registro con tipo de evento
        webhook_log.event_type = event_type
        webhook_log.save(update_fields=['event_type'])
        
        # Enviar a procesamiento asíncrono
        process_payment_webhook.delay(
            payload=event_data,
            provider=provider,
            event_type=event_type
        )
        
        # Actualizar registro de webhook
        processing_time = time.time() - start_time
        webhook_log.processing_time = processing_time
        webhook_log.status = 'queued'
        webhook_log.save(update_fields=['processing_time', 'status'])
        
        logger.info(f"{provider.capitalize()} webhook {event_type} queued for processing in {processing_time:.3f}s")
        
        # Devolver respuesta exitosa
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Error in {provider} webhook handler: {str(e)}", exc_info=True)
        
        # Actualizar registro de webhook si existe
        if webhook_id:
            try:
                webhook_log = WebhookLog.objects.get(id=webhook_id)
                webhook_log.status = 'error'
                webhook_log.error_message = str(e)
                webhook_log.save(update_fields=['status', 'error_message'])
            except Exception as inner_e:
                logger.error(f"Error updating webhook log: {str(inner_e)}")
                
        return HttpResponse(status=500)
