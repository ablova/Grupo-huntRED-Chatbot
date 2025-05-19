# /home/pablo/app/com/feedback/celery_config.py
"""
Configuración de tareas Celery para el sistema de retroalimentación.

Este archivo define las tareas programadas que se deben registrar
en el archivo celery.py principal de la aplicación.
"""

from celery.schedules import crontab

# Definición de tareas programadas para el sistema de feedback
CELERY_BEAT_SCHEDULE_FEEDBACK = {
    'send_proposal_feedback_requests': {
        'task': 'app.com.feedback.tasks.send_proposal_feedback_requests',
        'schedule': crontab(hour=9, minute=0),  # Todos los días a las 9:00 AM
        'options': {'queue': 'feedback'},
    },
    'send_ongoing_feedback_requests': {
        'task': 'app.com.feedback.tasks.send_ongoing_feedback_requests',
        'schedule': crontab(hour=10, minute=0),  # Todos los días a las 10:00 AM
        'options': {'queue': 'feedback'},
    },
    'send_completion_feedback_requests': {
        'task': 'app.com.feedback.tasks.send_completion_feedback_requests',
        'schedule': crontab(hour=11, minute=0),  # Todos los días a las 11:00 AM
        'options': {'queue': 'feedback'},
    },
    'process_pending_reminders': {
        'task': 'app.com.feedback.tasks.process_pending_reminders',
        'schedule': crontab(hour='*/3', minute=15),  # Cada 3 horas
        'options': {'queue': 'feedback'},
    },
    'check_pending_responses': {
        'task': 'app.com.feedback.tasks.check_pending_responses',
        'schedule': crontab(hour='*/6', minute=30),  # Cada 6 horas
        'options': {'queue': 'feedback'},
    },
    'generate_weekly_feedback_report': {
        'task': 'app.com.feedback.tasks.generate_weekly_feedback_report',
        'schedule': crontab(day_of_week=1, hour=8, minute=0),  # Lunes a las 8:00 AM
        'options': {'queue': 'feedback'},
    },
}

# Instrucciones para integrar con el archivo celery.py principal:
"""
Para integrar estas tareas en su configuración Celery principal, agregue lo siguiente
a su archivo celery.py:

from app.com.feedback.celery_config import CELERY_BEAT_SCHEDULE_FEEDBACK

# Después de la configuración app.conf.beat_schedule existente:
app.conf.beat_schedule.update(CELERY_BEAT_SCHEDULE_FEEDBACK)
"""
