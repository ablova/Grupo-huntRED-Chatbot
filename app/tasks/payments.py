"""
Tareas asíncronas relacionadas con el procesamiento de pagos y transacciones.
Este módulo centraliza todas las operaciones asíncronas de pagos, como procesamiento
de webhooks, recordatorios y actualizaciones de estado.
"""
from celery import shared_task
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
import json
import time
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 5},
    queue='payments'
)
def process_payment_webhook(self, payload, provider, event_type=None, signature=None):
    """
    Procesa webhooks recibidos de proveedores de pago.
    
    Args:
        payload (dict): Contenido del webhook
        provider (str): Proveedor de pago (stripe, paypal, etc.)
        event_type (str): Tipo de evento del webhook
        signature (str): Firma del webhook para verificación
        
    Returns:
        dict: Resultado del procesamiento
    """
    from app.pagos.gateways.webhook_processor import WebhookProcessor
    
    logger.info(f"Processing {provider} webhook: {event_type}")
    
    try:
        processor = WebhookProcessor()
        
        # Registrar webhook recibido en la base de datos
        webhook_id = async_to_sync(processor.register_webhook)(
            provider=provider,
            event_type=event_type,
            payload=payload,
            signature=signature
        )
        
        # Procesar el webhook según el proveedor
        result = async_to_sync(processor.process)(
            provider=provider,
            event_type=event_type,
            payload=payload,
            webhook_id=webhook_id
        )
        
        # Actualizar registro de webhook con el resultado
        async_to_sync(processor.update_webhook_status)(
            webhook_id=webhook_id,
            status="processed",
            processing_result=result
        )
        
        return {
            "success": True,
            "webhook_id": webhook_id,
            "provider": provider,
            "event_type": event_type,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error processing {provider} webhook: {str(e)}", exc_info=True)
        
        # Registrar error en la base de datos si es posible
        try:
            if 'processor' in locals() and 'webhook_id' in locals():
                async_to_sync(processor.update_webhook_status)(
                    webhook_id=webhook_id,
                    status="failed",
                    error=str(e)
                )
        except Exception as inner_e:
            logger.error(f"Error updating webhook status: {str(inner_e)}")
        
        self.retry(exc=e)


@shared_task(queue='payments')
def send_payment_reminder(payment_id, reminder_type="upcoming", days_before=3):
    """
    Envía recordatorios de pago por email y otros canales.
    
    Args:
        payment_id (int): ID del pago a recordar
        reminder_type (str): Tipo de recordatorio (upcoming, due, overdue)
        days_before (int): Días de anticipación para recordatorios futuros
        
    Returns:
        dict: Resultado del envío
    """
    from app.models import Pago, Empleador
    from app.com.notifications.manager import NotificationManager
    
    logger.info(f"Sending {reminder_type} payment reminder for payment {payment_id}")
    
    try:
        # Obtener información del pago
        pago = Pago.objects.select_related('empleador').get(id=payment_id)
        empleador = pago.empleador
        
        # Determinar plantilla según tipo de recordatorio
        template_map = {
            "upcoming": "pagos/email/upcoming_payment.html",
            "due": "pagos/email/payment_due.html",
            "overdue": "pagos/email/payment_overdue.html",
        }
        
        template_name = template_map.get(reminder_type, "pagos/email/payment_reminder.html")
        
        # Contexto para la plantilla
        context = {
            "pago": pago,
            "empleador": empleador,
            "reminder_type": reminder_type,
            "days_before": days_before,
            "fecha_formateada": pago.fecha_vencimiento.strftime("%d/%m/%Y") if pago.fecha_vencimiento else "No especificada",
            "amount_formatted": f"${pago.monto:,.2f}" if pago.monto else "Monto no especificado",
        }
        
        # Renderizar email
        html_content = render_to_string(template_name, context)
        
        # Asunto según tipo
        subject_map = {
            "upcoming": f"Recordatorio de pago próximo - Vence en {days_before} días",
            "due": "Pago vence hoy - Grupo huntRED",
            "overdue": f"Pago vencido - {pago.dias_vencido} días de retraso",
        }
        
        subject = subject_map.get(reminder_type, "Recordatorio de pago - Grupo huntRED")
        
        # Obtener email del empleador
        recipient_email = empleador.email if hasattr(empleador, 'email') and empleador.email else "finanzas@grupohuntred.com"
        
        # Enviar email
        send_mail(
            subject=subject,
            message="",  # Versión texto plano, dejamos vacío para usar HTML
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_content,
            fail_silently=False
        )
        
        # Enviar notificación por otros canales usando el NotificationManager
        async_to_sync(NotificationManager.notify)(
            event_type="payment_reminder",
            user_id=empleador.id if hasattr(empleador, 'id') else None,
            data={
                "payment_id": payment_id,
                "reminder_type": reminder_type,
                "amount": pago.monto,
                "due_date": pago.fecha_vencimiento.isoformat() if pago.fecha_vencimiento else None,
                "days_before": days_before,
            },
            channels=["email", "whatsapp"] if reminder_type == "overdue" else ["email"]
        )
        
        # Actualizar estado de recordatorio en la base de datos
        pago.ultimo_recordatorio = timezone.now()
        pago.recordatorios_enviados = (pago.recordatorios_enviados or 0) + 1
        pago.save(update_fields=['ultimo_recordatorio', 'recordatorios_enviados'])
        
        return {
            "success": True,
            "payment_id": payment_id,
            "reminder_type": reminder_type,
            "recipient": recipient_email
        }
    except Exception as e:
        logger.error(f"Error sending payment reminder: {str(e)}", exc_info=True)
        raise


@shared_task(queue='payments')
def update_payment_status(provider=None, days_threshold=30):
    """
    Actualiza el estado de pagos pendientes, consultando APIs externas si es necesario.
    
    Args:
        provider (str): Proveedor específico a actualizar (None = todos)
        days_threshold (int): Días desde la última actualización para procesar
        
    Returns:
        dict: Estadísticas de la actualización
    """
    from app.models import Pago
    from app.pagos.gateways.stripe_gateway import StripeGateway
    from app.pagos.gateways.paypal_gateway import PayPalGateway
    from datetime import timedelta
    
    logger.info(f"Updating payment status for provider={provider}, threshold={days_threshold} days")
    
    stats = {
        "total_processed": 0,
        "updated": 0,
        "already_updated": 0,
        "errors": 0,
        "by_provider": {}
    }
    
    # Determinar fecha límite para actualización
    threshold_date = timezone.now() - timedelta(days=days_threshold)
    
    try:
        # Consultar pagos pendientes que necesitan actualización
        pagos_query = Pago.objects.filter(
            estado__in=["pendiente", "procesando", "error"],
            ultima_actualizacion__lt=threshold_date
        )
        
        if provider:
            pagos_query = pagos_query.filter(proveedor=provider)
        
        pagos = pagos_query.all()
        stats["total_processed"] = len(pagos)
        
        for pago in pagos:
            try:
                provider_name = pago.proveedor
                transaction_id = pago.transaction_id
                
                if not provider_name or not transaction_id:
                    logger.warning(f"Payment {pago.id} missing provider or transaction_id")
                    stats["errors"] += 1
                    continue
                
                # Incrementar contador por proveedor
                if provider_name not in stats["by_provider"]:
                    stats["by_provider"][provider_name] = {"updated": 0, "errors": 0}
                
                # Actualizar según proveedor
                if provider_name.lower() == "stripe":
                    payment_info = async_to_sync(StripeGateway.get_payment_status)(transaction_id)
                elif provider_name.lower() == "paypal":
                    payment_info = async_to_sync(PayPalGateway.get_payment_status)(transaction_id)
                else:
                    logger.warning(f"Unsupported provider {provider_name} for payment {pago.id}")
                    stats["errors"] += 1
                    stats["by_provider"][provider_name]["errors"] += 1
                    continue
                
                # Actualizar estado en base de datos
                pago.estado = payment_info.get("status", pago.estado)
                pago.ultima_actualizacion = timezone.now()
                pago.detalles_pago = json.dumps(payment_info)
                pago.save(update_fields=['estado', 'ultima_actualizacion', 'detalles_pago'])
                
                stats["updated"] += 1
                stats["by_provider"][provider_name]["updated"] += 1
                
            except Exception as e:
                logger.error(f"Error updating payment {pago.id}: {str(e)}")
                stats["errors"] += 1
                if provider_name in stats["by_provider"]:
                    stats["by_provider"][provider_name]["errors"] += 1
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error in update_payment_status: {str(e)}", exc_info=True)
        raise
