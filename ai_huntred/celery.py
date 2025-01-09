# /home/pablollh/ai_huntred/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Establece el entorno predeterminado para Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')

app = Celery('ai_huntred')

# Cambiar el broker a Redis
app.conf.update(
    broker_url='redis://127.0.0.1:6379/0',  # Usar Redis como broker
    result_backend='redis://127.0.0.1:6379/0',  # Redis también como backend de resultados
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',
    timezone='America/Mexico_City',
    enable_utc=True,
)

# Autodetectar tareas definidas en apps instaladas
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')