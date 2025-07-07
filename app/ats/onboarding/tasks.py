#  app/ats/onboarding/tasks.py
"""
Módulo de tareas de onboarding para Celery.

Este módulo contiene las tareas asíncronas relacionadas con el proceso de onboarding,
incluyendo acompañamiento continuo, seguimiento de satisfacción y reportes para clientes.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from app.models import OnboardingProcess, OnboardingTask, Person, Vacante, BusinessUnit
from app.ats.onboarding.onboarding_controller import OnboardingController
from app.ats.onboarding.satisfaction_tracker import SatisfactionTracker
from app.ats.integrations.notifications.process.onboarding_notifications import OnboardingNotificationService
from app.ats.integrations.services.email_campaigns import EmailCampaignService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def start_onboarding_process(self, person_id: int, vacancy_id: int, hire_date: Optional[str] = None):
    """
    Inicia un nuevo proceso de onboarding para un candidato.
    
    Args:
        person_id: ID del candidato
        vacancy_id: ID de la vacante
        hire_date: Fecha de contratación (opcional, formato ISO)
    """
    try:
        # Convertir hire_date si se proporciona
        hire_date_obj = None
        if hire_date:
            hire_date_obj = datetime.fromisoformat(hire_date.replace('Z', '+00:00'))
        
        # Ejecutar el proceso de onboarding
        result = asyncio.run(OnboardingController.start_onboarding_process(
            person_id=person_id,
            vacancy_id=vacancy_id,
            hire_date=hire_date_obj
        ))
        
        if result.get('success'):
            logger.info(f"Proceso de onboarding iniciado exitosamente: {result.get('process_id')}")
            return f"Onboarding iniciado: {result.get('process_id')}"
        else:
            raise ValueError(f"Error iniciando onboarding: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error en tarea start_onboarding_process: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)  # Reintentar en 5 minutos


@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, onboarding_id: int):
    """
    Envía email de bienvenida al candidato en el proceso de onboarding.
    
    Args:
        onboarding_id: ID del proceso de onboarding
    """
    try:
        # Obtener el proceso de onboarding
        process = OnboardingProcess.objects.get(id=onboarding_id)
        person = process.person
        vacancy = process.vacancy
        
        # Preparar contexto del email
        context = {
            'person': person,
            'vacancy': vacancy,
            'hire_date': process.hire_date,
            'company_name': vacancy.empresa.name if hasattr(vacancy, 'empresa') and vacancy.empresa else "la empresa",
            'onboarding_url': f"{settings.SITE_URL}/onboarding/{onboarding_id}",
            'dashboard_url': f"{settings.SITE_URL}/dashboard"
        }
        
        # Renderizar template de email
        subject = f"¡Bienvenido/a a {context['company_name']}!"
        html_message = render_to_string('emails/onboarding_welcome.html', context)
        plain_message = render_to_string('emails/onboarding_welcome.txt', context)
        
        # Enviar email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[person.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Email de bienvenida enviado a {person.email} para onboarding {onboarding_id}")
        return f"Email de bienvenida enviado: {person.email}"
        
    except OnboardingProcess.DoesNotExist:
        logger.error(f"Proceso de onboarding {onboarding_id} no encontrado")
        return f"Error: Proceso de onboarding {onboarding_id} no encontrado"
    except Exception as e:
        logger.error(f"Error enviando email de bienvenida: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)  # Reintentar en 5 minutos


@shared_task(bind=True, max_retries=3)
def schedule_onboarding_tasks(self, onboarding_id: int):
    """
    Programa las tareas automáticas del proceso de onboarding.
    
    Args:
        onboarding_id: ID del proceso de onboarding
    """
    try:
        # Obtener el proceso de onboarding
        process = OnboardingProcess.objects.get(id=onboarding_id)
        
        # Programar tareas estándar si no existen
        existing_tasks = OnboardingTask.objects.filter(onboarding=process)
        
        if not existing_tasks.exists():
            # Crear tareas estándar de acompañamiento
            tasks_data = [
                {
                    'title': "Bienvenida y documentación inicial",
                    'description': "Enviar correo de bienvenida y solicitar documentación pendiente",
                    'priority': 10,
                    'due_date': timezone.now() + timedelta(days=1)
                },
                {
                    'title': "Configuración de accesos y herramientas",
                    'description': "Coordinar con IT la configuración de cuentas y accesos",
                    'priority': 9,
                    'due_date': timezone.now() + timedelta(days=2)
                },
                {
                    'title': "Reunión inicial con equipo",
                    'description': "Agendar presentación con el equipo y áreas relacionadas",
                    'priority': 8,
                    'due_date': timezone.now() + timedelta(days=3)
                },
                {
                    'title': "Sesión de capacitación inicial",
                    'description': "Coordinar entrenamiento sobre procesos y herramientas clave",
                    'priority': 7,
                    'due_date': timezone.now() + timedelta(days=7)
                },
                {
                    'title': "Check-in de primera semana",
                    'description': "Verificar adaptación y resolver dudas iniciales",
                    'priority': 6,
                    'due_date': timezone.now() + timedelta(days=7)
                },
                {
                    'title': "Evaluación de satisfacción inicial (3 días)",
                    'description': "Enviar encuesta de satisfacción del primer período",
                    'priority': 5,
                    'due_date': timezone.now() + timedelta(days=3)
                },
                {
                    'title': "Check-in de primer mes",
                    'description': "Evaluar integración y satisfacción del primer mes",
                    'priority': 4,
                    'due_date': timezone.now() + timedelta(days=30)
                },
                {
                    'title': "Evaluación de satisfacción mensual",
                    'description': "Enviar encuesta de satisfacción del primer mes",
                    'priority': 3,
                    'due_date': timezone.now() + timedelta(days=30)
                },
                {
                    'title': "Check-in de tres meses",
                    'description': "Evaluar consolidación en el puesto y satisfacción",
                    'priority': 2,
                    'due_date': timezone.now() + timedelta(days=90)
                },
                {
                    'title': "Evaluación de satisfacción trimestral",
                    'description': "Enviar encuesta de satisfacción de tres meses",
                    'priority': 1,
                    'due_date': timezone.now() + timedelta(days=90)
                }
            ]
            
            for task_data in tasks_data:
                OnboardingTask.objects.create(
                    onboarding=process,
                    **task_data
                )
            
            logger.info(f"Programadas {len(tasks_data)} tareas de acompañamiento para onboarding {onboarding_id}")
            return f"Programadas {len(tasks_data)} tareas de acompañamiento"
        else:
            logger.info(f"Tareas ya existen para onboarding {onboarding_id}")
            return f"Tareas ya programadas: {existing_tasks.count()} tareas"
            
    except OnboardingProcess.DoesNotExist:
        logger.error(f"Proceso de onboarding {onboarding_id} no encontrado")
        return f"Error: Proceso de onboarding {onboarding_id} no encontrado"
    except Exception as e:
        logger.error(f"Error programando tareas de onboarding: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)  # Reintentar en 5 minutos


@shared_task(bind=True, max_retries=3)
def process_onboarding_documents(self, onboarding_id: int):
    """
    Procesa los documentos del proceso de onboarding.
    
    Args:
        onboarding_id: ID del proceso de onboarding
    """
    try:
        # Obtener el proceso de onboarding
        process = OnboardingProcess.objects.get(id=onboarding_id)
        
        # Verificar documentos pendientes
        pending_documents = process.get_pending_documents()
        
        if pending_documents:
            # Enviar recordatorio de documentos pendientes
            notification_service = OnboardingNotificationService()
            asyncio.run(notification_service.notify_task_reminder(
                task_id=process.tasks.filter(title__icontains="documentación").first().id
            ))
            
            logger.info(f"Recordatorio de documentos enviado para onboarding {onboarding_id}")
            return f"Recordatorio enviado: {len(pending_documents)} documentos pendientes"
        else:
            logger.info(f"No hay documentos pendientes para onboarding {onboarding_id}")
            return "No hay documentos pendientes"
            
    except OnboardingProcess.DoesNotExist:
        logger.error(f"Proceso de onboarding {onboarding_id} no encontrado")
        return f"Error: Proceso de onboarding {onboarding_id} no encontrado"
    except Exception as e:
        logger.error(f"Error procesando documentos de onboarding: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)  # Reintentar en 5 minutos


@shared_task(bind=True, max_retries=3)
def send_onboarding_reminder(self, onboarding_id: int, task_id: Optional[int] = None):
    """
    Envía recordatorio de tareas pendientes en el onboarding.
    
    Args:
        onboarding_id: ID del proceso de onboarding
        task_id: ID específico de la tarea (opcional)
    """
    try:
        # Obtener el proceso de onboarding
        process = OnboardingProcess.objects.get(id=onboarding_id)
        
        if task_id:
            # Recordatorio para tarea específica
            task = OnboardingTask.objects.get(id=task_id, onboarding=process)
            tasks_to_remind = [task]
        else:
            # Recordatorio para todas las tareas pendientes
            tasks_to_remind = process.tasks.filter(
                status='pending',
                due_date__lte=timezone.now() + timedelta(days=1)
            )
        
        if tasks_to_remind:
            notification_service = OnboardingNotificationService()
            
            for task in tasks_to_remind:
                asyncio.run(notification_service.notify_task_reminder(task.id))
            
            logger.info(f"Recordatorios enviados para {len(tasks_to_remind)} tareas en onboarding {onboarding_id}")
            return f"Recordatorios enviados: {len(tasks_to_remind)} tareas"
        else:
            logger.info(f"No hay tareas pendientes para recordar en onboarding {onboarding_id}")
            return "No hay tareas pendientes"
            
    except OnboardingProcess.DoesNotExist:
        logger.error(f"Proceso de onboarding {onboarding_id} no encontrado")
        return f"Error: Proceso de onboarding {onboarding_id} no encontrado"
    except Exception as e:
        logger.error(f"Error enviando recordatorios de onboarding: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)  # Reintentar en 5 minutos


@shared_task(bind=True, max_retries=3)
def send_check_in_reminder(self, onboarding_id: int, check_in_type: str):
    """
    Envía recordatorio de check-in según el tipo (semana, mes, trimestre).
    
    Args:
        onboarding_id: ID del proceso de onboarding
        check_in_type: Tipo de check-in ('week', 'month', 'quarter')
    """
    try:
        # Obtener el proceso de onboarding
        process = OnboardingProcess.objects.get(id=onboarding_id)
        person = process.person
        vacancy = process.vacancy
        
        # Preparar mensaje según el tipo de check-in
        if check_in_type == 'week':
            subject = f"Check-in de primera semana - {person.first_name}"
            message = f"¡Hola {person.first_name}! Han pasado 7 días desde tu incorporación. ¿Cómo te sientes en tu nuevo rol como {vacancy.title}?"
        elif check_in_type == 'month':
            subject = f"Check-in de primer mes - {person.first_name}"
            message = f"¡Hola {person.first_name}! Ya llevas un mes con nosotros como {vacancy.title}. Nos gustaría saber cómo va todo."
        elif check_in_type == 'quarter':
            subject = f"Check-in de tres meses - {person.first_name}"
            message = f"¡Hola {person.first_name}! Han pasado 3 meses desde tu incorporación como {vacancy.title}. ¿Cómo te sientes en tu desarrollo?"
        else:
            raise ValueError(f"Tipo de check-in no válido: {check_in_type}")
        
        # Enviar email de check-in
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[person.email],
            fail_silently=False
        )
        
        logger.info(f"Check-in {check_in_type} enviado a {person.email} para onboarding {onboarding_id}")
        return f"Check-in {check_in_type} enviado: {person.email}"
        
    except OnboardingProcess.DoesNotExist:
        logger.error(f"Proceso de onboarding {onboarding_id} no encontrado")
        return f"Error: Proceso de onboarding {onboarding_id} no encontrado"
    except Exception as e:
        logger.error(f"Error enviando check-in {check_in_type}: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)  # Reintentar en 5 minutos


@shared_task(bind=True, max_retries=3)
def send_satisfaction_survey_reminder(self, onboarding_id: int, period_days: int):
    """
    Envía recordatorio de encuesta de satisfacción para un período específico.
    
    Args:
        onboarding_id: ID del proceso de onboarding
        period_days: Período en días (3, 7, 15, 30, 60, 90, 180, 365)
    """
    try:
        # Obtener el proceso de onboarding
        process = OnboardingProcess.objects.get(id=onboarding_id)
        person = process.person
        vacancy = process.vacancy
        
        # Verificar si ya se envió la encuesta
        tracker = SatisfactionTracker()
        survey_sent = asyncio.run(tracker.send_satisfaction_survey(onboarding_id, period_days))
        
        if survey_sent:
            logger.info(f"Encuesta de {period_days} días enviada a {person.email} para onboarding {onboarding_id}")
            return f"Encuesta de {period_days} días enviada: {person.email}"
        else:
            logger.info(f"Encuesta de {period_days} días ya fue enviada para onboarding {onboarding_id}")
            return f"Encuesta de {period_days} días ya enviada"
        
    except OnboardingProcess.DoesNotExist:
        logger.error(f"Proceso de onboarding {onboarding_id} no encontrado")
        return f"Error: Proceso de onboarding {onboarding_id} no encontrado"
    except Exception as e:
        logger.error(f"Error enviando encuesta de {period_days} días: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)  # Reintentar en 5 minutos


@shared_task(bind=True, max_retries=3)
def generate_client_satisfaction_report(self, onboarding_id: int, period_days: int):
    """
    Genera y envía reporte de satisfacción al cliente para períodos clave.
    
    Args:
        onboarding_id: ID del proceso de onboarding
        period_days: Período en días (30, 90, 180, 365)
    """
    try:
        # Solo generar reportes para períodos clave
        if period_days not in [30, 90, 180, 365]:
            logger.info(f"No se genera reporte para período {period_days} días")
            return f"No se genera reporte para período {period_days} días"
        
        # Obtener el proceso de onboarding
        process = OnboardingProcess.objects.get(id=onboarding_id)
        vacancy = process.vacancy
        company = vacancy.empresa
        
        # Generar reporte usando el tracker
        tracker = SatisfactionTracker()
        report_generated = asyncio.run(tracker._generate_client_report(onboarding_id, period_days))
        
        if report_generated:
            logger.info(f"Reporte de {period_days} días generado para {company.name}")
            return f"Reporte de {period_days} días generado para {company.name}"
        else:
            logger.warning(f"No se pudo generar reporte de {period_days} días para {company.name}")
            return f"No se pudo generar reporte de {period_days} días"
        
    except OnboardingProcess.DoesNotExist:
        logger.error(f"Proceso de onboarding {onboarding_id} no encontrado")
        return f"Error: Proceso de onboarding {onboarding_id} no encontrado"
    except Exception as e:
        logger.error(f"Error generando reporte de {period_days} días: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)  # Reintentar en 5 minutos


@shared_task(bind=True, max_retries=3)
def complete_onboarding_process(self, onboarding_id: int):
    """
    Marca el proceso de onboarding como completado.
    
    Args:
        onboarding_id: ID del proceso de onboarding
    """
    try:
        # Obtener el proceso de onboarding
        process = OnboardingProcess.objects.get(id=onboarding_id)
        
        # Verificar que todas las tareas estén completadas
        pending_tasks = process.tasks.filter(status__in=['pending', 'in_progress'])
        
        if pending_tasks.exists():
            logger.warning(f"No se puede completar onboarding {onboarding_id}: {pending_tasks.count()} tareas pendientes")
            return f"No se puede completar: {pending_tasks.count()} tareas pendientes"
        
        # Marcar como completado
        process.status = 'COMPLETED'
        process.completed_at = timezone.now()
        process.save()
        
        # Enviar notificación de completado
        notification_service = OnboardingNotificationService()
        asyncio.run(notification_service.notify_onboarding_started(onboarding_id))
        
        logger.info(f"Proceso de onboarding {onboarding_id} marcado como completado")
        return f"Onboarding completado: {onboarding_id}"
        
    except OnboardingProcess.DoesNotExist:
        logger.error(f"Proceso de onboarding {onboarding_id} no encontrado")
        return f"Error: Proceso de onboarding {onboarding_id} no encontrado"
    except Exception as e:
        logger.error(f"Error completando proceso de onboarding: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)  # Reintentar en 5 minutos


@shared_task(bind=True, max_retries=3)
def schedule_follow_up_sequence(self, onboarding_id: int):
    """
    Programa toda la secuencia de seguimiento y acompañamiento para un onboarding.
    
    Args:
        onboarding_id: ID del proceso de onboarding
    """
    try:
        # Obtener el proceso de onboarding
        process = OnboardingProcess.objects.get(id=onboarding_id)
        hire_date = process.hire_date
        
        # Programar check-ins
        check_in_dates = [
            (hire_date + timedelta(days=7), 'week'),
            (hire_date + timedelta(days=30), 'month'),
            (hire_date + timedelta(days=90), 'quarter')
        ]
        
        for check_in_date, check_in_type in check_in_dates:
            if check_in_date > timezone.now():
                send_check_in_reminder.apply_async(
                    args=[onboarding_id, check_in_type],
                    eta=check_in_date
                )
        
        # Programar encuestas de satisfacción
        survey_periods = [3, 7, 15, 30, 60, 90, 180, 365]
        
        for period in survey_periods:
            survey_date = hire_date + timedelta(days=period)
            if survey_date > timezone.now():
                send_satisfaction_survey_reminder.apply_async(
                    args=[onboarding_id, period],
                    eta=survey_date
                )
        
        # Programar reportes para cliente
        report_periods = [30, 90, 180, 365]
        
        for period in report_periods:
            report_date = hire_date + timedelta(days=period + 1)  # +1 día después de la encuesta
            if report_date > timezone.now():
                generate_client_satisfaction_report.apply_async(
                    args=[onboarding_id, period],
                    eta=report_date
                )
        
        logger.info(f"Secuencia de seguimiento programada para onboarding {onboarding_id}")
        return f"Secuencia de seguimiento programada: {len(check_in_dates)} check-ins, {len(survey_periods)} encuestas, {len(report_periods)} reportes"
        
    except OnboardingProcess.DoesNotExist:
        logger.error(f"Proceso de onboarding {onboarding_id} no encontrado")
        return f"Error: Proceso de onboarding {onboarding_id} no encontrado"
    except Exception as e:
        logger.error(f"Error programando secuencia de seguimiento: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)  # Reintentar en 5 minutos 