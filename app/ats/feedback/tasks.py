# /home/pablo/app/com/feedback/tasks.py
"""
Tareas programadas para el sistema integrado de retroalimentación de Grupo huntRED®.

Este módulo contiene las tareas Celery que se ejecutan periódicamente para:
1. Enviar solicitudes de feedback programadas
2. Procesar recordatorios pendientes
3. Verificar respuestas para solicitudes pendientes
4. Generar informes automáticos de insights
"""

import logging
import asyncio
from datetime import timedelta, datetime

from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from celery import shared_task

from app.ats.pricing.proposal_tracker import get_proposal_tracker
from app.ats.feedback.ongoing_tracker import get_ongoing_service_tracker 
from app.ats.feedback.completion_tracker import get_service_completion_tracker
from app.ats.feedback.reminder_system import get_reminder_system

logger = logging.getLogger(__name__)

# Función auxiliar para ejecutar corrutinas asíncronas
def run_async(coroutine):
    """Ejecuta una corrutina asíncrona desde un contexto síncrono."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coroutine)

@shared_task
def send_proposal_feedback_requests():
    """
    Envía solicitudes programadas de retroalimentación de propuestas.
    
    Esta tarea se ejecuta diariamente.
    """
    logger.info("Iniciando envío de solicitudes de retroalimentación de propuestas")
    try:
        tracker = get_proposal_tracker()
        run_async(tracker.send_feedback_requests())
        logger.info("Proceso de envío de retroalimentación de propuestas completado")
    except Exception as e:
        logger.error(f"Error en tarea de envío de retroalimentación de propuestas: {str(e)}")

@shared_task
def send_ongoing_feedback_requests():
    """
    Envía solicitudes programadas de retroalimentación de servicios en curso.
    
    Esta tarea se ejecuta diariamente.
    """
    logger.info("Iniciando envío de solicitudes de retroalimentación de servicios en curso")
    try:
        tracker = get_ongoing_service_tracker()
        run_async(tracker.send_feedback_requests())
        logger.info("Proceso de envío de retroalimentación de servicios en curso completado")
    except Exception as e:
        logger.error(f"Error en tarea de envío de retroalimentación de servicios en curso: {str(e)}")

@shared_task
def send_completion_feedback_requests():
    """
    Envía solicitudes programadas de evaluación final de servicios.
    
    Esta tarea se ejecuta diariamente.
    """
    logger.info("Iniciando envío de solicitudes de evaluación final")
    try:
        tracker = get_service_completion_tracker()
        run_async(tracker.send_completion_feedback_requests())
        logger.info("Proceso de envío de evaluación final completado")
    except Exception as e:
        logger.error(f"Error en tarea de envío de evaluación final: {str(e)}")

@shared_task
def process_pending_reminders():
    """
    Procesa recordatorios pendientes programados.
    
    Esta tarea se ejecuta cada 3 horas.
    """
    logger.info("Iniciando procesamiento de recordatorios pendientes")
    try:
        reminder_system = get_reminder_system()
        run_async(reminder_system.process_pending_reminders())
        logger.info("Proceso de recordatorios pendientes completado")
    except Exception as e:
        logger.error(f"Error en tarea de procesamiento de recordatorios: {str(e)}")

@shared_task
def check_pending_responses():
    """
    Verifica respuestas para solicitudes pendientes.
    
    Esta tarea se ejecuta cada 6 horas.
    """
    logger.info("Iniciando verificación de respuestas pendientes")
    try:
        reminder_system = get_reminder_system()
        run_async(reminder_system.check_pending_responses())
        logger.info("Proceso de verificación de respuestas pendientes completado")
    except Exception as e:
        logger.error(f"Error en tarea de verificación de respuestas: {str(e)}")

@shared_task
def generate_weekly_feedback_report():
    """
    Genera y envía un informe semanal con los insights de retroalimentación.
    
    Esta tarea se ejecuta semanalmente los lunes.
    """
    logger.info("Iniciando generación de informe semanal de retroalimentación")
    try:
        # Definir período (última semana)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        
        # Obtener insights para cada etapa
        stages = ['proposal', 'ongoing', 'completed']
        report_data = {
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'stages': {}
        }
        
        for stage in stages:
            if stage == 'proposal':
                tracker = get_proposal_tracker()
            elif stage == 'ongoing':
                tracker = get_ongoing_service_tracker()
            else:  # completed
                tracker = get_service_completion_tracker()
            
            insights = run_async(tracker.generate_insights_report(
                start_date=start_date,
                end_date=end_date
            ))
            
            report_data['stages'][stage] = insights
        
        # Obtener estadísticas de recordatorios
        reminder_system = get_reminder_system()
        reminder_stats = run_async(reminder_system.get_pending_requests_stats())
        report_data['reminders'] = reminder_stats
        
        # Preparar y enviar email con el informe
        recipients = getattr(settings, 'FEEDBACK_REPORT_RECIPIENTS', [
            getattr(settings, 'MANAGING_DIRECTOR_EMAIL', 'pablo@huntred.com')
        ])
        
        if recipients:
            subject = f"Informe Semanal de Retroalimentación - Grupo huntRED® ({start_date.strftime('%d/%m')} al {end_date.strftime('%d/%m/%Y')})"
            
            # En una implementación real, aquí renderizaríamos una plantilla HTML
            # con gráficos y visualizaciones de los datos
            
            # Versión simple para este ejemplo
            message = (
                f"Informe Semanal de Retroalimentación\n"
                f"Período: {start_date.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')}\n\n"
                f"Retroalimentación de Propuestas:\n"
                f"- Total: {report_data['stages'].get('proposal', {}).get('total_feedbacks', 0)}\n"
                f"- Tasa de interés: {report_data['stages'].get('proposal', {}).get('interest_rate', 0):.1f}%\n\n"
                f"Retroalimentación de Servicios en Curso:\n"
                f"- Total: {report_data['stages'].get('ongoing', {}).get('total_feedbacks', 0)}\n"
                f"- Calificación promedio: {report_data['stages'].get('ongoing', {}).get('average_ratings', {}).get('general', 0):.1f}/5\n\n"
                f"Evaluaciones Finales:\n"
                f"- Total: {report_data['stages'].get('completed', {}).get('total_feedbacks', 0)}\n"
                f"- NPS: {report_data['stages'].get('completed', {}).get('nps', {}).get('score', 0)}\n\n"
                f"Solicitudes Pendientes: {reminder_stats.get('total_pending', 0)}\n"
                f"- Críticas (>30 días): {reminder_stats.get('critical', 0)}\n"
                f"- Altas (15-30 días): {reminder_stats.get('high', 0)}\n"
                f"- Normales (7-14 días): {reminder_stats.get('normal', 0)}\n"
                f"- Recientes (<7 días): {reminder_stats.get('low', 0)}\n\n"
                f"Para ver el informe completo, acceda al Panel de Retroalimentación en el sistema.\n"
                f"Este es un mensaje automático del Sistema de Retroalimentación de Grupo huntRED®."
            )
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=True
            )
            
            logger.info(f"Informe semanal enviado a {', '.join(recipients)}")
        
        logger.info("Generación de informe semanal completada")
        
    except Exception as e:
        logger.error(f"Error en tarea de generación de informe semanal: {str(e)}")
