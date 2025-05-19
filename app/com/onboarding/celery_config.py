# /home/pablo/app/com/onboarding/celery_config.py
"""
Configuración de tareas programadas de Celery para el módulo de onboarding.

Este módulo configura las tareas periódicas relacionadas con el onboarding y
seguimiento de satisfacción de candidatos.
"""

from celery import shared_task
from celery.schedules import crontab
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)

def setup_onboarding_tasks():
    """
    Configura las tareas periódicas para el módulo de onboarding y feedback de clientes.
    Esta función debe ser llamada al inicio de la aplicación.
    """
    try:
        logger.info("Configurando tareas periódicas de onboarding y feedback de clientes...")

        # 1. Tarea diaria para revisar encuestas de satisfacción pendientes (9:00 AM)
        schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=9,
            minute=0,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone=timezone.get_current_timezone()
        )
        
        PeriodicTask.objects.update_or_create(
            name='Verificar encuestas de satisfacción pendientes',
            defaults={
                'task': 'app.tasks.check_satisfaction_surveys_task',
                'crontab': schedule,
                'enabled': True,
                'description': 'Revisa diariamente los procesos de onboarding y programa encuestas de satisfacción según corresponda.'
            }
        )
        
        # 2. Tarea mensual para generar reportes de satisfacción para clientes (1er día del mes, 5:00 AM)
        schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=5,
            minute=0,
            day_of_week='*',
            day_of_month='1',
            month_of_year='*',
            timezone=timezone.get_current_timezone()
        )
        
        PeriodicTask.objects.update_or_create(
            name='Generar reportes mensuales de satisfacción',
            defaults={
                'task': 'app.tasks.generate_client_satisfaction_reports_task',
                'crontab': schedule,
                'enabled': True,
                'description': 'Genera reportes mensuales de satisfacción para clientes con procesos de onboarding activos.'
            }
        )
        
        # 3. Tarea semanal para procesar datos de onboarding para ML (domingo, 3:00 AM)
        schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=3,
            minute=0,
            day_of_week='0',  # Domingo
            day_of_month='*',
            month_of_year='*',
            timezone=timezone.get_current_timezone()
        )
        
        PeriodicTask.objects.update_or_create(
            name='Procesar datos de onboarding para ML',
            defaults={
                'task': 'app.tasks.process_onboarding_ml_data_task',
                'crontab': schedule,
                'enabled': True,
                'description': 'Procesa datos de onboarding para actualizar modelos predictivos de satisfacción y retención.'
            }
        )
        
        # 4. Tarea diaria para verificar encuestas de clientes pendientes (10:00 AM)
        schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=10,
            minute=0,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone=timezone.get_current_timezone()
        )
        
        PeriodicTask.objects.update_or_create(
            name='Verificar encuestas de clientes pendientes',
            defaults={
                'task': 'app.com.onboarding.client_feedback_tasks.check_pending_client_feedback_task',
                'crontab': schedule,
                'enabled': True,
                'description': 'Revisa diariamente las programaciones de feedback de clientes y envía encuestas pendientes.'
            }
        )
        
        # 5. Tarea mensual para generar reportes de satisfacción de clientes (2do día del mes, 6:00 AM)
        schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=6,
            minute=0,
            day_of_week='*',
            day_of_month='2',
            month_of_year='*',
            timezone=timezone.get_current_timezone()
        )
        
        PeriodicTask.objects.update_or_create(
            name='Generar reportes mensuales de satisfacción de clientes',
            defaults={
                'task': 'app.com.onboarding.client_feedback_tasks.generate_client_feedback_reports_task',
                'crontab': schedule,
                'enabled': True,
                'description': 'Genera reportes mensuales de satisfacción de clientes por Business Unit.'
            }
        )
        
        # 6. Tarea quincenal para analizar tendencias de feedback (domingos alternos, 4:00 AM)
        schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=4,
            minute=0,
            day_of_week='0',  # Domingo
            day_of_month='*/15',  # Cada 15 días
            month_of_year='*',
            timezone=timezone.get_current_timezone()
        )
        
        PeriodicTask.objects.update_or_create(
            name='Analizar tendencias de feedback de clientes',
            defaults={
                'task': 'app.com.onboarding.client_feedback_tasks.analyze_client_feedback_trends_task',
                'crontab': schedule,
                'enabled': True,
                'description': 'Analiza tendencias y patrones en el feedback de clientes para identificar áreas de mejora.'
            }
        )
        
        logger.info("Tareas periódicas de onboarding y feedback de clientes configuradas correctamente.")
        
    except Exception as e:
        logger.error(f"Error configurando tareas periódicas: {str(e)}")
        raise
