# Ubicación del archivo: /home/amigro/chatbot_django/celery.py
# Configuración de Celery para chatbot_django.

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Establece el entorno predeterminado para Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_django.settings')

app = Celery('chatbot_django')

# Cargar configuraciones desde settings.py usando el prefijo "CELERY_"
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodetectar tareas definidas en apps instaladas
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')