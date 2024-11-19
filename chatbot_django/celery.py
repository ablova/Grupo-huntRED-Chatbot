# /home/amigro/chatbot_django/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Establecer el entorno predeterminado de Django para las configuraciones de Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_django.settings')

app = Celery('chatbot_django')

# Carga las configuraciones de Celery desde el archivo settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-detecta las tareas dentro de los apps instalados
app.autodiscover_tasks()

app.conf.beat_scheduler = 'django_celery_beat.schedulers.DatabaseScheduler'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
