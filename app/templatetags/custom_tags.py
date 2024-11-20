# /home/amigro/app/templatetags/custom_tags.py

from django import template

register = template.Library()

@register.filter
def pluck(objects, key):
    return [obj[key] for obj in objects]