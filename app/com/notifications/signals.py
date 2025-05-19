# /home/pablo/app/com/notifications/signals.py
#
# Señales para el sistema de notificaciones. Conecta eventos del sistema con el envío 
# de notificaciones a los diferentes usuarios según su rol y momento en el proceso.

import logging
from typing import Dict, Any, Optional
from asgiref.sync import async_to_sync

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from app.models import (
    Vacante, Person, BusinessUnit, User, Company, 
    CartaOferta, Entrevista, ChatState, Factura
)
from app.com.pricing.models import PaymentMilestone

from app.com.notifications.managersmanagers import (
    VacanteManager, ProcesoNotificationManager, ClienteNotificationManager,
    ConsultorNotificationManager, PagosNotificationManager, CandidatoNotificationManager
)

logger = logging.getLogger('notification_signals')

# =====================================================
# Señales para Vacantes
# =====================================================

@receiver(post_save, sender=Vacante)
def vacante_notification_handler(sender, instance, created, **kwargs):
    """
    Maneja notificaciones para eventos relacionados con vacantes.
    """
    try:
        # Evitamos recursión y procesamiento innecesario
        if kwargs.get('raw', False) or kwargs.get('signal_processed', False):
            return
            
        manager = VacanteManager(instance)
        
        # Evento de creación de vacante
        if created:
            logger.info(f"Nueva vacante creada: {instance.id} - {instance.title}")
            async_to_sync(manager.notify_all_stakeholders)(event_type='proceso_creado')
            
        # Eventos basados en cambio de estado
        else:
            old_instance = getattr(instance, '_old_instance', None)
            old_status = getattr(old_instance, 'status', None) if old_instance else None
            
            # Solo si el estado cambió
            if old_status and old_status != instance.status:
                # Nuevo estado: entrevista programada
                if instance.status == 'interview_scheduled':
                    # Buscamos entrevistas recién programadas
                    entrevistas = Entrevista.objects.filter(
                        vacante=instance, 
                        created_at__gte=timezone.now() - timezone.timedelta(minutes=5)
                    ).order_by('-created_at')
                    
                    if entrevistas.exists():
                        entrevista = entrevistas.first()
                        candidato = entrevista.person
                        
                        context = {
                            'candidato': candidato,
                            'entrevista_fecha': entrevista.fecha_hora,
                            'entrevista_virtual': entrevista.tipo == 'virtual',
                            'entrevista_link': entrevista.link,
                            'entrevista_lugar': entrevista.lugar
                        }
                        
                        async_to_sync(manager.notify_all_stakeholders)(
                            event_type='entrevista_programada',
                            context=context
                        )
                
                # Nuevo estado: se buscan candidatos
                elif instance.status == 'searching':
                    async_to_sync(manager.notify_all_stakeholders)(event_type='busqueda_iniciada')
                
                # Nuevo estado: cubierta
                elif instance.status == 'filled':
                    async_to_sync(manager.notify_all_stakeholders)(event_type='vacante_cubierta')
                
                # Nuevo estado: cerrada/cancelada
                elif instance.status in ['closed', 'cancelled']:
                    async_to_sync(manager.notify_all_stakeholders)(event_type='vacante_cerrada')
    
    except Exception as e:
        logger.error(f"Error procesando notificación para vacante {instance.id}: {e}")

# Guardar estado previo para detectar cambios
@receiver(pre_save, sender=Vacante)
def store_vacante_old_state(sender, instance, **kwargs):
    """Guarda el estado previo de la vacante para comparación."""
    try:
        if instance.pk:
            instance._old_instance = Vacante.objects.get(pk=instance.pk)
    except Vacante.DoesNotExist:
        pass

# =====================================================
# Señales para Candidatos
# =====================================================

@receiver(post_save, sender=Person)
def candidate_notification_handler(sender, instance, created, **kwargs):
    """
    Maneja notificaciones para eventos relacionados con candidatos.
    """
    try:
        # Evitamos recursión
        if kwargs.get('raw', False) or kwargs.get('signal_processed', False):
            return
            
        # Solo procesamos candidatos (role='candidate')
        if getattr(instance, 'role', None) != 'candidate':
            return
            
        # Obtenemos el estado anterior
        old_instance = getattr(instance, '_old_instance', None)
        old_state = getattr(old_instance, 'state', None) if old_instance else None
        
        # Obtenemos la vacante principal de este candidato
        vacante = None
        if hasattr(instance, 'vacante') and instance.vacante:
            vacante = instance.vacante
        elif hasattr(instance, 'get_primary_vacancy'):
            vacante = instance.get_primary_vacancy()
            
        if not vacante:
            return
            
        # Solo si el candidato está asociado a una vacante
        manager = VacanteManager(vacante)
            
        # Evento de nuevo candidato
        if created:
            # Solo si está asociado a una vacante existente
            async_to_sync(manager.notify_all_stakeholders)(
                event_type='nuevo_candidato',
                context={'candidato': instance}
            )
            
        # Eventos basados en cambio de estado
        elif old_state and old_state != instance.state:
            # Candidato avanzó en el proceso
            if instance.state == 'shortlisted' and old_state in ['new', 'active']:
                async_to_sync(manager.notify_all_stakeholders)(
                    event_type='candidato_preseleccionado',
                    context={'candidato': instance}
                )
                
            # Candidato contratado
            elif instance.state == 'hired' and old_state != 'hired':
                async_to_sync(manager.notify_all_stakeholders)(
                    event_type='candidato_contratado',
                    context={'candidato': instance}
                )
                
            # Candidato rechazado
            elif instance.state == 'rejected' and old_state != 'rejected':
                async_to_sync(manager.notify_all_stakeholders)(
                    event_type='candidato_rechazado',
                    context={'candidato': instance}
                )
    
    except Exception as e:
        logger.error(f"Error procesando notificación para candidato {instance.id}: {e}")

# Guardar estado previo para detectar cambios
@receiver(pre_save, sender=Person)
def store_person_old_state(sender, instance, **kwargs):
    """Guarda el estado previo del candidato para comparación."""
    try:
        if instance.pk:
            instance._old_instance = Person.objects.get(pk=instance.pk)
    except Person.DoesNotExist:
        pass

# =====================================================
# Señales para Entrevistas
# =====================================================

@receiver(post_save, sender=Entrevista)
def entrevista_notification_handler(sender, instance, created, **kwargs):
    """
    Maneja notificaciones para eventos relacionados con entrevistas.
    """
    try:
        # Evitamos recursión
        if kwargs.get('raw', False) or kwargs.get('signal_processed', False):
            return
            
        # Solo nos interesa cuando se crea una entrevista
        if created and instance.vacante and instance.person:
            vacante = instance.vacante
            candidato = instance.person
            
            # Creamos el manager
            manager = VacanteManager(vacante)
            
            # Preparamos el contexto para la notificación
            context = {
                'candidato': candidato,
                'entrevista_fecha': instance.fecha_hora,
                'entrevista_virtual': instance.tipo == 'virtual',
                'entrevista_link': instance.link,
                'entrevista_lugar': instance.lugar
            }
            
            # Enviamos notificación de entrevista programada
            async_to_sync(manager.notify_all_stakeholders)(
                event_type='entrevista_programada',
                context=context
            )
    
    except Exception as e:
        logger.error(f"Error procesando notificación para entrevista {instance.id}: {e}")

# =====================================================
# Señales para Carta Oferta
# =====================================================

@receiver(post_save, sender=CartaOferta)
def carta_oferta_notification_handler(sender, instance, created, **kwargs):
    """
    Maneja notificaciones para eventos relacionados con cartas oferta.
    """
    try:
        # Evitamos recursión
        if kwargs.get('raw', False) or kwargs.get('signal_processed', False):
            return
            
        # Solo procesamos cuando cambia el estado
        old_instance = getattr(instance, '_old_instance', None)
        old_status = getattr(old_instance, 'status', None) if old_instance else None
        
        if instance.vacante and instance.candidate:
            vacante = instance.vacante
            candidato = instance.candidate
            
            # Creamos el manager
            manager = VacanteManager(vacante)
            
            # Evento de carta oferta creada
            if created:
                # Enviamos notificación de oferta generada
                async_to_sync(manager.notify_all_stakeholders)(
                    event_type='oferta_emitida',
                    context={
                        'candidato': candidato,
                        'oferta': instance
                    }
                )
                
            # Eventos basados en cambio de estado
            elif old_status and old_status != instance.status:
                # Oferta aceptada
                if instance.status == 'accepted' and old_status != 'accepted':
                    async_to_sync(manager.notify_all_stakeholders)(
                        event_type='oferta_aceptada',
                        context={
                            'candidato': candidato,
                            'oferta': instance
                        }
                    )
                    
                # Oferta rechazada
                elif instance.status == 'rejected' and old_status != 'rejected':
                    async_to_sync(manager.notify_all_stakeholders)(
                        event_type='oferta_rechazada',
                        context={
                            'candidato': candidato,
                            'oferta': instance
                        }
                    )
    
    except Exception as e:
        logger.error(f"Error procesando notificación para carta oferta {instance.id}: {e}")

# Guardar estado previo para detectar cambios
@receiver(pre_save, sender=CartaOferta)
def store_carta_oferta_old_state(sender, instance, **kwargs):
    """Guarda el estado previo de la carta oferta para comparación."""
    try:
        if instance.pk:
            instance._old_instance = CartaOferta.objects.get(pk=instance.pk)
    except CartaOferta.DoesNotExist:
        pass

# =====================================================
# Señales para Pagos y Facturación
# =====================================================

@receiver(post_save, sender=Factura)
def factura_notification_handler(sender, instance, created, **kwargs):
    """
    Maneja notificaciones para eventos relacionados con facturas.
    """
    try:
        # Evitamos recursión
        if kwargs.get('raw', False) or kwargs.get('signal_processed', False):
            return
            
        if hasattr(instance, 'vacante') and instance.vacante:
            vacante = instance.vacante
            
            # Creamos el manager
            manager = VacanteManager(vacante)
            
            # Factura creada - enviar notificación al cliente
            if created:
                # Datos de la factura para el contexto
                factura_data = {
                    'numero': instance.numero_factura,
                    'fecha_emision': instance.fecha_emision,
                    'fecha_vencimiento': instance.fecha_vencimiento,
                    'monto_total': instance.monto_total,
                    'concepto': instance.concepto
                }
                
                # Datos bancarios desde settings (podría venir de configuración)
                from django.conf import settings
                datos_bancarios = {
                    'banco': getattr(settings, 'PAYMENT_BANK_NAME', 'BBVA'),
                    'titular': getattr(settings, 'PAYMENT_ACCOUNT_HOLDER', 'Grupo huntRED, S.A. de C.V.'),
                    'cuenta': getattr(settings, 'PAYMENT_ACCOUNT_NUMBER', '012345678901234567'),
                    'clabe': getattr(settings, 'PAYMENT_CLABE', '012180001234567890')
                }
                
                # Enviar notificación de factura emitida
                async_to_sync(manager.notify_all_stakeholders)(
                    event_type='factura_emitida',
                    context={
                        'factura': factura_data,
                        'datos_bancarios': datos_bancarios
                    }
                )
                
            # Eventos basados en cambio de estado
            else:
                old_instance = getattr(instance, '_old_instance', None)
                old_status = getattr(old_instance, 'status', None) if old_instance else None
                
                # Cambio de estado en la factura
                if old_status and old_status != instance.status:
                    # Factura pagada
                    if instance.status == 'paid' and old_status != 'paid':
                        async_to_sync(manager.notify_all_stakeholders)(
                            event_type='factura_pagada',
                            context={'factura': instance}
                        )
                        
                    # Factura vencida
                    elif instance.status == 'overdue' and old_status != 'overdue':
                        async_to_sync(manager.notify_all_stakeholders)(
                            event_type='factura_vencida',
                            context={'factura': instance}
                        )
    
    except Exception as e:
        logger.error(f"Error procesando notificación para factura {instance.id}: {e}")

# Señal para hitos de pago (Payment Milestones)
@receiver(post_save, sender=PaymentMilestone)
def payment_milestone_handler(sender, instance, created, **kwargs):
    """
    Maneja notificaciones para eventos relacionados con hitos de pago.
    """
    try:
        # Evitamos recursión
        if kwargs.get('raw', False) or kwargs.get('signal_processed', False):
            return
            
        # Procesamos cuando un hito llega a su fecha o cambia de estado
        if hasattr(instance, 'status') and instance.status == 'due':
            if hasattr(instance, 'vacante') and instance.vacante:
                vacante = instance.vacante
                
                # Creamos el manager
                manager = VacanteManager(vacante)
                
                # Preparamos el contexto con los datos del hito
                context = {
                    'milestone': {
                        'nombre': instance.nombre,
                        'porcentaje': instance.porcentaje,
                        'monto': instance.monto,
                        'fecha_vencimiento': instance.fecha_vencimiento
                    }
                }
                
                # Enviamos notificación del hito de pago
                async_to_sync(manager.notify_all_stakeholders)(
                    event_type='hito_pago',
                    context=context
                )
    
    except Exception as e:
        logger.error(f"Error procesando notificación para hito de pago {instance.id}: {e}")

# Guardar estado previo para detectar cambios
@receiver(pre_save, sender=Factura)
def store_factura_old_state(sender, instance, **kwargs):
    """Guarda el estado previo de la factura para comparación."""
    try:
        if instance.pk:
            instance._old_instance = Factura.objects.get(pk=instance.pk)
    except Factura.DoesNotExist:
        pass
