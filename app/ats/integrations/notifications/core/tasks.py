"""
Tareas programadas para el sistema de notificaciones.

Implementa tareas Celery para el procesamiento asíncrono de notificaciones,
programación de envíos y limpieza de registros antiguos.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from django.utils import timezone
from asgiref.sync import async_to_sync
from celery import shared_task
from datetime import datetime

from app.models import BusinessUnit, Person, Vacante, User, Notification, NotificationStatus
from app.ats.notifications.managerscore import send_notification
from app.ats.notifications.managershandlers import (
    EmailNotificationHandler, WhatsAppNotificationHandler,
    SMSNotificationHandler, TelegramNotificationHandler,
    AppNotificationHandler, SlackNotificationHandler
)
from app.ats.notifications.specific_notifications import (
    placement_notifier, payment_notifier,
    process_notifier, metrics_notifier, event_notifier,
    alert_notifier
)
from app.ats.integrations.notifications.user_notifications import get_user_notifier

logger = logging.getLogger('notifications')

@shared_task
def process_notification_queue(limit=50):
    """
    Procesa la cola de notificaciones pendientes.
    
    Args:
        limit: Número máximo de notificaciones a procesar en una ejecución
    """
    # Obtenemos las notificaciones pendientes que ya deberían haberse enviado
    now = timezone.now()
    notifications = Notification.objects.filter(
        status=NotificationStatus.PENDING,
        scheduled_for__lte=now
    ).order_by('created_at')[:limit]
    
    processed = 0
    for notification in notifications:
        try:
            # Enviamos la notificación usando el handler correspondiente
            business_unit = notification.business_unit
            
            # Determinamos qué canales usar basados en los datos de la notificación
            handlers = []
            if notification.email_data is not None:
                handlers.append(EmailNotificationHandler(business_unit))
            if notification.whatsapp_data is not None:
                handlers.append(WhatsAppNotificationHandler(business_unit))
            if notification.sms_data is not None:
                handlers.append(SMSNotificationHandler(business_unit))
            if notification.telegram_data is not None:
                handlers.append(TelegramNotificationHandler(business_unit))
            if notification.app_data is not None:
                handlers.append(AppNotificationHandler(business_unit))
            if notification.slack_data is not None:
                handlers.append(SlackNotificationHandler(business_unit))
            
            # Si no hay handlers específicos, usamos email y whatsapp por defecto
            if not handlers:
                handlers = [
                    EmailNotificationHandler(business_unit),
                    WhatsAppNotificationHandler(business_unit)
                ]
            
            # Enviamos la notificación por cada canal
            for handler in handlers:
                try:
                    # Convertimos la llamada asíncrona a síncrona
                    async_to_sync(handler.send)(notification)
                except Exception as e:
                    logger.error(f"Error enviando notificación {notification.id} por {handler.__class__.__name__}: {e}")
            
            processed += 1
            
        except Exception as e:
            logger.error(f"Error procesando notificación {notification.id}: {e}")
            notification.mark_as_failed(str(e))
    
    return f"Procesadas {processed} notificaciones"

@shared_task
def send_scheduled_notification(notification_id):
    """
    Envía una notificación programada específica.
    
    Args:
        notification_id: ID de la notificación a enviar
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        
        # Solo procesamos si está pendiente y su tiempo programado ya pasó
        now = timezone.now()
        if notification.status == NotificationStatus.PENDING and notification.scheduled_for <= now:
            # Determinamos qué canales usar
            business_unit = notification.business_unit
            
            # Por defecto usamos email y whatsapp
            handlers = [
                EmailNotificationHandler(business_unit),
                WhatsAppNotificationHandler(business_unit)
            ]
            
            # Enviamos la notificación por cada canal
            for handler in handlers:
                try:
                    # Convertimos la llamada asíncrona a síncrona
                    async_to_sync(handler.send)(notification)
                except Exception as e:
                    logger.error(f"Error enviando notificación {notification_id} por {handler.__class__.__name__}: {e}")
            
            return f"Notificación {notification_id} enviada"
        else:
            return f"Notificación {notification_id} no está lista para envío"
    
    except Notification.DoesNotExist:
        logger.error(f"Notificación {notification_id} no encontrada")
        return f"Notificación {notification_id} no encontrada"
    
    except Exception as e:
        logger.error(f"Error procesando notificación {notification_id}: {e}")
        return f"Error: {str(e)}"

@shared_task
def send_daily_status_reports():
    """
    Envía reportes diarios de estado para cada proceso activo.
    """
    from app.models import Vacante
    from app.ats.notifications.managersmanagers import ConsultorNotificationManager
    
    # Obtenemos todas las vacantes activas
    vacantes_activas = Vacante.objects.filter(status='active')
    sent_count = 0
    
    for vacante in vacantes_activas:
        try:
            # Determinamos la unidad de negocio
            business_unit = None
            if hasattr(vacante, 'business_unit') and vacante.business_unit:
                business_unit = vacante.business_unit
            else:
                # Intentamos obtener la BU de otra manera si es necesario
                from app.ats.utils.vacantes import get_business_unit_for_vacante
                business_unit = get_business_unit_for_vacante(vacante)
            
            if not business_unit:
                logger.warning(f"No se pudo determinar BU para vacante {vacante.id}")
                continue
            
            # Determinamos el consultor asignado
            consultor = getattr(vacante, 'consultor', None)
            if not consultor:
                logger.warning(f"Vacante {vacante.id} no tiene consultor asignado")
                continue
            
            # Obtenemos las estadísticas y actividades
            from app.ats.utils.reporting import get_vacancy_stats
            stats = get_vacancy_stats(vacante.id)
            
            # Preparamos los datos para la notificación
            context = {
                'stats': stats.get('summary', {}),
                'actividades_recientes': stats.get('recent_activities', []),
                'proximos_pasos': stats.get('next_steps', []),
                'dashboard_url': f"{business_unit.dashboard_url}/vacancy/{vacante.id}"
            }
            
            # Creamos el gestor de notificaciones y enviamos el reporte
            manager = ConsultorNotificationManager(business_unit)
            async_to_sync(manager.enviar_estatus_diario)(
                consultor=consultor,
                vacante=vacante,
                stats=context['stats'],
                actividades_recientes=context['actividades_recientes'],
                proximos_pasos=context['proximos_pasos'],
                dashboard_url=context['dashboard_url']
            )
            
            sent_count += 1
            
        except Exception as e:
            logger.error(f"Error enviando reporte diario para vacante {vacante.id}: {e}")
    
    return f"Enviados {sent_count} reportes diarios"

@shared_task
def send_payment_reminders():
    """
    Envía recordatorios de pago para facturas próximas a vencer.
    """
    from app.ats.pagos.models import Invoice
    from app.ats.notifications.managersmanagers import PagosNotificationManager
    
    # Obtenemos facturas que vencen en los próximos 5 días y no están pagadas
    now = timezone.now()
    five_days_later = now + timezone.timedelta(days=5)
    
    facturas_por_vencer = Invoice.objects.filter(
        due_date__gte=now,
        due_date__lte=five_days_later,
        status='pending'
    )
    
    sent_count = 0
    for factura in facturas_por_vencer:
        try:
            # Obtenemos la vacante relacionada
            vacante = getattr(factura, 'vacante', None)
            if not vacante:
                logger.warning(f"Factura {factura.id} no tiene vacante asociada")
                continue
            
            # Determinamos la unidad de negocio
            business_unit = None
            if hasattr(vacante, 'business_unit') and vacante.business_unit:
                business_unit = vacante.business_unit
            else:
                # Intentamos obtener la BU de otra manera si es necesario
                from app.ats.utils.vacantes import get_business_unit_for_vacante
                business_unit = get_business_unit_for_vacante(vacante)
            
            if not business_unit:
                logger.warning(f"No se pudo determinar BU para factura {factura.id}")
                continue
            
            # Obtenemos el contacto de facturación
            contacto = None
            if hasattr(factura, 'contact') and factura.contact:
                contacto = factura.contact
            elif hasattr(vacante, 'empresa') and hasattr(vacante.empresa, 'contacto_facturacion'):
                contacto = vacante.empresa.contacto_facturacion
            
            if not contacto:
                logger.warning(f"No se pudo determinar contacto para factura {factura.id}")
                continue
            
            # Preparamos los datos para la notificación
            factura_data = {
                'numero': factura.invoice_number,
                'fecha_emision': factura.issue_date,
                'fecha_vencimiento': factura.due_date,
                'monto_total': factura.total_amount,
                'concepto': factura.concept
            }
            
            # Obtenemos los datos bancarios
            from django.conf import settings
            datos_bancarios = {
                'banco': settings.PAYMENT_BANK_NAME,
                'titular': settings.PAYMENT_ACCOUNT_HOLDER,
                'cuenta': settings.PAYMENT_ACCOUNT_NUMBER,
                'clabe': settings.PAYMENT_CLABE
            }
            
            # Creamos el gestor de notificaciones y enviamos el recordatorio
            manager = PagosNotificationManager(business_unit)
            async_to_sync(manager.enviar_recordatorio_pago)(
                contacto=contacto,
                vacante=vacante,
                factura=factura_data,
                datos_bancarios=datos_bancarios
            )
            
            sent_count += 1
            
        except Exception as e:
            logger.error(f"Error enviando recordatorio de pago para factura {factura.id}: {e}")
    
    return f"Enviados {sent_count} recordatorios de pago"

@shared_task
def clean_old_notifications(days=90):
    """
    Elimina notificaciones antiguas para mantener la base de datos ligera.
    
    Args:
        days: Antigüedad en días para considerar una notificación como vieja
    """
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    
    # Eliminamos notificaciones antiguas que ya han sido leídas o fallaron
    result = Notification.objects.filter(
        created_at__lt=cutoff_date,
        status__in=[NotificationStatus.READ, NotificationStatus.FAILED]
    ).delete()
    
    return f"Eliminadas {result[0]} notificaciones antiguas"

# =====================================================
# Tareas para Notificaciones Específicas
# =====================================================

@shared_task
def send_user_notification(
    business_unit_id: int,
    user_id: int,
    person_id: int,
    notification_type: str,
    **kwargs
) -> bool:
    """
    Tarea para enviar notificaciones de usuario.
    """
    try:
        # Obtenemos los objetos necesarios
        business_unit = BusinessUnit.objects.get(id=business_unit_id)
        user = User.objects.get(id=user_id)
        person = Person.objects.get(id=person_id)
        
        # Creamos el notificador
        notifier = get_user_notifier()
        
        # Enviamos la notificación según el tipo
        if notification_type == 'registration':
            return async_to_sync(notifier.notify_registration)(user, person)
        elif notification_type == 'login':
            login_method = kwargs.get('login_method', 'default')
            return async_to_sync(notifier.notify_login)(user, person, login_method)
        
        return False
        
    except Exception as e:
        logger.error(f"Error en send_user_notification: {str(e)}")
        return False

@shared_task
def send_placement_notification(
    business_unit_id: int,
    candidate_id: int,
    position: str,
    company: str,
    salary: float,
    start_date: str
) -> bool:
    """
    Tarea para enviar notificaciones de colocación.
    """
    try:
        # Obtenemos los objetos necesarios
        business_unit = BusinessUnit.objects.get(id=business_unit_id)
        candidate = Person.objects.get(id=candidate_id)
        
        # Creamos el notificador
        notifier = placement_notifier(business_unit)
        
        # Convertimos la fecha
        start_date = datetime.fromisoformat(start_date)
        
        # Enviamos la notificación
        return async_to_sync(notifier.notify_executive_placement)(
            candidate=candidate,
            position=position,
            company=company,
            salary=salary,
            start_date=start_date
        )
        
    except Exception as e:
        logger.error(f"Error en send_placement_notification: {str(e)}")
        return False

@shared_task
def send_payment_notification(
    business_unit_id: int,
    recipient_id: int,
    amount: float,
    payment_type: str,
    reference: str
) -> bool:
    """
    Tarea para enviar notificaciones de pago.
    """
    try:
        # Obtenemos los objetos necesarios
        business_unit = BusinessUnit.objects.get(id=business_unit_id)
        recipient = Person.objects.get(id=recipient_id)
        
        # Creamos el notificador
        notifier = payment_notifier(business_unit)
        
        # Enviamos la notificación
        return async_to_sync(notifier.notify_payment_received)(
            recipient=recipient,
            amount=amount,
            payment_type=payment_type,
            reference=reference
        )
        
    except Exception as e:
        logger.error(f"Error en send_payment_notification: {str(e)}")
        return False

@shared_task
def send_process_notification(
    business_unit_id: int,
    recipient_id: int,
    process_type: str,
    process_id: str
) -> bool:
    """
    Tarea para enviar notificaciones de proceso.
    """
    try:
        # Obtenemos los objetos necesarios
        business_unit = BusinessUnit.objects.get(id=business_unit_id)
        recipient = Person.objects.get(id=recipient_id)
        
        # Creamos el notificador
        notifier = process_notifier(business_unit)
        
        # Enviamos la notificación
        return async_to_sync(notifier.notify_process_start)(
            recipient=recipient,
            process_type=process_type,
            process_id=process_id
        )
        
    except Exception as e:
        logger.error(f"Error en send_process_notification: {str(e)}")
        return False

@shared_task
def send_metrics_notification(
    business_unit_id: int,
    recipient_id: int,
    metrics_type: str,
    metrics_data: Dict[str, Any]
) -> bool:
    """
    Tarea para enviar notificaciones de métricas.
    """
    try:
        # Obtenemos los objetos necesarios
        business_unit = BusinessUnit.objects.get(id=business_unit_id)
        recipient = Person.objects.get(id=recipient_id)
        
        # Creamos el notificador
        notifier = metrics_notifier(business_unit)
        
        # Enviamos la notificación
        return async_to_sync(notifier.notify_metrics_update)(
            recipient=recipient,
            metrics_type=metrics_type,
            metrics_data=metrics_data
        )
        
    except Exception as e:
        logger.error(f"Error en send_metrics_notification: {str(e)}")
        return False

@shared_task
def send_event_notification(
    business_unit_id: int,
    recipient_id: int,
    event_name: str,
    event_type: str,
    event_data: Dict[str, Any]
) -> bool:
    """
    Tarea para enviar notificaciones de eventos.
    """
    try:
        # Obtenemos los objetos necesarios
        business_unit = BusinessUnit.objects.get(id=business_unit_id)
        recipient = Person.objects.get(id=recipient_id)
        
        # Creamos el notificador
        notifier = event_notifier(business_unit)
        
        # Enviamos la notificación
        return async_to_sync(notifier.notify_system_event)(
            recipient=recipient,
            event_name=event_name,
            event_type=event_type,
            event_data=event_data
        )
        
    except Exception as e:
        logger.error(f"Error en send_event_notification: {str(e)}")
        return False

@shared_task
def send_alert_notification(
    business_unit_id: int,
    recipient_id: int,
    alert_type: str,
    alert_message: str,
    severity: str
) -> bool:
    """
    Tarea para enviar notificaciones de alertas.
    """
    try:
        # Obtenemos los objetos necesarios
        business_unit = BusinessUnit.objects.get(id=business_unit_id)
        recipient = Person.objects.get(id=recipient_id)
        
        # Creamos el notificador
        notifier = alert_notifier(business_unit)
        
        # Enviamos la notificación
        return async_to_sync(notifier.notify_system_alert)(
            recipient=recipient,
            alert_type=alert_type,
            alert_message=alert_message,
            severity=severity
        )
        
    except Exception as e:
        logger.error(f"Error en send_alert_notification: {str(e)}")
        return False
