"""
Módulo de tareas de onboarding para Grupo huntRED.
Gestiona los procesos de incorporación de clientes y candidatos,
incluyendo generación de reportes y análisis de feedback.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
import os
import pandas as pd

from app.models import BusinessUnit, Person, Vacante, OnboardingProcess, ClientFeedback
from app.com.chatbot.workflow.amigro import (
    generate_candidate_summary_task, send_migration_docs_task,
    follow_up_migration_task
)
from app.tasks.base import with_retry

# Configuración de logging
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_client_feedback_task(self, feedback_id):
    """
    Procesa el feedback de un cliente y actualiza los modelos predictivos.
    
    Args:
        feedback_id: ID del feedback a procesar
        
    Returns:
        dict: Resultado del procesamiento
    """
    try:
        # Obtener el feedback
        feedback = ClientFeedback.objects.get(id=feedback_id)
        
        # Procesar el feedback (implementar lógica específica)
        logger.info(f"Procesando feedback del cliente {feedback.client.name}")
        
        # Actualizar estado
        feedback.processed = True
        feedback.processed_date = timezone.now()
        feedback.save()
        
        return {
            "status": "success",
            "message": f"Feedback {feedback_id} procesado correctamente"
        }
    except Exception as e:
        logger.error(f"Error procesando feedback {feedback_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=2)
def update_client_metrics_task(self, client_id=None):
    """
    Actualiza las métricas de todos los clientes o uno específico.
    
    Args:
        client_id: ID opcional del cliente
        
    Returns:
        dict: Resultado de la actualización
    """
    try:
        # Definir qué clientes actualizar
        clients_query = Person.objects.filter(is_client=True)
        if client_id:
            clients_query = clients_query.filter(id=client_id)
        
        clients = list(clients_query)
        updated = 0
        
        for client in clients:
            # Calcular métricas
            # Ejemplo: tiempo medio de respuesta, tasa de satisfacción, etc.
            
            # Actualizar cliente
            # client.metrics = {...}
            # client.save()
            
            updated += 1
        
        return {
            "status": "success",
            "message": f"Actualizadas métricas de {updated} clientes"
        }
    except Exception as e:
        logger.error(f"Error actualizando métricas de clientes: {str(e)}")
        raise self.retry(exc=e, countdown=300)

@shared_task(bind=True, max_retries=3)
def generate_client_feedback_reports_task(self, business_unit_id=None):
    """
    Genera reportes de feedback de clientes para una o todas las unidades de negocio.
    
    Args:
        business_unit_id: ID opcional de la unidad de negocio
        
    Returns:
        str: Mensaje con el resultado
    """
    try:
        # Obtener unidades de negocio
        if business_unit_id:
            business_units = [BusinessUnit.objects.get(id=business_unit_id)]
        else:
            business_units = BusinessUnit.objects.all()
        
        # Directorio para reportes
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports', 'client_feedback')
        os.makedirs(reports_dir, exist_ok=True)
        
        reports_generated = 0
        
        # Generar reportes por unidad de negocio
        for bu in business_units:
            # Obtener datos de feedback
            feedback_data = ClientFeedback.objects.filter(
                client__business_unit=bu,
                created_at__gte=timezone.now() - timedelta(days=30)
            ).order_by('-created_at')
            
            if not feedback_data:
                logger.info(f"No hay datos de feedback para {bu.name}")
                continue
            
            # Crear informe HTML
            report_path = os.path.join(reports_dir, f"feedback_report_{bu.name}_{datetime.now().strftime('%Y%m%d')}.html")
            
            with open(report_path, 'w') as f:
                f.write("<!DOCTYPE html>\n<html>\n<head>\n")
                f.write(f"<title>Informe de Feedback de Clientes - {bu.name}</title>\n")
                f.write("<style>\n")
                f.write("body { font-family: Arial, sans-serif; margin: 20px; }\n")
                f.write("h1 { color: #333366; }\n")
                f.write("table { border-collapse: collapse; width: 100%; }\n")
                f.write("th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }\n")
                f.write("tr:nth-child(even) { background-color: #f2f2f2; }\n")
                f.write("</style>\n")
                f.write("</head>\n<body>\n")
                
                f.write(f"<h1>Informe de Feedback de Clientes - {bu.name}</h1>\n")
                f.write(f"<p>Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>\n")
                
                # Tabla de resumen
                f.write("<h2>Resumen</h2>\n")
                f.write("<table>\n")
                f.write("<tr><th>Métrica</th><th>Valor</th></tr>\n")
                f.write(f"<tr><td>Total de feedback</td><td>{feedback_data.count()}</td></tr>\n")
                # Añadir más métricas según necesidad
                f.write("</table>\n")
                
                # Detalles de feedback
                f.write("<h2>Detalles de Feedback</h2>\n")
                f.write("<table>\n")
                f.write("<tr><th>Cliente</th><th>Fecha</th><th>Puntuación</th><th>Comentarios</th></tr>\n")
                
                for fb in feedback_data:
                    f.write(f"<tr>")
                    f.write(f"<td>{fb.client.first_name} {fb.client.last_name}</td>")
                    f.write(f"<td>{fb.created_at.strftime('%d/%m/%Y')}</td>")
                    f.write(f"<td>{fb.score or 'N/A'}</td>")
                    f.write(f"<td>{fb.comments or 'Sin comentarios'}</td>")
                    f.write(f"</tr>")
                
                f.write("</table>\n")
                f.write("</body>\n</html>")
            
            reports_generated += 1
            logger.info(f"Generado reporte de feedback para {bu.name}: {report_path}")
        
        return f"Generados {reports_generated} reportes de feedback de clientes"
    
    except Exception as e:
        logger.error(f"Error generando reportes de feedback: {str(e)}")
        raise self.retry(exc=e, countdown=300)

@shared_task(bind=True, max_retries=3)
def process_onboarding_ml_data_task(self):
    """
    Procesa datos de onboarding para machine learning, incluyendo actualización de modelos
    predictivos de satisfacción y retención.
    
    Returns:
        str: Resultado del procesamiento
    """
    try:
        # Implementar la lógica para procesar datos de onboarding
        from app.ml.onboarding_processor import OnboardingMLProcessor
        
        processor = OnboardingMLProcessor()
        results = asyncio.run(processor.process_all_onboarding_data())
        
        return f"Datos de onboarding procesados: {results}"
    except Exception as e:
        logger.error(f"Error procesando datos de onboarding para ML: {str(e)}")
        raise self.retry(exc=e, countdown=300)

@shared_task(bind=True, max_retries=3)
def generate_employee_satisfaction_reports_task(self, business_unit_id=None):
    """
    Genera reportes de satisfacción de empleados contratados a través de la plataforma.
    
    Args:
        business_unit_id: ID opcional de la unidad de negocio
        
    Returns:
        str: Mensaje con el resultado
    """
    try:
        # Definir período de reporte (últimos 90 días)
        cutoff_date = timezone.now() - timedelta(days=90)
        
        # Obtener empresas para las que generar reportes
        if business_unit_id:
            companies = [BusinessUnit.objects.get(id=business_unit_id)]
        else:
            # Filtrar solo empresas que han contratado candidatos
            companies = BusinessUnit.objects.filter(
                vacante__application__status='HIRED',
                vacante__application__status_changed_at__gte=cutoff_date
            ).distinct()
        
        # Directorio para reportes
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports', 'employee_satisfaction')
        os.makedirs(reports_dir, exist_ok=True)
        
        reports_generated = 0
        
        # Generar reportes por empresa
        for company in companies:
            # Obtener procesos de onboarding completados
            processes = OnboardingProcess.objects.filter(
                vacancy__business_unit=company,
                status='COMPLETED',
                hire_date__gte=cutoff_date
            ).select_related('person', 'vacancy')
            
            if not processes:
                logger.info(f"No hay procesos de onboarding para {company.name}")
                continue
            
            # Crear informe HTML
            report_path = os.path.join(reports_dir, f"satisfaction_report_{company.name}_{datetime.now().strftime('%Y%m%d')}.html")
            
            with open(report_path, 'w') as f:
                f.write("<!DOCTYPE html>\n<html>\n<head>\n")
                f.write(f"<title>Informe de Satisfacción de Empleados - {company.name}</title>\n")
                f.write("<style>\n")
                f.write("body { font-family: Arial, sans-serif; margin: 20px; }\n")
                f.write("h1 { color: #333366; }\n")
                f.write("table { border-collapse: collapse; width: 100%; }\n")
                f.write("th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }\n")
                f.write("tr:nth-child(even) { background-color: #f2f2f2; }\n")
                f.write("</style>\n")
                f.write("</head>\n<body>\n")
                
                f.write(f"<h1>Informe de Satisfacción de Empleados - {company.name}</h1>\n")
                f.write(f"<p>Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>\n")
                
                # Detalles de empleados
                f.write("<h2>Detalles de Empleados</h2>\n")
                f.write("<table>\n")
                f.write("<tr><th>Empleado</th><th>Posición</th><th>Días desde contratación</th><th>Satisfacción</th></tr>\n")
                
                for process in processes:
                    days_since_hire = (timezone.now().date() - process.hire_date.date()).days
                    satisfaction = process.get_satisfaction_score() or "N/A"
                    satisfaction_display = f"{satisfaction}/10" if satisfaction != "N/A" else "N/A"
                    
                    f.write(f"<tr>")
                    f.write(f"<td>{process.person.first_name} {process.person.last_name}</td>")
                    f.write(f"<td>{process.vacancy.title}</td>")
                    f.write(f"<td>{days_since_hire}</td>")
                    f.write(f"<td>{satisfaction_display}</td>")
                    f.write(f"</tr>")
                
                f.write("</table>")
                
                # Más contenido aquí según necesidad
                
                f.write("</body>\n</html>")
            
            reports_generated += 1
            logger.info(f"Generado reporte de satisfacción para {company.name}: {report_path}")
        
        return f"Generados {reports_generated} reportes de satisfacción"
    
    except Exception as e:
        logger.error(f"Error generando reportes de satisfacción: {str(e)}")
        raise self.retry(exc=e, countdown=300)
