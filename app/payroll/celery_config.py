"""
Configuración de Celery para huntRED® Payroll
Tareas programadas para actualización de tablas fiscales
"""
from celery import Celery
from celery.schedules import crontab
from django.conf import settings
import os

# Configurar Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('huntred_payroll')

# Configuración desde settings de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrir tareas
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Configuración de beat schedule para tareas programadas
app.conf.beat_schedule = {
    # Actualización diaria de UMA (a las 2 AM)
    'update-uma-daily': {
        'task': 'app.payroll.tasks.update_uma_values',
        'schedule': crontab(hour=2, minute=0),
        'args': ('MEX',),
        'options': {'queue': 'tax_updates'}
    },
    
    # Actualización semanal de tablas fiscales (domingos a las 3 AM)
    'update-tax-tables-weekly': {
        'task': 'app.payroll.tasks.update_tax_tables',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),
        'args': ('MEX',),
        'options': {'queue': 'tax_updates'}
    },
    
    # Actualización mensual de tablas IMSS (primer día del mes a las 4 AM)
    'update-imss-monthly': {
        'task': 'app.payroll.tasks.update_imss_tables',
        'schedule': crontab(day_of_month=1, hour=4, minute=0),
        'options': {'queue': 'tax_updates'}
    },
    
    # Actualización mensual de tablas INFONAVIT (primer día del mes a las 4:30 AM)
    'update-infonavit-monthly': {
        'task': 'app.payroll.tasks.update_infonavit_tables',
        'schedule': crontab(day_of_month=1, hour=4, minute=30),
        'options': {'queue': 'tax_updates'}
    },
    
    # Actualización mensual de tablas SAT (primer día del mes a las 5 AM)
    'update-sat-monthly': {
        'task': 'app.payroll.tasks.update_sat_tables',
        'schedule': crontab(day_of_month=1, hour=5, minute=0),
        'options': {'queue': 'tax_updates'}
    },
    
    # Validación diaria de cálculos fiscales (a las 6 AM)
    'validate-tax-calculations-daily': {
        'task': 'app.payroll.tasks.validate_tax_calculations',
        'schedule': crontab(hour=6, minute=0),
        'options': {'queue': 'validation'}
    },
    
    # Actualización de tablas colombianas (primer domingo del mes a las 7 AM)
    'update-colombian-tables-monthly': {
        'task': 'app.payroll.tasks.update_tax_tables',
        'schedule': crontab(day_of_week=0, hour=7, minute=0),
        'args': ('COL',),
        'options': {'queue': 'tax_updates'}
    },
    
    # Actualización de tablas argentinas (primer domingo del mes a las 8 AM)
    'update-argentine-tables-monthly': {
        'task': 'app.payroll.tasks.update_tax_tables',
        'schedule': crontab(day_of_week=0, hour=8, minute=0),
        'args': ('ARG',),
        'options': {'queue': 'tax_updates'}
    },
    
    # Limpieza de logs antiguos (primer día del mes a las 9 AM)
    'cleanup-old-logs-monthly': {
        'task': 'app.payroll.tasks.cleanup_old_logs',
        'schedule': crontab(day_of_month=1, hour=9, minute=0),
        'options': {'queue': 'maintenance'}
    },
    
    # Backup de tablas fiscales (primer día del mes a las 10 AM)
    'backup-tax-tables-monthly': {
        'task': 'app.payroll.tasks.backup_tax_tables',
        'schedule': crontab(day_of_month=1, hour=10, minute=0),
        'options': {'queue': 'backup'}
    },
}

# Configuración de colas
app.conf.task_routes = {
    'app.payroll.tasks.update_uma_values': {'queue': 'tax_updates'},
    'app.payroll.tasks.update_tax_tables': {'queue': 'tax_updates'},
    'app.payroll.tasks.update_imss_tables': {'queue': 'tax_updates'},
    'app.payroll.tasks.update_infonavit_tables': {'queue': 'tax_updates'},
    'app.payroll.tasks.update_sat_tables': {'queue': 'tax_updates'},
    'app.payroll.tasks.validate_tax_calculations': {'queue': 'validation'},
    'app.payroll.tasks.notify_tax_updates': {'queue': 'notifications'},
    'app.payroll.tasks.cleanup_old_logs': {'queue': 'maintenance'},
    'app.payroll.tasks.backup_tax_tables': {'queue': 'backup'},
}

# Configuración de reintentos
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

# Configuración de timeouts
app.conf.task_soft_time_limit = 300  # 5 minutos
app.conf.task_time_limit = 600       # 10 minutos

# Configuración de rate limiting
app.conf.task_annotations = {
    'app.payroll.tasks.update_uma_values': {'rate_limit': '10/m'},
    'app.payroll.tasks.update_tax_tables': {'rate_limit': '5/m'},
    'app.payroll.tasks.update_imss_tables': {'rate_limit': '2/m'},
    'app.payroll.tasks.update_infonavit_tables': {'rate_limit': '2/m'},
    'app.payroll.tasks.update_sat_tables': {'rate_limit': '2/m'},
    'app.payroll.tasks.validate_tax_calculations': {'rate_limit': '1/m'},
}

# Configuración de monitoreo
app.conf.worker_prefetch_multiplier = 1
app.conf.task_always_eager = False  # Cambiar a True para desarrollo

# Configuración de resultados
app.conf.result_backend = 'redis://localhost:6379/1'
app.conf.result_expires = 3600  # 1 hora

# Configuración de logs
app.conf.worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
app.conf.worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Configuración de eventos
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True

# Configuración de seguridad
app.conf.broker_connection_retry_on_startup = True
app.conf.broker_connection_max_retries = 10

# Configuración de monitoreo de salud
app.conf.worker_disable_rate_limits = False
app.conf.task_ignore_result = False

# Configuración de notificaciones
app.conf.task_track_started = True
app.conf.task_remote_tracebacks = True

# Configuración de desarrollo vs producción
if settings.DEBUG:
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True
    app.conf.worker_log_level = 'DEBUG'
else:
    app.conf.worker_log_level = 'INFO'
    app.conf.task_always_eager = False

# Configuración de colas específicas
app.conf.task_default_queue = 'default'
app.conf.task_default_exchange = 'default'
app.conf.task_default_routing_key = 'default'

# Configuración de prioridades
app.conf.task_queue_max_priority = 10
app.conf.task_default_priority = 5

# Configuración de dead letter queue
app.conf.task_default_delivery_mode = 2  # Persistent
app.conf.task_default_retry_delay = 60   # 1 minuto
app.conf.task_default_max_retries = 3

# Configuración de monitoreo de memoria
app.conf.worker_max_memory_per_child = 200000  # 200MB

# Configuración de concurrencia
app.conf.worker_concurrency = 4  # Número de workers concurrentes

# Configuración de pool
app.conf.worker_pool = 'prefork'  # o 'eventlet', 'gevent'

# Configuración de heartbeat
app.conf.broker_heartbeat = 10
app.conf.broker_connection_timeout = 30

# Configuración de SSL (si es necesario)
if hasattr(settings, 'CELERY_BROKER_USE_SSL'):
    app.conf.broker_use_ssl = settings.CELERY_BROKER_USE_SSL

# Configuración de autenticación (si es necesario)
if hasattr(settings, 'CELERY_BROKER_URL'):
    app.conf.broker_url = settings.CELERY_BROKER_URL

# Configuración de resultados (si es necesario)
if hasattr(settings, 'CELERY_RESULT_BACKEND'):
    app.conf.result_backend = settings.CELERY_RESULT_BACKEND

# Configuración de timezone
app.conf.timezone = 'America/Mexico_City'
app.conf.enable_utc = True

# Configuración de imports
app.conf.imports = [
    'app.payroll.tasks',
    'app.payroll.services.payroll_engine',
    'app.payroll.services.authority_integration_service',
    'app.payroll.services.severance_calculation_service',
    'app.payroll.services.workplace_climate_service',
    'app.payroll.services.integration_service',
]

# Configuración de signals
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Configuración de manejo de errores
@app.task(bind=True)
def handle_task_failure(self, exc, task_id, args, kwargs, einfo):
    """Maneja errores en tareas"""
    from .models import TaxUpdateLog
    
    # Registrar error en log
    TaxUpdateLog.objects.create(
        update_type='error',
        country_code='ALL',
        description=f'Error en tarea {task_id}',
        error_message=str(exc),
        success=False,
        source='celery'
    )
    
    # Log del error
    self.logger.error(f'Task {task_id} failed: {exc}')

# Configuración de callbacks
@app.task(bind=True)
def task_success_callback(self, result, task_id, args, kwargs):
    """Callback cuando una tarea es exitosa"""
    self.logger.info(f'Task {task_id} completed successfully')

@app.task(bind=True)
def task_failure_callback(self, exc, task_id, args, kwargs, einfo):
    """Callback cuando una tarea falla"""
    self.logger.error(f'Task {task_id} failed: {exc}')

# Configuración de monitoreo de salud
@app.task(bind=True)
def health_check(self):
    """Tarea de verificación de salud del sistema"""
    from .models import TaxTable, UMARegistry
    
    # Verificar tablas activas
    active_tables = TaxTable.objects.filter(is_active=True).count()
    active_uma = UMARegistry.objects.filter(is_active=True).count()
    
    health_status = {
        'active_tables': active_tables,
        'active_uma': active_uma,
        'timestamp': timezone.now().isoformat(),
        'status': 'healthy' if active_tables > 0 and active_uma > 0 else 'unhealthy'
    }
    
    return health_status

# Configuración de limpieza
@app.task(bind=True)
def cleanup_old_logs(self, days=90):
    """Limpia logs antiguos"""
    from datetime import timedelta
    from .models import TaxUpdateLog, TaxValidationLog
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Limpiar logs de actualización
    deleted_updates = TaxUpdateLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()
    
    # Limpiar logs de validación
    deleted_validations = TaxValidationLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()
    
    return {
        'deleted_updates': deleted_updates[0],
        'deleted_validations': deleted_validations[0],
        'cutoff_date': cutoff_date.isoformat()
    }

# Configuración de backup
@app.task(bind=True)
def backup_tax_tables(self):
    """Crea backup de tablas fiscales"""
    from .models import TaxTable, UMARegistry
    import json
    
    # Backup de tablas fiscales
    tax_tables = list(TaxTable.objects.filter(is_active=True).values())
    
    # Backup de valores UMA
    uma_values = list(UMARegistry.objects.filter(is_active=True).values())
    
    backup_data = {
        'tax_tables': tax_tables,
        'uma_values': uma_values,
        'backup_date': timezone.now().isoformat()
    }
    
    # Guardar backup (implementar según necesidades)
    backup_filename = f'tax_backup_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    return {
        'backup_filename': backup_filename,
        'tax_tables_count': len(tax_tables),
        'uma_values_count': len(uma_values),
        'backup_date': backup_data['backup_date']
    } 