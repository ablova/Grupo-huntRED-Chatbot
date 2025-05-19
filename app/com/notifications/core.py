"""
Funciones core del sistema de notificaciones.

Proporciona las funciones principales para enviar y programar notificaciones,
así como para gestionar su ciclo de vida.
"""

import uuid
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from asgiref.sync import sync_to_async

from app.models import Person, BusinessUnit, Vacante, User, Notification, NotificationType, NotificationStatus, NotificationChannel, NotificationPreference
from app.com.notifications.handlershandlers import (
    NotificationHandler, EmailNotificationHandler, WhatsAppNotificationHandler,
    SMSNotificationHandler, TelegramNotificationHandler, AppNotificationHandler,
    SlackNotificationHandler
)
from app.com.notifications.handlerstemplates import get_notification_template

logger = logging.getLogger('notifications')

def _get_handlers_for_recipient(recipient: Person, notification_type: str, business_unit: BusinessUnit) -> Dict[str, NotificationHandler]:
    """
    Obtiene los manejadores de notificación apropiados para el destinatario
    basándose en sus preferencias.
    """
    # Si el destinatario es un usuario del sistema, consultamos sus preferencias
    handlers = {}
    
    # Por defecto, usamos email y WhatsApp
    handlers[NotificationChannel.EMAIL] = EmailNotificationHandler(business_unit)
    handlers[NotificationChannel.WHATSAPP] = WhatsAppNotificationHandler(business_unit)
    
    # Si el destinatario tiene un usuario asociado, verificamos sus preferencias
    user = getattr(recipient, 'user', None)
    if not user:
        return handlers
    
    try:
        # Obtenemos las preferencias para este tipo de notificación y unidad de negocio
        pref = NotificationPreference.objects.get(
            user=user,
            notification_type=notification_type,
            business_unit=business_unit
        )
        
        # Solo incluimos los canales habilitados
        handlers = {}
        if pref.email_enabled:
            handlers[NotificationChannel.EMAIL] = EmailNotificationHandler(business_unit)
        if pref.whatsapp_enabled:
            handlers[NotificationChannel.WHATSAPP] = WhatsAppNotificationHandler(business_unit)
        if pref.sms_enabled:
            handlers[NotificationChannel.SMS] = SMSNotificationHandler(business_unit)
        if pref.telegram_enabled:
            handlers[NotificationChannel.TELEGRAM] = TelegramNotificationHandler(business_unit)
        if pref.app_enabled:
            handlers[NotificationChannel.APP] = AppNotificationHandler(business_unit)
        if pref.slack_enabled:
            handlers[NotificationChannel.SLACK] = SlackNotificationHandler(business_unit)
            
    except NotificationPreference.DoesNotExist:
        # Si no hay preferencias específicas, mantenemos los canales por defecto
        pass
    
    return handlers

async def send_notification(
    notification_type: str,
    recipient: Person,
    business_unit: BusinessUnit,
    title: str = None,
    content: str = None,
    context: Dict[str, Any] = None,
    sender: User = None,
    vacante: Vacante = None,
    channels: List[str] = None,
    include_verification: bool = False,
    template_name: str = None,
) -> Notification:
    """
    Envía una notificación a un destinatario a través de los canales especificados.
    
    Args:
        notification_type: Tipo de notificación (de NotificationType)
        recipient: Persona que recibirá la notificación
        business_unit: Unidad de negocio relacionada con la notificación
        title: Título de la notificación (opcional, si se usa plantilla)
        content: Contenido de la notificación (opcional, si se usa plantilla)
        context: Contexto para renderizar la plantilla de notificación
        sender: Usuario que envía la notificación
        vacante: Vacante relacionada con la notificación (opcional)
        channels: Lista de canales por los que enviar (si None, usa preferencias)
        include_verification: Si incluir un código de verificación
        template_name: Nombre de la plantilla a usar (si None, usa automática)
    
    Returns:
        La notificación creada
    """
    # Generamos el contenido usando plantillas si es necesario
    if not title or not content:
        if not template_name:
            template_name = notification_type
        
        # Si no hay contexto, creamos uno vacío
        context = context or {}
        
        # Añadimos datos comunes al contexto
        context.update({
            'recipient': recipient,
            'business_unit': business_unit,
            'vacante': vacante,
            'sender': sender,
        })
        
        # Obtenemos la plantilla y renderizamos
        template_result = await sync_to_async(get_notification_template)(
            template_name, 
            recipient=recipient,
            business_unit=business_unit,
            context=context
        )
        
        title = title or template_result.get('title', f"Notificación de {business_unit.name}")
        content = content or template_result.get('content', "")
    
    # Generamos un código de verificación si es necesario
    verification_code = None
    if include_verification:
        verification_code = str(uuid.uuid4())[:8].upper()
    
    # Creamos la notificación en la base de datos
    notification = await sync_to_async(Notification.objects.create)(
        title=title,
        content=content,
        notification_type=notification_type,
        recipient=recipient,
        business_unit=business_unit,
        sender=sender,
        vacante=vacante,
        verification_code=verification_code,
        status=NotificationStatus.PENDING
    )
    
    # Determinamos los canales a usar
    if not channels:
        handlers = _get_handlers_for_recipient(recipient, notification_type, business_unit)
    else:
        handlers = {}
        for channel in channels:
            if channel == NotificationChannel.EMAIL:
                handlers[channel] = EmailNotificationHandler(business_unit)
            elif channel == NotificationChannel.WHATSAPP:
                handlers[channel] = WhatsAppNotificationHandler(business_unit)
            elif channel == NotificationChannel.SMS:
                handlers[channel] = SMSNotificationHandler(business_unit)
            elif channel == NotificationChannel.TELEGRAM:
                handlers[channel] = TelegramNotificationHandler(business_unit)
            elif channel == NotificationChannel.APP:
                handlers[channel] = AppNotificationHandler(business_unit)
            elif channel == NotificationChannel.SLACK:
                handlers[channel] = SlackNotificationHandler(business_unit)
    
    # Enviamos la notificación por cada canal
    tasks = []
    for channel, handler in handlers.items():
        tasks.append(handler.send(notification))
    
    # Esperamos a que todas las notificaciones se envíen
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verificamos si al menos uno de los canales tuvo éxito
        success = any(result is True for result in results if not isinstance(result, Exception))
        
        # Si ningún canal tuvo éxito, marcamos la notificación como fallida
        if not success:
            await sync_to_async(notification.mark_as_failed)("Ningún canal de notificación tuvo éxito")
    
    return notification

def schedule_notification(
    notification_type: str,
    recipient: Person,
    business_unit: BusinessUnit,
    scheduled_time: datetime,
    title: str = None,
    content: str = None,
    context: Dict[str, Any] = None,
    sender: User = None,
    vacante: Vacante = None,
    channels: List[str] = None,
    include_verification: bool = False,
    template_name: str = None,
) -> Notification:
    """
    Programa una notificación para ser enviada en un momento futuro.
    
    Args:
        Los mismos que send_notification, más:
        scheduled_time: Fecha y hora para enviar la notificación
    
    Returns:
        La notificación programada
    """
    # Obtenemos el contenido de la plantilla si es necesario
    if not title or not content:
        if not template_name:
            template_name = notification_type
        
        # Si no hay contexto, creamos uno vacío
        context = context or {}
        
        # Añadimos datos comunes al contexto
        context.update({
            'recipient': recipient,
            'business_unit': business_unit,
            'vacante': vacante,
            'sender': sender,
        })
        
        # Obtenemos la plantilla y renderizamos
        template_result = get_notification_template(
            template_name, 
            recipient=recipient,
            business_unit=business_unit,
            context=context
        )
        
        title = title or template_result.get('title', f"Notificación de {business_unit.name}")
        content = content or template_result.get('content', "")
    
    # Generamos un código de verificación si es necesario
    verification_code = None
    if include_verification:
        verification_code = str(uuid.uuid4())[:8].upper()
    
    # Creamos la notificación programada
    with transaction.atomic():
        notification = Notification.objects.create(
            title=title,
            content=content,
            notification_type=notification_type,
            recipient=recipient,
            business_unit=business_unit,
            sender=sender,
            vacante=vacante,
            verification_code=verification_code,
            status=NotificationStatus.PENDING,
            scheduled_for=scheduled_time
        )
        
        # Aquí podríamos programar la tarea en Celery o similar
        # from app.tasks import send_scheduled_notification
        # send_scheduled_notification.apply_async(
        #     args=[notification.id],
        #     eta=scheduled_time
        # )
        
        logger.info(f"Notificación {notification.id} programada para {scheduled_time}")
        
    return notification

def verify_notification_code(code: str) -> Optional[Notification]:
    """
    Verifica un código de notificación y marca la notificación como verificada
    si el código es válido.
    
    Args:
        code: El código de verificación a verificar
    
    Returns:
        La notificación verificada o None si el código no es válido
    """
    try:
        notification = Notification.objects.get(
            verification_code=code,
            is_verified=False,
            status__in=[NotificationStatus.SENT, NotificationStatus.DELIVERED, NotificationStatus.READ]
        )
        
        notification.is_verified = True
        notification.save(update_fields=['is_verified'])
        
        return notification
    except Notification.DoesNotExist:
        return None
