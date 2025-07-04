"""
🚀 GhuntRED-v2 Celery Configuration
Background task processing with ML integration
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('ghuntred_v2')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'process-candidate-analysis': {
        'task': 'tasks.ml_tasks.process_pending_candidate_analysis',
        'schedule': 300.0,  # Every 5 minutes
    },
    'cleanup-old-sessions': {
        'task': 'tasks.system_tasks.cleanup_old_sessions',
        'schedule': 3600.0,  # Every hour
    },
    'send-job-alerts': {
        'task': 'tasks.notification_tasks.send_job_alerts',
        'schedule': 86400.0,  # Daily
    },
    'generate-analytics': {
        'task': 'tasks.analytics_tasks.generate_daily_analytics',
        'schedule': 86400.0,  # Daily
    },
}

app.conf.timezone = 'America/Mexico_City'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')