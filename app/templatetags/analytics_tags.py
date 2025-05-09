from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
@mark_safe
def to_json(value):
    """
    Convierte un objeto Python a JSON.
    
    Args:
        value: Objeto Python
        
    Returns:
        str: Representación JSON del objeto
    """
    return json.dumps(value)

@register.filter
@mark_safe
def format_percentage(value):
    """
    Formatea un número como porcentaje.
    
    Args:
        value: Número decimal
        
    Returns:
        str: Número formateado como porcentaje
    """
    if value is None:
        return "0%"
    return f"{value:.2f}%"

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
