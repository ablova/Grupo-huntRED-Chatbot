"""
Señales relacionadas con el módulo de pagos en Grupo huntRED®.
Gestiona las señales para eventos de pagos, facturas y transacciones.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver, Signal
from django.utils import timezone
from app.models import Payment, Invoice, BusinessUnit
from app.tasks import (
    update_payment_status,
    process_payment_webhook
)

logger = logging.getLogger(__name__)

# Señales personalizadas
payment_processed = Signal()
payment_failed = Signal()
invoice_generated = Signal()

@receiver(post_save, sender=Payment)
def handle_payment_update(sender, instance, created, **kwargs):
    """
    Maneja actualizaciones en pagos, generando notificaciones
    y actualizando estados relacionados.
    """
    if created:
        logger.info(f"Nuevo pago registrado: {instance.reference} - {instance.amount}")
        
        # Emitir señal personalizada
        payment_processed.send(
            sender=sender,
            payment=instance,
            status=instance.status,
            amount=instance.amount
        )
        
        # Si el pago está asociado a una factura, actualizar su estado
        if instance.invoice:
            if instance.status == 'completed':
                instance.invoice.status = 'paid'
                instance.invoice.paid_date = timezone.now()
                instance.invoice.save()
                logger.info(f"Factura {instance.invoice.reference} marcada como pagada")
    
    elif instance.tracker.has_changed('status'):
        logger.info(f"Estado de pago actualizado: {instance.reference} - {instance.status}")
        
        # Si el pago falló, emitir señal correspondiente
        if instance.status == 'failed':
            payment_failed.send(
                sender=sender,
                payment=instance,
                previous_status=instance.tracker.previous('status')
            )


@receiver(post_save, sender=Invoice)
def handle_invoice_creation(sender, instance, created, **kwargs):
    """
    Maneja la creación y actualización de facturas.
    """
    if created:
        logger.info(f"Nueva factura generada: {instance.reference} - {instance.total_amount}")
        
        # Emitir señal personalizada
        invoice_generated.send(
            sender=sender,
            invoice=instance,
            business_unit=instance.business_unit,
            amount=instance.total_amount
        )
        
        # Actualizar métricas del business unit si aplica
        if instance.business_unit:
            try:
                # Actualizar total facturado
                instance.business_unit.total_invoiced = (
                    instance.business_unit.total_invoiced or 0
                ) + instance.total_amount
                instance.business_unit.save(update_fields=['total_invoiced'])
            except Exception as e:
                logger.error(f"Error actualizando métricas de BU: {str(e)}")
