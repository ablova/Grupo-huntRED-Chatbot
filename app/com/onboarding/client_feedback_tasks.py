"""
Tareas de Celery para el módulo de feedback de clientes.

Este módulo define las tareas programadas para el envío de encuestas
de satisfacción a clientes y la generación de reportes periódicos.
"""

import logging
import asyncio
from datetime import datetime, timedelta

from celery import shared_task
from django.utils import timezone
from django.db.models import Q

from app.models_client_feedback import ClientFeedback, ClientFeedbackSchedule
from app.com.onboarding.client_feedback_controller import ClientFeedbackController

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_client_feedback_survey_task(self, feedback_id):
    """
    Envía una encuesta de satisfacción a un cliente.
    
    Args:
        feedback_id (int): ID del feedback a enviar
    """
    try:
        # Enviar encuesta
        result = asyncio.run(ClientFeedbackController.send_feedback_survey(feedback_id))
        
        if not result.get('success'):
            raise ValueError(f"Error enviando encuesta: {result.get('error')}")
        
        return f"Encuesta enviada correctamente: {feedback_id}"
        
    except Exception as e:
        logger.error(f"Error enviando encuesta a cliente: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)  # Reintentar en 5 minutos

@shared_task(bind=True)
def check_pending_client_feedback_task(self):
    """
    Verifica encuestas pendientes de envío según las programaciones.
    """
    try:
        # Verificar encuestas pendientes
        result = asyncio.run(ClientFeedbackController.check_pending_feedback())
        
        if not result.get('success'):
            raise ValueError(f"Error verificando encuestas pendientes: {result.get('error')}")
        
        # Programar envío de encuestas pendientes
        count = 0
        for feedback in result.get('pending_feedback', []):
            feedback_id = feedback.get('feedback_id')
            if feedback_id:
                send_client_feedback_survey_task.delay(feedback_id)
                count += 1
                logger.info(f"Programado envío de encuesta {feedback_id} a cliente {feedback.get('empresa_name')}")
        
        return f"Programado envío de {count} encuestas pendientes"
        
    except Exception as e:
        logger.error(f"Error verificando encuestas pendientes para clientes: {str(e)}")
        return f"Error: {str(e)}"

@shared_task(bind=True)
def generate_client_feedback_reports_task(self):
    """
    Genera reportes mensuales de satisfacción de clientes por Business Unit.
    """
    from app.models import BusinessUnit
    import os
    from django.conf import settings
    
    try:
        # Obtener todas las Business Units activas
        business_units = BusinessUnit.objects.filter(is_active=True)
        reports_generated = 0
        
        for bu in business_units:
            # Verificar si hay encuestas para esta BU
            feedback_count = ClientFeedback.objects.filter(
                business_unit=bu,
                status='COMPLETED'
            ).count()
            
            if feedback_count == 0:
                continue
            
            # Generar reporte para la BU
            report_data = asyncio.run(
                ClientFeedbackController.generate_bu_satisfaction_report(bu.id)
            )
            
            # Crear directorio si no existe
            reports_dir = os.path.join(settings.MEDIA_ROOT, 'client_feedback_reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            # Guardar reporte en formato HTML
            current_month = timezone.now().strftime('%B_%Y').lower()
            report_filename = f"{bu.code.lower()}_client_satisfaction_{current_month}.html"
            report_path = os.path.join(reports_dir, report_filename)
            
            # Renderizar HTML
            from django.template.loader import render_to_string
            context = {
                'report': report_data,
                'year': datetime.now().year,
                'logo_url': f"{settings.STATIC_URL}images/logo.png"
            }
            html_content = render_to_string('onboarding/client_satisfaction_report.html', context)
            
            # Guardar reporte
            with open(report_path, 'w') as f:
                f.write(html_content)
            
            reports_generated += 1
            logger.info(f"Generado reporte de satisfacción de clientes para BU {bu.name}: {report_path}")
        
        return f"Generados {reports_generated} reportes de satisfacción de clientes"
        
    except Exception as e:
        logger.error(f"Error generando reportes de satisfacción de clientes: {str(e)}")
        return f"Error: {str(e)}"

@shared_task(bind=True)
def analyze_client_feedback_trends_task(self):
    """
    Analiza tendencias en el feedback de clientes e identifica patrones.
    """
    from app.models import BusinessUnit
    from app.ml.onboarding_processor import OnboardingMLProcessor
    
    try:
        # Procesar datos de feedback para ML
        ml_processor = OnboardingMLProcessor()
        results = asyncio.run(ml_processor.analyze_client_feedback_trends())
        
        return f"Análisis de tendencias de feedback completado: {results}"
        
    except Exception as e:
        logger.error(f"Error analizando tendencias de feedback: {str(e)}")
        return f"Error: {str(e)}"
