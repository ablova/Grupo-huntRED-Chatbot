# Ubicación del archivo: /home/pablo/ai_huntred/__init__.py
# Inicialización de tareas para la aplicación ai_huntred.

from __future__ import absolute_import, unicode_literals

# Importa Celery para detectar tareas
from .celery_app import app as celery_app  # Cambia a importar desde celery_app.py

__all__ = ('celery_app',)