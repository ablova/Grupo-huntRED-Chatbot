from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
@mark_safe
def format_pricing_details(pricing_details):
    """
    Formatea los detalles del pricing para mostrar en el template.
    
    Args:
        pricing_details: Detalles del pricing
        
    Returns:
        str: Detalles formateados
    """
    try:
        details = json.loads(pricing_details)
        return mark_safe(json.dumps(details, indent=2))
    except (json.JSONDecodeError, TypeError):
        return pricing_details

@register.filter
@mark_safe
def format_currency(value):
    """
    Formatea un número como moneda.
    
    Args:
        value: Número decimal
        
    Returns:
        str: Número formateado como moneda
    """
    if value is None:
        return "$0.00"
    return f"${value:,.2f}"

@register.filter
@mark_safe
def format_date(value):
    """
    Formatea una fecha.
    
    Args:
        value: Objeto datetime
        
    Returns:
        str: Fecha formateada
    """
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d")

@register.filter
@mark_safe
def format_status(value):
    """
    Formatea el estado de la propuesta.
    
    Args:
        value: Estado de la propuesta
        
    Returns:
        str: Estado formateado
    """
    statuses = {
        'PENDING': 'Pendiente',
        'SENT': 'Enviada',
        'CONVERTED': 'Convertida',
        'REJECTED': 'Rechazada'
    }
    return statuses.get(value, value)
