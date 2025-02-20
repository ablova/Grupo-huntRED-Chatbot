# /home/pablo/ai_huntred/celery.py
from __future__ import absolute_import, unicode_literals
import os
import logging
from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger("app.tasks")

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')

app = Celery('ai_huntred')

# Base configuration
app.conf.update(
    broker_url='redis://127.0.0.1:6379/0',
    result_backend='redis://127.0.0.1:6379/0',
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',
    timezone='America/Mexico_City',
    enable_utc=True,
)

# Queue definitions
task_queues = {
    'default': {'exchange': 'default', 'routing_key': 'default'},
    'ml': {'exchange': 'ml', 'routing_key': 'ml.#'},
    'scraping': {'exchange': 'scraping', 'routing_key': 'scraping.#'},
    'notifications': {'exchange': 'notifications', 'routing_key': 'notifications.#'},
}

# Task routing
task_routes = {
    'app.tasks.execute_ml_and_scraping': {'queue': 'ml'},
    'app.tasks.ejecutar_scraping': {'queue': 'scraping'},
    'app.tasks.send_whatsapp_message': {'queue': 'notifications'},
    'app.tasks.send_telegram_message': {'queue': 'notifications'},
    'app.tasks.send_messenger_message': {'queue': 'notifications'},
}

# =========================================================
# Configuración de Celery Beat (programación de tareas)
# =========================================================

# Schedule definitions
SCHEDULE_DICT = {
    'execute_ml_and_scraping_daily': {
        'task': 'app.tasks.execute_ml_and_scraping',
        'schedule': crontab(hour=7, minute=30),  # 7:30 AM
    },
    'execute_ml_and_scraping_daily_late': {
        'task': 'app.tasks.execute_ml_and_scraping',
        'schedule': crontab(hour=12, minute=0),  # 12:00 PM
    },
    'send_daily_notification': {
        'task': 'app.tasks.send_daily_notification',
        'schedule': crontab(minute=0, hour='*'),
    },
    'send_consolidated_reports': {
        'task': 'app.tasks.generate_and_send_reports',
        'schedule': crontab(hour=8, minute=40),
    },
    'send_anniversary_reports': {
        'task': 'app.tasks.generate_and_send_anniversary_reports',
        'schedule': crontab(hour=9, minute=0),
    },
    'send_daily_report': {
        'task': 'app.tasks.enviar_reporte_diario',
        'schedule': crontab(hour=23, minute=59),
    },
    'database_cleanup_vacantes': {
        'task': 'app.tasks.limpieza_vacantes',
        'schedule': crontab(day_of_month='1', month_of_year='1,4,7,11', hour=0, minute=0),
    },
    'execute_scraping_daily': {
        'task': 'app.tasks.ejecutar_scraping',
        'schedule': crontab(hour=2, minute=0),
    },
    'verify_scraping_domains_daily': {
        'task': 'app.tasks.verificar_dominios_scraping',
        'schedule': crontab(hour=2, minute=0),
    },
    'train_ml_models_daily': {
        'task': 'app.tasks.train_ml_task',
        'schedule': crontab(hour=3, minute=0),
    },
    'check-emails-every-hour': {
        'task': 'app.tasks.check_emails_and_parse_cvs',
        'schedule': crontab(minute=0, hour='*'),
    },
    'run-email-scraper-morning': {
        'task': 'tasks.execute_email_scraper',
        'schedule': crontab(hour=8, minute=30),
    },
    'run-email-scraper-night': {
        'task': 'tasks.execute_email_scraper',
        'schedule': crontab(hour=22, minute=30),
    },
    'enviar_invitaciones_completar_perfil': {
        'task': 'app.tasks.enviar_invitaciones_completar_perfil',
        'schedule': crontab(minute=0, hour='*/4'),  # Cada 4 horas
    },
}


def setup_periodic_tasks(sender, **kwargs):
    """
    Single source of truth for periodic task registration.
    Used by both beat_schedule and django-celery-beat.
    """
    # Update Celery beat schedule
    sender.conf.beat_schedule = SCHEDULE_DICT
    
    try:
        from django_celery_beat.models import CrontabSchedule, PeriodicTask
        
        # Register tasks in django-celery-beat
        for name, config in SCHEDULE_DICT.items():
            crontab_kwargs = {
                'minute': config['schedule'].minute,
                'hour': config['schedule'].hour,
                'day_of_week': config['schedule'].day_of_week,
                'day_of_month': config['schedule'].day_of_month,
                'month_of_year': config['schedule'].month_of_year,
            }
            
            schedule, _ = CrontabSchedule.objects.get_or_create(**crontab_kwargs)
            PeriodicTask.objects.get_or_create(
                name=name,
                task=config['task'],
                crontab=schedule,
                defaults={'enabled': True}
            )
            logger.info(f"✅ Task registered: {name}")
            
    except Exception as e:
        logger.error(f"❌ Error registering periodic tasks: {e}")

# Connect the setup function
app.on_after_configure.connect(setup_periodic_tasks)

# Set configuration
app.conf.task_queues = task_queues
app.conf.task_routes = task_routes

# Autodiscover tasks
app.autodiscover_tasks()