# Ubicación del archivo: /home/pablollh/ai_huntred/celery.py
# Configuración de Celery para ai_huntred.

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Establece el entorno predeterminado para Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')

app = Celery('ai_huntred')

# Cargar configuraciones desde settings.py usando el prefijo "CELERY_"
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodetectar tareas definidas en apps instaladas
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')