from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filtro personalizado para acceder a elementos de diccionario en templates.
    Uso: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key) 