"""
Módulo de tareas de generación de reportes para Grupo huntRED.
Genera informes periódicos, analíticas y dashboards para diferentes unidades de negocio.
Optimizado para bajo uso de CPU y operaciones asíncronas.
"""

import logging
import asyncio
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum

from app.models import (
    BusinessUnit, Person, Vacante, Interview, Application,
    RegistroScraping, DominioScraping, OnboardingProcess
)
from app.ats.tasks.base import with_retry

# Configuración de logging
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def generate_weekly_report_task(self, business_unit_id=None):
    """
    Genera reportes semanales para una o todas las unidades de negocio.
    
    Args:
        business_unit_id: ID opcional de la unidad de negocio
        
    Returns:
        dict: Resultado de la generación
    """
    try:
        # Definir período del reporte
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        
        # Obtener unidades de negocio
        if business_unit_id:
            business_units = [BusinessUnit.objects.get(id=business_unit_id)]
        else:
            business_units = BusinessUnit.objects.filter(active=True)
        
        # Directorio para reportes
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports', 'weekly')
        os.makedirs(reports_dir, exist_ok=True)
        
        reports_generated = 0
        
        # Generar reportes por unidad de negocio
        for bu in business_units:
            # Recopilar datos
            new_vacancies = Vacante.objects.filter(
                business_unit=bu,
                creation_date__gte=start_date,
                creation_date__lte=end_date
            ).count()
            
            new_candidates = Person.objects.filter(
                business_unit=bu,
                creation_date__gte=start_date,
                creation_date__lte=end_date,
                is_client=False
            ).count()
            
            interviews = Interview.objects.filter(
                vacancy__business_unit=bu,
                date__gte=start_date,
                date__lte=end_date
            ).count()
            
            applications = Application.objects.filter(
                vacancy__business_unit=bu,
                created_at__gte=start_date,
                created_at__lte=end_date
            ).count()
            
            hires = Application.objects.filter(
                vacancy__business_unit=bu,
                status='HIRED',
                status_changed_at__gte=start_date,
                status_changed_at__lte=end_date
            ).count()
            
            # Crear reporte HTML
            report_filename = f"weekly_report_{bu.name}_{end_date.strftime('%Y%m%d')}.html"
            report_path = os.path.join(reports_dir, report_filename)
            
            with open(report_path, 'w') as f:
                f.write("<!DOCTYPE html>\n<html>\n<head>\n")
                f.write(f"<title>Reporte Semanal - {bu.name}</title>\n")
                f.write("<style>\n")
                f.write("body { font-family: Arial, sans-serif; margin: 20px; }\n")
                f.write("h1 { color: #333366; }\n")
                f.write("table { border-collapse: collapse; width: 100%; }\n")
                f.write("th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }\n")
                f.write("tr:nth-child(even) { background-color: #f2f2f2; }\n")
                f.write(".metrics { display: flex; flex-wrap: wrap; }\n")
                f.write(".metric-box { border: 1px solid #ddd; padding: 15px; margin: 10px; flex: 1; min-width: 200px; text-align: center; }\n")
                f.write(".metric-value { font-size: 24px; font-weight: bold; color: #333366; }\n")
                f.write(".metric-label { font-size: 14px; color: #666; }\n")
                f.write("</style>\n")
                f.write("</head>\n<body>\n")
                
                f.write(f"<h1>Reporte Semanal - {bu.name}</h1>\n")
                f.write(f"<p>Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}</p>\n")
                
                # Métricas principales
                f.write("<div class='metrics'>\n")
                
                f.write("<div class='metric-box'>\n")
                f.write(f"<div class='metric-value'>{new_vacancies}</div>\n")
                f.write("<div class='metric-label'>Nuevas Vacantes</div>\n")
                f.write("</div>\n")
                
                f.write("<div class='metric-box'>\n")
                f.write(f"<div class='metric-value'>{new_candidates}</div>\n")
                f.write("<div class='metric-label'>Nuevos Candidatos</div>\n")
                f.write("</div>\n")
                
                f.write("<div class='metric-box'>\n")
                f.write(f"<div class='metric-value'>{interviews}</div>\n")
                f.write("<div class='metric-label'>Entrevistas</div>\n")
                f.write("</div>\n")
                
                f.write("<div class='metric-box'>\n")
                f.write(f"<div class='metric-value'>{applications}</div>\n")
                f.write("<div class='metric-label'>Aplicaciones</div>\n")
                f.write("</div>\n")
                
                f.write("<div class='metric-box'>\n")
                f.write(f"<div class='metric-value'>{hires}</div>\n")
                f.write("<div class='metric-label'>Contrataciones</div>\n")
                f.write("</div>\n")
                
                f.write("</div>\n")  # Fin de métricas
                
                # Más secciones según necesidad...
                
                f.write("</body>\n</html>")
            
            reports_generated += 1
            logger.info(f"Generado reporte semanal para {bu.name}: {report_path}")
            
            # También podríamos generar una versión PDF si es necesario
        
        return {
            "status": "success",
            "reports_generated": reports_generated,
            "period": f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        }
    except Exception as e:
        logger.error(f"Error generando reportes semanales: {str(e)}")
        raise self.retry(exc=e, countdown=300)

@shared_task(bind=True, max_retries=2)
def generate_scraping_efficiency_report_task(self):
    """
    Genera un reporte de eficiencia del scraping.
    
    Returns:
        dict: Resultado de la generación
    """
    try:
        # Definir período del reporte (último mes)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Obtener datos de scraping
        scraping_records = RegistroScraping.objects.filter(
            fecha_inicio__gte=start_date,
            fecha_inicio__lte=end_date
        ).select_related('dominio')
        
        if not scraping_records:
            logger.warning("No hay registros de scraping en el último mes")
            return {
                "status": "warning",
                "message": "No hay datos de scraping para generar el reporte"
            }
        
        # Directorio para reportes
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports', 'scraping')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Crear DataFrame con datos
        data = []
        for record in scraping_records:
            duration = None
            if record.fecha_fin and record.fecha_inicio:
                duration = (record.fecha_fin - record.fecha_inicio).total_seconds()
            
            data.append({
                'domain': record.dominio.dominio,
                'date': record.fecha_inicio,
                'status': record.estado,
                'duration': duration,
                'vacancies_found': record.vacantes_encontradas or 0,
                'vacancies_new': record.vacantes_nuevas or 0,
                'vacancies_updated': record.vacantes_actualizadas or 0
            })
        
        df = pd.DataFrame(data)
        
        # Calcular métricas
        total_records = len(df)
        successful_records = df[df['status'] == 'COMPLETADO'].shape[0]
        success_rate = (successful_records / total_records * 100) if total_records > 0 else 0
        
        total_vacancies = df['vacancies_found'].sum()
        new_vacancies = df['vacancies_new'].sum()
        updated_vacancies = df['vacancies_updated'].sum()
        
        avg_duration = df['duration'].mean()
        
        # Dominio con mejor rendimiento
        domain_stats = df.groupby('domain').agg({
            'vacancies_new': 'sum',
            'vacancies_found': 'sum',
            'duration': 'mean'
        }).reset_index()
        
        if not domain_stats.empty:
            domain_stats['efficiency'] = domain_stats['vacancies_new'] / domain_stats['duration']
            top_domain = domain_stats.sort_values('efficiency', ascending=False).iloc[0]
        else:
            top_domain = None
        
        # Crear reporte HTML
        report_filename = f"scraping_efficiency_report_{end_date.strftime('%Y%m%d')}.html"
        report_path = os.path.join(reports_dir, report_filename)
        
        with open(report_path, 'w') as f:
            f.write("<!DOCTYPE html>\n<html>\n<head>\n")
            f.write("<title>Reporte de Eficiencia de Scraping</title>\n")
            f.write("<style>\n")
            f.write("body { font-family: Arial, sans-serif; margin: 20px; }\n")
            f.write("h1 { color: #333366; }\n")
            f.write("table { border-collapse: collapse; width: 100%; }\n")
            f.write("th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }\n")
            f.write("tr:nth-child(even) { background-color: #f2f2f2; }\n")
            f.write(".metrics { display: flex; flex-wrap: wrap; }\n")
            f.write(".metric-box { border: 1px solid #ddd; padding: 15px; margin: 10px; flex: 1; min-width: 200px; text-align: center; }\n")
            f.write(".metric-value { font-size: 24px; font-weight: bold; color: #333366; }\n")
            f.write(".metric-label { font-size: 14px; color: #666; }\n")
            f.write("</style>\n")
            f.write("</head>\n<body>\n")
            
            f.write("<h1>Reporte de Eficiencia de Scraping</h1>\n")
            f.write(f"<p>Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}</p>\n")
            
            # Métricas principales
            f.write("<div class='metrics'>\n")
            
            f.write("<div class='metric-box'>\n")
            f.write(f"<div class='metric-value'>{total_records}</div>\n")
            f.write("<div class='metric-label'>Ejecuciones Totales</div>\n")
            f.write("</div>\n")
            
            f.write("<div class='metric-box'>\n")
            f.write(f"<div class='metric-value'>{success_rate:.1f}%</div>\n")
            f.write("<div class='metric-label'>Tasa de Éxito</div>\n")
            f.write("</div>\n")
            
            f.write("<div class='metric-box'>\n")
            f.write(f"<div class='metric-value'>{total_vacancies}</div>\n")
            f.write("<div class='metric-label'>Vacantes Encontradas</div>\n")
            f.write("</div>\n")
            
            f.write("<div class='metric-box'>\n")
            f.write(f"<div class='metric-value'>{new_vacancies}</div>\n")
            f.write("<div class='metric-label'>Vacantes Nuevas</div>\n")
            f.write("</div>\n")
            
            if avg_duration:
                f.write("<div class='metric-box'>\n")
                f.write(f"<div class='metric-value'>{avg_duration/60:.1f} min</div>\n")
                f.write("<div class='metric-label'>Duración Promedio</div>\n")
                f.write("</div>\n")
            
            f.write("</div>\n")  # Fin de métricas
            
            # Dominio más eficiente
            if top_domain is not None:
                f.write("<h2>Dominio Más Eficiente</h2>\n")
                f.write("<table>\n")
                f.write("<tr><th>Dominio</th><th>Vacantes Nuevas</th><th>Duración Promedio (min)</th><th>Eficiencia</th></tr>\n")
                f.write(f"<tr>")
                f.write(f"<td>{top_domain['domain']}</td>")
                f.write(f"<td>{top_domain['vacancies_new']}</td>")
                f.write(f"<td>{top_domain['duration']/60:.1f}</td>")
                f.write(f"<td>{top_domain['efficiency']*60:.2f} vacantes/min</td>")
                f.write(f"</tr>")
                f.write("</table>\n")
            
            # Tabla de dominios
            f.write("<h2>Rendimiento por Dominio</h2>\n")
            f.write("<table>\n")
            f.write("<tr><th>Dominio</th><th>Vacantes Encontradas</th><th>Vacantes Nuevas</th><th>Duración Promedio (min)</th></tr>\n")
            
            for _, row in domain_stats.iterrows():
                f.write(f"<tr>")
                f.write(f"<td>{row['domain']}</td>")
                f.write(f"<td>{row['vacancies_found']}</td>")
                f.write(f"<td>{row['vacancies_new']}</td>")
                f.write(f"<td>{row['duration']/60:.1f}</td>")
                f.write(f"</tr>")
            
            f.write("</table>\n")
            
            f.write("</body>\n</html>")
        
        logger.info(f"Generado reporte de eficiencia de scraping: {report_path}")
        
        return {
            "status": "success",
            "report_path": report_path,
            "metrics": {
                "total_records": total_records,
                "success_rate": success_rate,
                "total_vacancies": total_vacancies,
                "new_vacancies": new_vacancies
            }
        }
    except Exception as e:
        logger.error(f"Error generando reporte de eficiencia de scraping: {str(e)}")
        raise self.retry(exc=e, countdown=300)

@shared_task(bind=True, max_retries=2)
def generate_conversion_funnel_report_task(self, business_unit_id=None, days=30):
    """
    Genera un reporte del embudo de conversión para una o todas las unidades de negocio.
    
    Args:
        business_unit_id: ID opcional de la unidad de negocio
        days: Número de días a incluir en el reporte
        
    Returns:
        dict: Resultado de la generación
    """
    try:
        # Definir período del reporte
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Obtener unidades de negocio
        if business_unit_id:
            business_units = [BusinessUnit.objects.get(id=business_unit_id)]
        else:
            business_units = BusinessUnit.objects.filter(active=True)
        
        # Directorio para reportes
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports', 'funnels')
        os.makedirs(reports_dir, exist_ok=True)
        
        reports_generated = 0
        
        # Generar reportes por unidad de negocio
        for bu in business_units:
            # Recopilar datos para el embudo
            vacancies = Vacante.objects.filter(
                business_unit=bu,
                creation_date__gte=start_date,
                creation_date__lte=end_date
            ).count()
            
            views = Vacante.objects.filter(
                business_unit=bu,
                creation_date__gte=start_date,
                creation_date__lte=end_date,
                views__gt=0
            ).count()
            
            applications = Application.objects.filter(
                vacancy__business_unit=bu,
                created_at__gte=start_date,
                created_at__lte=end_date
            ).count()
            
            interviews = Interview.objects.filter(
                vacancy__business_unit=bu,
                date__gte=start_date,
                date__lte=end_date
            ).count()
            
            hires = Application.objects.filter(
                vacancy__business_unit=bu,
                status='HIRED',
                status_changed_at__gte=start_date,
                status_changed_at__lte=end_date
            ).count()
            
            # Conversiones entre etapas
            view_to_app_rate = (applications / views * 100) if views > 0 else 0
            app_to_interview_rate = (interviews / applications * 100) if applications > 0 else 0
            interview_to_hire_rate = (hires / interviews * 100) if interviews > 0 else 0
            
            # Crear reporte HTML
            report_filename = f"funnel_report_{bu.name}_{end_date.strftime('%Y%m%d')}.html"
            report_path = os.path.join(reports_dir, report_filename)
            
            with open(report_path, 'w') as f:
                f.write("<!DOCTYPE html>\n<html>\n<head>\n")
                f.write(f"<title>Embudo de Conversión - {bu.name}</title>\n")
                f.write("<style>\n")
                f.write("body { font-family: Arial, sans-serif; margin: 20px; }\n")
                f.write("h1 { color: #333366; }\n")
                f.write(".funnel { margin: 30px 0; text-align: center; }\n")
                f.write(".funnel-step { margin: 10px auto; background-color: #4472C4; color: white; padding: 15px; }\n")
                f.write(".funnel-step:nth-child(1) { width: 90%; }\n")
                f.write(".funnel-step:nth-child(2) { width: 70%; }\n")
                f.write(".funnel-step:nth-child(3) { width: 50%; }\n")
                f.write(".funnel-step:nth-child(4) { width: 30%; }\n")
                f.write(".funnel-step:nth-child(5) { width: 20%; }\n")
                f.write(".funnel-number { font-size: 24px; font-weight: bold; }\n")
                f.write(".conversion-rate { font-size: 14px; color: #666; margin-top: 5px; }\n")
                f.write("</style>\n")
                f.write("</head>\n<body>\n")
                
                f.write(f"<h1>Embudo de Conversión - {bu.name}</h1>\n")
                f.write(f"<p>Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}</p>\n")
                
                # Embudo visual
                f.write("<div class='funnel'>\n")
                
                f.write("<div class='funnel-step'>\n")
                f.write("<div>Vacantes Publicadas</div>\n")
                f.write(f"<div class='funnel-number'>{vacancies}</div>\n")
                f.write("</div>\n")
                
                f.write("<div class='funnel-step'>\n")
                f.write("<div>Vacantes Vistas</div>\n")
                f.write(f"<div class='funnel-number'>{views}</div>\n")
                f.write("</div>\n")
                
                f.write("<div class='funnel-step'>\n")
                f.write("<div>Aplicaciones</div>\n")
                f.write(f"<div class='funnel-number'>{applications}</div>\n")
                f.write(f"<div class='conversion-rate'>Conversión: {view_to_app_rate:.1f}%</div>\n")
                f.write("</div>\n")
                
                f.write("<div class='funnel-step'>\n")
                f.write("<div>Entrevistas</div>\n")
                f.write(f"<div class='funnel-number'>{interviews}</div>\n")
                f.write(f"<div class='conversion-rate'>Conversión: {app_to_interview_rate:.1f}%</div>\n")
                f.write("</div>\n")
                
                f.write("<div class='funnel-step'>\n")
                f.write("<div>Contrataciones</div>\n")
                f.write(f"<div class='funnel-number'>{hires}</div>\n")
                f.write(f"<div class='conversion-rate'>Conversión: {interview_to_hire_rate:.1f}%</div>\n")
                f.write("</div>\n")
                
                f.write("</div>\n")  # Fin del embudo
                
                f.write("</body>\n</html>")
            
            reports_generated += 1
            logger.info(f"Generado reporte de embudo para {bu.name}: {report_path}")
        
        return {
            "status": "success",
            "reports_generated": reports_generated,
            "period": f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        }
    except Exception as e:
        logger.error(f"Error generando reportes de embudo: {str(e)}")
        raise self.retry(exc=e, countdown=300)
