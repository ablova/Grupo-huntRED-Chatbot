from __future__ import absolute_import, unicode_literals
import os
import django
import logging
from celery import Celery
from celery.schedules import crontab
from celery.signals import after_setup_task_logger, worker_ready
from django.db.utils import OperationalError
import tensorflow as tf

logger = logging.getLogger("app.tasks")

# Set Django settings if not already set
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')
    django.setup()

app = Celery('ai_huntred')


#Evitar que Tensorflow truene el sistema - CPU
# Evitar que TensorFlow intente usar GPUs si no hay
tf.config.set_visible_devices([], 'GPU')

# Verifica si hay GPUs y configura sus límites si están presentes
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        tf.config.experimental.set_memory_growth(gpus[0], True)
        tf.config.set_logical_device_configuration(
            gpus[0],
            [tf.config.LogicalDeviceConfiguration(memory_limit=1000)]  # Limitar GPU a 1GB
        )
        logger.info(f"✅ GPU detectada. Limitada a 1GB RAM.")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo configurar la memoria de la GPU: {str(e)}")
else:
    logger.warning("⚠️ No GPU detectada. TensorFlow correrá en CPU.")

# La configuración de hilos se manejará dinámicamente en ml_opt.py

# Configuración segura para CPUs LO DEJO PERO NO JALA
#cpus = tf.config.experimental.list_physical_devices('CPU')
#if cpus:
#    tf.config.set_logical_device_configuration(
#        cpus[0],
#        [tf.config.LogicalDeviceConfiguration(memory_limit=500)]  # Limita a 500MB RAM
#    )
#    logger.info(f"✅ TensorFlow configurado en CPU con 500MB de RAM.")


# Initialize task annotations dictionary
app.conf.task_annotations = {}

# Improved broker and backend configuration with connection pool settings
app.conf.update(
    broker_url='redis://127.0.0.1:6379/0',
    result_backend='redis://127.0.0.1:6379/0',
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',
    timezone='America/Mexico_City',
    enable_utc=False,  # Use local timezone
    
    # Connection management - prevent connection issues
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    broker_pool_limit=10,  # Increased from 1 to allow more connections
    broker_heartbeat=10,  # Add heartbeat to detect connection issues
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_remote_tracebacks=True,  # Enable detailed error tracing
    result_expires=3600,  # 1 hour
    
    # Memory optimization
    worker_max_memory_per_child=80000,  # Reduced from 200MB to 80MB
    worker_max_tasks_per_child=2,  # Reduced from 5 to 3 tasks before worker restart
    worker_concurrency=1,
    worker_prefetch_multiplier=1,
    
    # Task time constraints
    task_time_limit=600,  # Increased to 10 minutes
    task_soft_time_limit=540,  # 9 minutes - gives workers time to clean up
    
    # Add visibility settings for tasks
    task_track_started=True,
    task_send_sent_event=True,
)


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# =========================================================
# Queue and routing definitions
# =========================================================

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
    # Add explicit routing for all other tasks
    'app.tasks.*': {'queue': 'default'},
}

app.conf.task_queues = task_queues
app.conf.task_routes = task_routes

# =========================================================
# Beat schedule definition with better distribution
# =========================================================

# =========================================================
# Beat schedule definition with better distribution and more descriptive names
# =========================================================

SCHEDULE_DICT = {
    # Staggered the execution times to avoid concurrent resource usage
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
}

# =========================================================
# Improved periodic task registration with better error handling
# =========================================================

@worker_ready.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Register periodic tasks only when Celery is ready and Django apps are loaded.
    Includes better error handling and retry logic.
    """
    from django.apps import apps
    import time
    
    # Check Django readiness up to 3 times with a delay
    for attempt in range(2):
        if apps.ready:
            break
            
        logger.warning(f"⏳ Django not ready on attempt {attempt+1}. Waiting...")
        time.sleep(8)
    
    if not apps.ready:
        logger.error("❌ Django still not ready after retries. Scheduling will be handled by beat service.")
        return
    
    sender.conf.beat_schedule = SCHEDULE_DICT
    
    # Register tasks in django_celery_beat with better error handling
    max_attempts = 3
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
                    
                    # Add task arguments if present
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
                
        except OperationalError:
            logger.warning(f"⚠️ Database not available on attempt {attempt+1}/{max_attempts}")
            if attempt < max_attempts - 1:
                time.sleep(10)  # Wait 10 seconds before retrying
        except Exception as e:
            logger.error(f"❌ Error registering periodic tasks: {str(e)}")
            break

# Connect setup function to Celery configuration signal
app.on_after_configure.connect(setup_periodic_tasks)

# Autodiscover tasks
app.autodiscover_tasks()

# Task-specific rate limits and resource constraints with better limits
app.conf.task_annotations.update({
    'app.tasks.generate_and_send_reports': {
        'rate_limit': '3/m',
        'time_limit': 300,  # 5 minutes
        'soft_time_limit': 270,  # 4.5 minutes
    },
    'app.tasks.send_daily_notification': {
        'rate_limit': '3/m',
        'time_limit': 300,
    },
    'app.tasks.execute_ml_and_scraping': {
        'rate_limit': '1/h',
        'time_limit': 2700,  # 45 minutes
        'soft_time_limit': 2400,  # 40 minutes
    },
    'app.tasks.ejecutar_scraping': {
        'rate_limit': '6/h',
        'time_limit': 2700,
        'soft_time_limit': 2400,
    },
    'app.tasks.train_ml_task': {
        'rate_limit': '8/h',
        'time_limit': 5400,  # 1.5 hours
        'soft_time_limit': 4800,  # 1.3 hours
    },
})