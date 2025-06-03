"""
Utilidades para el sistema de notificaciones.

Proporciona funciones auxiliares para trabajar con notificaciones,
validación de datos y utilidades para integraciones con otros módulos.
"""

import uuid
import logging
import hashlib
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.db.models import Q

from app.models import Person, BusinessUnit, Vacante, User, Company, Notification, NotificationType, NotificationStatus, NotificationChannel, NotificationPreference

logger = logging.getLogger('notifications')

def generate_verification_code(length: int = 8) -> str:
    """
    Genera un código de verificación aleatorio.
    
    Args:
        length: Longitud del código
    
    Returns:
        Código de verificación
    """
    # Generamos un UUID y tomamos los primeros caracteres
    return str(uuid.uuid4()).replace('-', '')[:length].upper()

def generate_whatsapp_verification_link(
    phone_number: str, 
    code: str, 
    purpose: str = "verificacion", 
    vacante_id: Optional[int] = None
) -> str:
    """
    Genera un enlace de WhatsApp con código de verificación.
    
    Args:
        phone_number: Número de teléfono de WhatsApp (formato internacional sin +)
        code: Código de verificación a incluir
        purpose: Propósito del enlace (verificación, pago, etc.)
        vacante_id: ID de la vacante relacionada (opcional)
    
    Returns:
        URL completa para abrir WhatsApp con mensaje predefinido
    """
    # Formateamos el mensaje según el propósito
    if purpose.lower() == "pago":
        message = f"Confirmo el pago de la factura. Código: {code}"
        if vacante_id:
            message += f" Vacante ID: {vacante_id}"
    elif purpose.lower() == "firma":
        message = f"Confirmo la firma del contrato. Código: {code}"
        if vacante_id:
            message += f" Vacante ID: {vacante_id}"
    else:  # Verificación general
        message = f"Código de verificación: {code}"
    
    # Codificamos el mensaje para URL
    import urllib.parse
    encoded_message = urllib.parse.quote(message)
    
    # Construimos la URL de WhatsApp
    return f"https://wa.me/{phone_number}?text={encoded_message}"

def get_notification_preferences(user: User, notification_type: str, business_unit: Optional[BusinessUnit] = None) -> Dict[str, bool]:
    """
    Obtiene las preferencias de notificación para un usuario.
    
    Args:
        user: Usuario para el que obtener preferencias
        notification_type: Tipo de notificación
        business_unit: Unidad de negocio (opcional)
    
    Returns:
        Diccionario con canales habilitados
    """
    # Intentamos obtener la preferencia específica
    try:
        if business_unit:
            pref = NotificationPreference.objects.get(
                user=user,
                notification_type=notification_type,
                business_unit=business_unit
            )
        else:
            pref = NotificationPreference.objects.get(
                user=user,
                notification_type=notification_type,
                business_unit__isnull=True
            )
        
        # Devolvemos los canales habilitados
        return {
            NotificationChannel.EMAIL: pref.email_enabled,
            NotificationChannel.WHATSAPP: pref.whatsapp_enabled,
            NotificationChannel.SMS: pref.sms_enabled,
            NotificationChannel.TELEGRAM: pref.telegram_enabled,
            NotificationChannel.APP: pref.app_enabled,
            NotificationChannel.SLACK: pref.slack_enabled,
        }
        
    except NotificationPreference.DoesNotExist:
        # Si no hay preferencia específica, devolvemos los valores por defecto
        return {
            NotificationChannel.EMAIL: True,
            NotificationChannel.WHATSAPP: True,
            NotificationChannel.SMS: False,
            NotificationChannel.TELEGRAM: False,
            NotificationChannel.APP: True,
            NotificationChannel.SLACK: False,
        }

def get_enabled_channels(user: User, notification_type: str, business_unit: Optional[BusinessUnit] = None) -> List[str]:
    """
    Obtiene una lista de canales habilitados para un usuario.
    
    Args:
        user: Usuario para el que obtener preferencias
        notification_type: Tipo de notificación
        business_unit: Unidad de negocio (opcional)
    
    Returns:
        Lista de canales habilitados
    """
    prefs = get_notification_preferences(user, notification_type, business_unit)
    return [channel for channel, enabled in prefs.items() if enabled]

def get_notification_recipients_for_vacante(vacante: Vacante, role: str) -> List[Person]:
    """
    Obtiene los destinatarios de notificaciones según el rol y la vacante.
    
    Args:
        vacante: Vacante para la que obtener destinatarios
        role: Rol para el que obtener destinatarios (responsable_proceso, 
              contacto_cliente, consultor, etc.)
    
    Returns:
        Lista de personas que deben recibir la notificación
    """
    recipients = []
    
    if role == 'responsable_proceso':
        # Responsable directo del proceso
        if hasattr(vacante, 'responsable') and vacante.responsable:
            recipients.append(vacante.responsable)
    
    elif role == 'contacto_cliente':
        # Contacto principal en el cliente
        if hasattr(vacante, 'empresa') and hasattr(vacante.empresa, 'contacto_principal'):
            recipients.append(vacante.empresa.contacto_principal)
    
    elif role == 'contacto_facturacion':
        # Contacto de facturación en el cliente
        if hasattr(vacante, 'empresa') and hasattr(vacante.empresa, 'contacto_facturacion'):
            recipients.append(vacante.empresa.contacto_facturacion)
    
    elif role == 'consultor_asignado':
        # Consultor asignado al proceso
        if hasattr(vacante, 'consultor') and vacante.consultor:
            recipients.append(vacante.consultor)
    
    elif role == 'candidatos':
        # Todos los candidatos activos en el proceso
        if hasattr(vacante, 'get_active_candidates'):
            candidates = vacante.get_active_candidates()
            recipients.extend(candidates)
    
    elif role == 'equipo_completo':
        # Todos los involucrados en el proceso
        recipients = []
        
        # Responsable
        if hasattr(vacante, 'responsable') and vacante.responsable:
            recipients.append(vacante.responsable)
        
        # Consultor
        if hasattr(vacante, 'consultor') and vacante.consultor:
            recipients.append(vacante.consultor)
        
        # Contactos en cliente
        if hasattr(vacante, 'empresa'):
            if hasattr(vacante.empresa, 'contacto_principal'):
                recipients.append(vacante.empresa.contacto_principal)
            if hasattr(vacante.empresa, 'contacto_facturacion'):
                recipients.append(vacante.empresa.contacto_facturacion)
    
    # Eliminamos duplicados si hay alguno
    return list(set(recipients))

def get_notification_stats(business_unit: Optional[BusinessUnit] = None, days: int = 30) -> Dict[str, Any]:
    """
    Obtiene estadísticas sobre las notificaciones enviadas.
    
    Args:
        business_unit: Unidad de negocio para filtrar (opcional)
        days: Número de días para calcular estadísticas
    
    Returns:
        Diccionario con estadísticas de notificaciones
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Base query
    query = Q(created_at__gte=cutoff_date)
    
    if business_unit:
        query &= Q(business_unit=business_unit)
    
    # Totales por estado
    total = Notification.objects.filter(query).count()
    sent = Notification.objects.filter(query & Q(status=NotificationStatus.SENT)).count()
    delivered = Notification.objects.filter(query & Q(status=NotificationStatus.DELIVERED)).count()
    read = Notification.objects.filter(query & Q(status=NotificationStatus.READ)).count()
    failed = Notification.objects.filter(query & Q(status=NotificationStatus.FAILED)).count()
    
    # Totales por tipo
    by_type = {}
    for nt_choice in NotificationType.choices:
        nt_key = nt_choice[0]
        by_type[nt_key] = Notification.objects.filter(query & Q(notification_type=nt_key)).count()
    
    # Estadísticas por día
    daily_stats = []
    for i in range(days):
        day_date = timezone.now() - timedelta(days=i)
        day_start = day_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        day_query = query & Q(created_at__gte=day_start) & Q(created_at__lte=day_end)
        day_total = Notification.objects.filter(day_query).count()
        
        daily_stats.append({
            'date': day_date.date().isoformat(),
            'total': day_total
        })
    
    return {
        'total': total,
        'sent': sent,
        'delivered': delivered,
        'read': read,
        'failed': failed,
        'delivery_rate': (delivered / sent * 100) if sent > 0 else 0,
        'read_rate': (read / delivered * 100) if delivered > 0 else 0,
        'by_type': by_type,
        'daily_stats': daily_stats
    }
