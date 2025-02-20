# /home/pablo/ai_huntred/celery.py
from __future__ import absolute_import, unicode_literals
import os
import logging
from celery import Celery
from celery.schedules import crontab  # Importación necesaria

logger = logging.getLogger("app.tasks")

# Establece el entorno predeterminado para Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')

app = Celery('ai_huntred')

# Configuración de broker y backend (Redis)
app.conf.update(
    broker_url='redis://127.0.0.1:6379/0',
    result_backend='redis://127.0.0.1:6379/0',
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',
    timezone='America/Mexico_City',
    enable_utc=True,
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# =========================================================
# Configuración de Celery Beat (programación de tareas)
# =========================================================

app.conf.beat_schedule.update({
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
})

# Definición de colas
app.conf.task_queues = {
    'default': {'exchange': 'default', 'routing_key': 'default'},
    'ml': {'exchange': 'ml', 'routing_key': 'ml.#'},
    'scraping': {'exchange': 'scraping', 'routing_key': 'scraping.#'},
    'notifications': {'exchange': 'notifications', 'routing_key': 'notifications.#'},
}

# Rutas de tareas a colas específicas
app.conf.task_routes = {
    'app.tasks.execute_ml_and_scraping': {'queue': 'ml'},
    'app.tasks.ejecutar_scraping': {'queue': 'scraping'},
    'app.tasks.send_whatsapp_message': {'queue': 'notifications'},
    'app.tasks.send_telegram_message': {'queue': 'notifications'},
    'app.tasks.send_messenger_message': {'queue': 'notifications'},
}

# Autodiscover tasks
app.autodiscover_tasks()

def register_periodic_tasks():
    """
    Registra tareas periódicas usando django-celery-beat.
    """
    from django_celery_beat.models import CrontabSchedule, PeriodicTask
    logger.info("🔄 Registrando tareas periódicas...")
    tasks = [
        {"name": "Execute ML and Scraping Daily", "task": "app.tasks.execute_ml_and_scraping", "crontab": {"hour": 7, "minute": 30}},
        {"name": "Send Daily Notifications", "task": "app.tasks.send_daily_notification", "crontab": {"hour": "*", "minute": 0}},
        {"name": "Train ML Models Daily", "task": "app.tasks.train_ml_task", "crontab": {"hour": 3, "minute": 0}},
        {"name": "Ejecutar Scraping Diario", "task": "app.tasks.ejecutar_scraping", "crontab": {"hour": 2, "minute": 0}},
        {"name": "Verify Scraping Domains Daily", "task": "app.tasks.verificar_dominios_scraping", "crontab": {"hour": 2, "minute": 30}},
        {"name": "Clean Vacantes Database", "task": "app.tasks.limpieza_vacantes", "crontab": {"day_of_month": "1", "month_of_year": "1,4,7,11", "hour": 0, "minute": 0}},
        {"name": "Send Consolidated Reports", "task": "app.tasks.generate_and_send_reports", "crontab": {"hour": 8, "minute": 40}},
        {"name": "Check Emails and Parse CVs Morning", "task": "app.tasks.check_emails_and_parse_cvs", "crontab": {"hour": 9, "minute": 0}},
        {"name": "Check Emails and Parse CVs Afternoon", "task": "app.tasks.check_emails_and_parse_cvs", "crontab": {"hour": 14, "minute": 0}},
    ]
    for task_info in tasks:
        try:
            schedule, _ = CrontabSchedule.objects.get_or_create(**task_info["crontab"])
            PeriodicTask.objects.get_or_create(
                crontab=schedule,
                name=task_info["name"],
                task=task_info["task"],
                defaults={'enabled': True}
            )
            logger.info(f"✅ Tarea registrada: {task_info['name']}")
        except Exception as e:
            logger.error(f"❌ Error registrando tarea {task_info['name']}: {e}")

# Comentamos la llamada directa para evitar problemas al iniciar migraciones
# register_periodic_tasks()