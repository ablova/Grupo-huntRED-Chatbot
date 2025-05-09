# /Users/pablollh/MEGA/GitHub/Grupo-huntRED-Chatbot/ai_huntred/celery_app.py
#
# Configuración de Celery para el proyecto AI HuntRED.
# Define colas, rutas y tareas periódicas para el procesamiento asíncrono.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

from __future__ import absolute_import, unicode_literals
import os
import sys
import django
import logging
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_ready
from django.db.utils import OperationalError
from django.apps import apps

logger = logging.getLogger("app.tasks")

if not any(arg in sys.argv for arg in ['migrate', 'makemigrations', 'collectstatic']):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')
    django.setup()

app = Celery('ai_huntred')

app.conf.update(
    broker_url='redis://127.0.0.1:6379/0',
    result_backend='redis://127.0.0.1:6379/0',
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',
    timezone='America/Mexico_City',
    enable_utc=False,
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

task_queues = {
    'default': {'exchange': 'default', 'routing_key': 'default'},
    'ml': {'exchange': 'ml', 'routing_key': 'ml.#'},
    'scraping': {'exchange': 'scraping', 'routing_key': 'scraping.#'},
    'notifications': {'exchange': 'notifications', 'routing_key': 'notifications.#'},
}

task_routes = {
    'app.tasks.execute_ml_and_scraping': {'queue': 'ml'},
    'app.tasks.ejecutar_scraping': {'queue': 'scraping'},
    'app.tasks.send_whatsapp_message': {'queue': 'notifications'},
    'app.tasks.send_telegram_message': {'queue': 'notifications'},
    'app.tasks.send_messenger_message': {'queue': 'notifications'},
    'app.tasks.*': {'queue': 'default'},
}

app.conf.task_queues = task_queues
app.conf.task_routes = task_routes

SCHEDULE_DICT = {
    'Ejecutar ML y Scraping (mañana)': {
        'task': 'app.tasks.execute_ml_and_scraping',
        'schedule': crontab(hour=7, minute=30),
    },
    'Ejecutar ML y Scraping (mediodía)': {
        'task': 'app.tasks.execute_ml_and_scraping',
        'schedule': crontab(hour=12, minute=15),
    },
    'Enviar notificaciones diarias': {
        'task': 'app.tasks.send_daily_notification',
        'schedule': crontab(minute=15, hour='*/2'),
    },
    'Generar y enviar reportes consolidados': {
        'task': 'app.tasks.generate_and_send_reports',
        'schedule': crontab(hour=8, minute=40),
    },
    'Generar y enviar reportes de aniversario': {
        'task': 'app.tasks.generate_and_send_anniversary_reports',
        'schedule': crontab(hour=9, minute=10),
    },
    'Enviar reporte diario completo': {
        'task': 'app.tasks.enviar_reporte_diario',
        'schedule': crontab(hour=23, minute=45),
    },
    'Limpieza trimestral de vacantes antiguas': {
        'task': 'app.tasks.limpieza_vacantes',
        'schedule': crontab(day_of_month='1', month_of_year='1,4,7,11', hour=1, minute=30),
    },
    'Ejecución diaria de scraping': {
        'task': 'app.tasks.ejecutar_scraping',
        'schedule': crontab(hour=2, minute=30),
    },
    'Verificación diaria de dominios de scraping': {
        'task': 'app.tasks.verificar_dominios_scraping',
        'schedule': crontab(hour=3, minute=30),
    },
    'Entrenamiento diario de modelos ML': {
        'task': 'app.tasks.train_ml_task',
        'schedule': crontab(hour=4, minute=0),
    },
    'Revisión de emails cada 2 horas': {
        'task': 'app.tasks.check_emails_and_parse_cvs',
        'schedule': crontab(minute=30, hour='*/2'),
    },
    'Scraping de emails (mañana)': {
        'task': 'tasks.execute_email_scraper',
        'schedule': crontab(hour=8, minute=45),
    },
    'Scraping de emails (noche)': {
        'task': 'tasks.execute_email_scraper',
        'schedule': crontab(hour=22, minute=45),
    },
    'Invitaciones para completar perfil': {
        'task': 'app.tasks.enviar_invitaciones_completar_perfil',
        'schedule': crontab(minute=45, hour='*/6'),
    },
    'Procesar perfiles a profundidad de reciente creacion': {
        'task': 'app.tasks.process_batch_task',
        'schedule': crontab(minute=0, hour=2, day_of_week='1,3,5'),
    },
    'Syncronizar Oportunidades Diario': {
        'task': 'app.tasks.sync_jobs_with_api',
        'schedule': crontab(minute=0, hour=5),
    },
}

@worker_ready.connect
def setup_periodic_tasks(sender, **kwargs):
    if any(arg in sys.argv for arg in ['makemigrations', 'migrate', 'collectstatic', 'shell']):
        logger.info("Skipping periodic task setup for admin commands.")
        return

    import time
    max_attempts = 4
    for attempt in range(max_attempts):
        try:
            if apps.apps_ready and apps.models_ready and apps.ready:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                logger.info("Django app registry and database are fully ready")
                break
            logger.warning(f"⏳ Django not ready on attempt {attempt+1}")
            time.sleep(20)
        except Exception as e:
            logger.warning(f"⚠️ Error checking Django readiness on attempt {attempt+1}: {e}")
            time.sleep(20)
    
    if not (apps.apps_ready and apps.models_ready and apps.ready):
        logger.error("❌ Django still not ready after retries.")
        return
    
    app.conf.beat_schedule = SCHEDULE_DICT
    
    for attempt in range(max_attempts):
        try:
            from django_celery_beat.models import CrontabSchedule, PeriodicTask
            from django.db import transaction
            with transaction.atomic():
                for name, config in SCHEDULE_DICT.items():
                    schedule, _ = CrontabSchedule.objects.get_or_create(
                        minute=config["schedule"].minute,
                        hour=config["schedule"].hour,
                        day_of_week=config["schedule"].day_of_week,
                        day_of_month=config["schedule"].day_of_month,
                        month_of_year=config["schedule"].month_of_year,
                    )
                    task_defaults = {"crontab": schedule, "enabled": True}
                    if "args" in config:
                        task_defaults["args"] = config["args"]
                    if "kwargs" in config:
                        task_defaults["kwargs"] = config["kwargs"]
                    PeriodicTask.objects.update_or_create(
                        name=name,
                        task=config["task"],
                        defaults=task_defaults,
                    )
                logger.info(f"✅ Successfully registered {len(SCHEDULE_DICT)} periodic tasks")
                break
        except OperationalError as e:
            logger.warning(f"⚠️ Database not available on attempt {attempt+1}/{max_attempts}: {e}")
            if attempt < max_attempts - 1:
                time.sleep(20)
        except Exception as e:
            logger.error(f"❌ Error registering periodic tasks: {str(e)}")
            break

app.on_after_configure.connect(setup_periodic_tasks)
app.autodiscover_tasks()