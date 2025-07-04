"""
huntRED® v2 - Celery Application
Task queue configuration for distributed processing
"""

import os
from celery import Celery
from kombu import Queue

# Get configuration from environment
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

# Create Celery application
celery_app = Celery('huntred_v2')

# Configure Celery
celery_app.conf.update(
    # Broker settings
    broker_url=BROKER_URL,
    result_backend=RESULT_BACKEND,
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'src.tasks.notifications.*': {'queue': 'notifications'},
        'src.tasks.ml.*': {'queue': 'ml'},
        'src.tasks.scraping.*': {'queue': 'scraping'},
        'src.tasks.onboarding.*': {'queue': 'onboarding'},
        'src.tasks.reports.*': {'queue': 'reports'},
        'src.tasks.maintenance.*': {'queue': 'maintenance'},
        'src.tasks.messaging.*': {'queue': 'messaging'},
    },
    
    # Queue configuration
    task_default_queue='default',
    task_queues=(
        Queue('default', routing_key='default'),
        Queue('notifications', routing_key='notifications'),
        Queue('ml', routing_key='ml'),
        Queue('scraping', routing_key='scraping'),
        Queue('onboarding', routing_key='onboarding'),
        Queue('reports', routing_key='reports'),
        Queue('maintenance', routing_key='maintenance'),
        Queue('messaging', routing_key='messaging'),
        Queue('payroll', routing_key='payroll'),
        Queue('analytics', routing_key='analytics'),
    ),
    
    # Worker settings
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # Result settings
    result_expires=3600,  # 1 hour
    
    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Rate limiting
    task_annotations={
        'src.tasks.notifications.send_whatsapp_message_task': {'rate_limit': '10/m'},
        'src.tasks.notifications.send_telegram_message_task': {'rate_limit': '10/m'},
        'src.tasks.notifications.send_email_task': {'rate_limit': '50/m'},
        'src.tasks.ml.train_ml_task': {'rate_limit': '1/h'},
        'src.tasks.ml.train_matchmaking_model_task': {'rate_limit': '5/h'},
    },
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-conversations': {
            'task': 'src.tasks.maintenance.cleanup_old_conversations',
            'schedule': 3600.0,  # Every hour
        },
        'train-ml-models': {
            'task': 'src.tasks.ml.train_ml_task',
            'schedule': 86400.0,  # Daily
        },
        'sync-jobs': {
            'task': 'src.tasks.ml.sync_jobs_with_api',
            'schedule': 21600.0,  # Every 6 hours
        },
        'analyze-communication-patterns': {
            'task': 'src.tasks.notifications.analyze_communication_patterns_task',
            'schedule': 43200.0,  # Every 12 hours
        },
        'update-user-profiles': {
            'task': 'src.tasks.notifications.update_user_communication_profiles_task',
            'schedule': 86400.0,  # Daily
        },
        'system-maintenance': {
            'task': 'src.tasks.maintenance.run_maintenance_tasks',
            'schedule': 604800.0,  # Weekly
        },
    },
)

# Auto-discover tasks from modules
celery_app.autodiscover_tasks([
    'src.tasks.base',
    'src.tasks.notifications',
    'src.tasks.ml',
    'src.tasks.scraping',
    'src.tasks.onboarding',
    'src.tasks.reports',
    'src.tasks.maintenance',
    'src.tasks.messaging',
])

if __name__ == '__main__':
    celery_app.start()