from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')

app = Celery('ai_huntred')

# Configuración base de Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configuración específica
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Mexico_City',
    enable_utc=True,
    broker_transport_options={'visibility_timeout': 3600},  # 1 hora
    worker_prefetch_multiplier=1,  # Mejor rendimiento para tareas largas
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    beat_schedule={
        'check_vacancies_status': {
            'task': 'app.tasks.check_vacancies_status',
            'schedule': crontab(minute='*/15'),  # Cada 15 minutos
        },
        'process_pending_applications': {
            'task': 'app.tasks.process_pending_applications',
            'schedule': crontab(minute='*/5'),  # Cada 5 minutos
        },
        'update_user_profiles': {
            'task': 'app.tasks.update_user_profiles',
            'schedule': crontab(hour='*/1'),  # Cada hora
        },
    },
    task_queues={
        'default': {'exchange': 'default', 'routing_key': 'default'},
        'ml': {'exchange': 'ml', 'routing_key': 'ml.#'},
        'scraping': {'exchange': 'scraping', 'routing_key': 'scraping.#'},
        'notifications': {'exchange': 'notifications', 'routing_key': 'notifications.#'},
    },
    task_routes={
        'app.tasks.execute_ml_and_scraping': {'queue': 'ml'},
        'app.tasks.ejecutar_scraping': {'queue': 'scraping'},
        'app.tasks.send_whatsapp_message': {'queue': 'notifications'},
        'app.tasks.send_telegram_message': {'queue': 'notifications'},
        'app.tasks.send_messenger_message': {'queue': 'notifications'},
    },
)

# Configuración de Redis como backend
app.conf.update(
    result_backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}',
    broker_url=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}',
)

# Configuración de monitoreo
app.conf.update(
    task_send_sent_event=True,
    task_track_started=True,
    worker_send_task_events=True,
    task_ignore_result=False,
    result_expires=3600,  # 1 hora
)

# Configuración de rendimiento
app.conf.update(
    worker_max_tasks_per_child=100,
    worker_max_memory_per_child=300,  # 300MB
    broker_pool_limit=None,
    broker_heartbeat=30,
    broker_connection_timeout=30,
)

# Configuración de seguridad
app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)

# Configuración de retry
app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_retry_backoff=True,
    task_retry_backoff_max=600,  # 10 minutos
    task_retry_jitter=True,
)
