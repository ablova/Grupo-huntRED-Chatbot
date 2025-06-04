from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def status_color(status):
    """Retorna el color de Bootstrap según el estado de la referencia"""
    colors = {
        'pending': 'warning',
        'completed': 'success',
        'expired': 'danger',
        'converted': 'info'
    }
    return colors.get(status, 'secondary')

@register.filter
def multiply(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_question_text(questions, question_id):
    """Obtiene el texto de una pregunta según su ID"""
    return questions.get(question_id, {}).get('text', question_id) 