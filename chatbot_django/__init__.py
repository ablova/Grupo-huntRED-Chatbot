# Ubicación del archivo: /home/pablollh/chatbot_django/tasks/__init__.py
# Inicialización de tareas para la aplicación chatbot_django.

from __future__ import absolute_import, unicode_literals

# Importa Celery para detectar tareas
from .celery import app as celery_app

__all__ = ('celery_app',)