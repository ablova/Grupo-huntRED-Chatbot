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

app.conf.beat_schedule = {
    'check_and_renew_whatsapp_token_every_day': {
        'task': 'app.tasks.check_and_renew_whatsapp_token',
        'schedule': crontab(minute=0, hour=0),  # Se ejecuta diariamente a la medianoche
    },
    'check-whatsapp-token-every-day': {
        'task': 'app.tasks.check_and_update_whatsapp_token',
        'schedule': crontab(hour=0, minute=0),  # Ejecuta la tarea todos los días a medianoche
    },
    'clean_old_chat_logs': {
        'task': 'app.tasks.clean_old_chat_logs',
        'schedule': crontab(hour=1, minute=0),  # Ejecuta la tarea todos los días a la 1 AM
    },
    
} 

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

