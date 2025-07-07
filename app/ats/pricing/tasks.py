"""
Tareas Celery para el módulo de pricing.
"""
from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from app.ats.pricing.services.scheduled_payment_service import (
    ScheduledPaymentService,
    execute_scheduled_payments_task,
    execute_paypal_scheduled_payments_task,
    execute_stripe_scheduled_payments_task
)
from app.ats.pricing.services.payment_processing_service import PaymentProcessingService
from app.ats.pricing.services.electronic_billing_service import ElectronicBillingService
from app.ats.pricing.services.integrations.wordpress_sync_service import WordPressSyncService

logger = logging.getLogger('pricing_tasks')


@shared_task
def execute_daily_scheduled_payments():
    """
    Tarea diaria para ejecutar pagos programados.
    Se ejecuta automáticamente todos los días a las 6:00 AM.
    """
    try:
        logger.info("Iniciando ejecución diaria de pagos programados")
        result = execute_scheduled_payments_task()
        logger.info(f"Ejecución diaria completada: {result}")
        return result
    except Exception as e:
        logger.error(f"Error en ejecución diaria: {str(e)}")
        return {'error': str(e)}


@shared_task
def execute_paypal_scheduled_payments():
    """
    Tarea para ejecutar pagos programados vía PayPal.
    Se ejecuta automáticamente todos los días a las 8:00 AM.
    """
    try:
        logger.info("Iniciando ejecución PayPal de pagos programados")
        result = execute_paypal_scheduled_payments_task()
        logger.info(f"Ejecución PayPal completada: {result}")
        return result
    except Exception as e:
        logger.error(f"Error en ejecución PayPal: {str(e)}")
        return {'error': str(e)}


@shared_task
def execute_stripe_scheduled_payments():
    """
    Tarea para ejecutar pagos programados vía Stripe.
    Se ejecuta automáticamente todos los días a las 8:30 AM.
    """
    try:
        logger.info("Iniciando ejecución Stripe de pagos programados")
        result = execute_stripe_scheduled_payments_task()
        logger.info(f"Ejecución Stripe completada: {result}")
        return result
    except Exception as e:
        logger.error(f"Error en ejecución Stripe: {str(e)}")
        return {'error': str(e)}


@shared_task
def process_pending_electronic_invoices():
    """
    Tarea para procesar facturas electrónicas pendientes.
    Se ejecuta automáticamente cada hora.
    """
    try:
        from app.models import Invoice, BusinessUnit
        
        logger.info("Iniciando procesamiento de facturas electrónicas pendientes")
        
        business_units = BusinessUnit.objects.all()
        total_processed = 0
        total_errors = 0
        
        for business_unit in business_units:
            # Obtener facturas pendientes de facturación electrónica
            pending_invoices = Invoice.objects.filter(
                business_unit=business_unit,
                electronic_billing_status='pending'
            )
            
            billing_service = ElectronicBillingService(business_unit)
            
            for invoice in pending_invoices:
                try:
                    result = billing_service.process_invoice_electronic_billing(invoice)
                    if result.get('success'):
                        total_processed += 1
                        logger.info(f"Factura {invoice.invoice_number} procesada exitosamente")
                    else:
                        total_errors += 1
                        logger.error(f"Error procesando factura {invoice.invoice_number}: {result.get('error')}")
                except Exception as e:
                    total_errors += 1
                    logger.error(f"Error procesando factura {invoice.invoice_number}: {str(e)}")
        
        result = {
            'total_processed': total_processed,
            'total_errors': total_errors,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Procesamiento de facturas electrónicas completado: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error en procesamiento de facturas electrónicas: {str(e)}")
        return {'error': str(e)}


@shared_task
def sync_wordpress_pricing():
    """
    Tarea para sincronizar pricing con WordPress.
    Se ejecuta automáticamente cada 6 horas.
    """
    try:
        from app.models import BusinessUnit
        
        logger.info("Iniciando sincronización de pricing con WordPress")
        
        business_units = BusinessUnit.objects.all()
        total_synced = 0
        total_errors = 0
        
        for business_unit in business_units:
            try:
                sync_service = WordPressSyncService(business_unit.name)
                result = sync_service.sincronizar_pricing()
                
                if result.get('success'):
                    total_synced += 1
                    logger.info(f"Pricing de {business_unit.name} sincronizado exitosamente")
                else:
                    total_errors += 1
                    logger.error(f"Error sincronizando pricing de {business_unit.name}: {result.get('error')}")
            except Exception as e:
                total_errors += 1
                logger.error(f"Error sincronizando {business_unit.name}: {str(e)}")
        
        result = {
            'total_synced': total_synced,
            'total_errors': total_errors,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Sincronización de pricing completada: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error en sincronización de pricing: {str(e)}")
        return {'error': str(e)}


@shared_task
def sync_wordpress_opportunities():
    """
    Tarea para sincronizar oportunidades con WordPress.
    Se ejecuta automáticamente cada 2 horas.
    """
    try:
        from app.ats.models import Oportunidad
        
        logger.info("Iniciando sincronización de oportunidades con WordPress")
        
        # Obtener oportunidades no sincronizadas
        opportunities = Oportunidad.objects.filter(
            estado='activo'
        ).select_related('empleador__persona')
        
        total_synced = 0
        total_errors = 0
        
        for opportunity in opportunities:
            try:
                # Verificar si ya fue sincronizada recientemente
                recent_sync = opportunity.sincronizaciones.filter(
                    estado='EXITO',
                    fecha_creacion__gte=timezone.now() - timedelta(hours=1)
                ).first()
                
                if recent_sync:
                    continue
                
                # Sincronizar oportunidad
                from app.ats.pricing.services.integrations.wordpress_sync_service import WordPressSyncService
                sync_service = WordPressSyncService(opportunity.empleador.persona.business_unit.name)
                result = sync_service.sincronizar_oportunidad(opportunity.id)
                
                if result.get('success'):
                    total_synced += 1
                    logger.info(f"Oportunidad {opportunity.id} sincronizada exitosamente")
                else:
                    total_errors += 1
                    logger.error(f"Error sincronizando oportunidad {opportunity.id}: {result.get('error')}")
            except Exception as e:
                total_errors += 1
                logger.error(f"Error sincronizando oportunidad {opportunity.id}: {str(e)}")
        
        result = {
            'total_synced': total_synced,
            'total_errors': total_errors,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Sincronización de oportunidades completada: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error en sincronización de oportunidades: {str(e)}")
        return {'error': str(e)}


@shared_task
def cleanup_old_payment_transactions():
    """
    Tarea para limpiar transacciones de pago antiguas.
    Se ejecuta automáticamente cada semana.
    """
    try:
        from app.ats.models import PaymentTransaction
        
        logger.info("Iniciando limpieza de transacciones antiguas")
        
        # Eliminar transacciones fallidas de más de 30 días
        cutoff_date = timezone.now() - timedelta(days=30)
        old_failed_transactions = PaymentTransaction.objects.filter(
            status='failed',
            created_at__lt=cutoff_date
        )
        
        deleted_count = old_failed_transactions.count()
        old_failed_transactions.delete()
        
        result = {
            'deleted_transactions': deleted_count,
            'cutoff_date': cutoff_date.isoformat(),
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Limpieza de transacciones completada: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error en limpieza de transacciones: {str(e)}")
        return {'error': str(e)}


@shared_task
def generate_payment_reports():
    """
    Tarea para generar reportes de pagos.
    Se ejecuta automáticamente cada día a las 11:00 PM.
    """
    try:
        from app.ats.models import PaymentTransaction
        from django.db.models import Sum, Count
        from datetime import datetime, timedelta
        
        logger.info("Iniciando generación de reportes de pagos")
        
        # Reporte del día
        today = timezone.now().date()
        today_transactions = PaymentTransaction.objects.filter(
            created_at__date=today
        )
        
        today_stats = {
            'total_transactions': today_transactions.count(),
            'completed_transactions': today_transactions.filter(status='completed').count(),
            'total_amount': today_transactions.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0,
            'failed_transactions': today_transactions.filter(status='failed').count(),
        }
        
        # Reporte del mes
        month_start = today.replace(day=1)
        month_transactions = PaymentTransaction.objects.filter(
            created_at__date__gte=month_start
        )
        
        month_stats = {
            'total_transactions': month_transactions.count(),
            'completed_transactions': month_transactions.filter(status='completed').count(),
            'total_amount': month_transactions.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0,
            'failed_transactions': month_transactions.filter(status='failed').count(),
        }
        
        result = {
            'today': today_stats,
            'month': month_stats,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Generación de reportes completada: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error generando reportes: {str(e)}")
        return {'error': str(e)}


# ============================================================================
# CONFIGURACIÓN DE TAREAS PERIÓDICAS
# ============================================================================

# Estas tareas se configuran en settings.py para ejecutarse automáticamente

SCHEDULED_TASKS = {
    'execute_daily_scheduled_payments': {
        'task': 'app.ats.pricing.tasks.execute_daily_scheduled_payments',
        'schedule': timedelta(days=1),
        'options': {'expires': 3600}  # Expira en 1 hora
    },
    'execute_paypal_scheduled_payments': {
        'task': 'app.ats.pricing.tasks.execute_paypal_scheduled_payments',
        'schedule': timedelta(days=1),
        'options': {'expires': 3600}
    },
    'execute_stripe_scheduled_payments': {
        'task': 'app.ats.pricing.tasks.execute_stripe_scheduled_payments',
        'schedule': timedelta(days=1),
        'options': {'expires': 3600}
    },
    'process_pending_electronic_invoices': {
        'task': 'app.ats.pricing.tasks.process_pending_electronic_invoices',
        'schedule': timedelta(hours=1),
        'options': {'expires': 1800}  # Expira en 30 minutos
    },
    'sync_wordpress_pricing': {
        'task': 'app.ats.pricing.tasks.sync_wordpress_pricing',
        'schedule': timedelta(hours=6),
        'options': {'expires': 3600}
    },
    'sync_wordpress_opportunities': {
        'task': 'app.ats.pricing.tasks.sync_wordpress_opportunities',
        'schedule': timedelta(hours=2),
        'options': {'expires': 1800}
    },
    'cleanup_old_payment_transactions': {
        'task': 'app.ats.pricing.tasks.cleanup_old_payment_transactions',
        'schedule': timedelta(days=7),
        'options': {'expires': 7200}  # Expira en 2 horas
    },
    'generate_payment_reports': {
        'task': 'app.ats.pricing.tasks.generate_payment_reports',
        'schedule': timedelta(days=1),
        'options': {'expires': 3600}
    },
} 