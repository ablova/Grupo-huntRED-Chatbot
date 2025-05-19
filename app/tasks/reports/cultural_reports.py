"""
Tareas asíncronas para la generación de reportes culturales.

Este módulo implementa las tareas de Celery para analizar datos de evaluaciones
culturales y generar reportes comprensivos optimizados para bajo uso de CPU.
"""

import logging
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Q, F, Sum
from django.db import transaction
from django.conf import settings
from celery import shared_task
from app.models_cultural import (
    CulturalAssessment, OrganizationalCulture, CulturalReport,
    CulturalDimension, CulturalValue
)
from app.utils.cache import cache_result
from app.utils.analysis import calculate_confidence_interval, detect_outliers
from app.utils.date import get_date_range

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def generate_cultural_report_task(self, organizational_culture_id, report_type='complete', created_by_id=None):
    """
    Genera un reporte de análisis cultural para una organización.
    
    Args:
        organizational_culture_id (int): ID de la cultura organizacional
        report_type (str): Tipo de reporte ('preliminary', 'complete', 'executive', 'team')
        created_by_id (int): ID del usuario que solicita el reporte
        
    Returns:
        int: ID del reporte generado, o None si hubo error
    """
    try:
        # Recuperar la cultura organizacional
        org_culture = OrganizationalCulture.objects.select_related(
            'organization', 'business_unit'
        ).get(id=organizational_culture_id)
        
        # Verificar si podemos generar el reporte según el tipo
        if report_type == 'complete' and org_culture.status != 'complete':
            logger.warning(
                f"No se puede generar reporte completo para {org_culture.organization.name}. "
                f"Estado actual: {org_culture.status}"
            )
            return None
            
        if report_type == 'preliminary' and org_culture.completion_percentage < 80:
            logger.warning(
                f"No se puede generar reporte preliminar para {org_culture.organization.name}. "
                f"Completado: {org_culture.completion_percentage}%"
            )
            return None
        
        # Crear el reporte en la base de datos
        with transaction.atomic():
            report = CulturalReport.objects.create(
                title=f"Análisis Cultural: {org_culture.organization.name} - {report_type.capitalize()}",
                organization=org_culture.organization,
                organizational_culture=org_culture,
                business_unit=org_culture.business_unit,
                report_type=report_type,
                status='generating',
                report_date=timezone.now(),
                created_by_id=created_by_id
            )
            
            # Iniciar procesamiento asíncrono de datos
            process_cultural_data_task.delay(report_id=report.id)
            
            logger.info(
                f"Iniciado reporte cultural {report_type} para {org_culture.organization.name}"
            )
            return report.id
            
    except OrganizationalCulture.DoesNotExist:
        logger.error(f"No se encontró la cultura organizacional con ID {organizational_culture_id}")
        return None
    except Exception as e:
        logger.exception(f"Error generando reporte cultural: {str(e)}")
        # Reintento con backoff exponencial
        self.retry(exc=e)
        return None


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def process_cultural_data_task(self, report_id):
    """
    Procesa los datos culturales para generar el reporte.
    
    Args:
        report_id (int): ID del reporte a procesar
        
    Returns:
        bool: True si se procesó correctamente, False en caso contrario
    """
    try:
        # Recuperar el reporte
        report = CulturalReport.objects.select_related(
            'organization', 'organizational_culture', 'business_unit'
        ).get(id=report_id)
        
        if report.status != 'generating':
            logger.warning(f"Reporte {report_id} no está en estado 'generating'")
            return False
            
        org_culture = report.organizational_culture
        organization = report.organization
        
        # Obtener evaluaciones relacionadas
        assessments = CulturalAssessment.objects.filter(
            organizational_culture=org_culture,
            status='completed'
        )
        
        participant_count = assessments.count()
        report.participant_count = participant_count
        
        if participant_count == 0:
            report.status = 'error'
            report.summary = "No hay participantes que hayan completado la evaluación"
            report.save()
            logger.error(f"No hay datos para generar el reporte {report_id}")
            return False
            
        # Recolectar y agregar datos
        dimensions_data = {}
        # Usar aggregate para optimizar consultas DB
        dimension_scores = {}
        overall_scores = {}
        
        # Análisis por departamento y equipo
        departments_analysis = {}
        teams_analysis = {}
        
        # Recolectar y procesar datos por dimensión cultural
        dimensions = CulturalDimension.objects.filter(
            business_unit=report.business_unit, 
            active=True
        )
        
        for dimension in dimensions:
            # Calcular puntaje promedio para esta dimensión
            assessment_scores = []
            for assessment in assessments:
                if 'dimensions_scores' in assessment.assessment_data:
                    score = assessment.dimensions_scores.get(str(dimension.id), 0)
                    assessment_scores.append(score)
            
            if assessment_scores:
                avg_score = sum(assessment_scores) / len(assessment_scores)
                confidence = calculate_confidence_interval(assessment_scores)
                outliers = detect_outliers(assessment_scores)
                
                dimensions_data[dimension.id] = {
                    'name': dimension.name,
                    'category': dimension.category,
                    'score': avg_score,
                    'confidence': confidence,
                    'outliers_percentage': len(outliers) / len(assessment_scores) * 100 if assessment_scores else 0,
                    'distribution': _calculate_distribution(assessment_scores)
                }
        
        # Procesamiento por departamentos y equipos si es relevante
        if report.report_type in ['complete', 'executive']:
            departments = {}
            for assessment in assessments:
                if assessment.department:
                    dept_id = assessment.department.id
                    if dept_id not in departments:
                        departments[dept_id] = {
                            'name': assessment.department.name,
                            'participants': 0,
                            'scores': {},
                            'risk_factors': []
                        }
                    
                    departments[dept_id]['participants'] += 1
                    
                    # Agregar puntajes por dimensión
                    for dim_id, score in assessment.dimensions_scores.items():
                        if dim_id not in departments[dept_id]['scores']:
                            departments[dept_id]['scores'][dim_id] = []
                        departments[dept_id]['scores'][dim_id].append(score)
                    
                    # Agregar factor de riesgo
                    if assessment.risk_factor is not None:
                        departments[dept_id]['risk_factors'].append(assessment.risk_factor)
            
            # Calcular promedios para departamentos
            for dept_id, data in departments.items():
                dept_summary = {
                    'name': data['name'],
                    'participants': data['participants'],
                    'dimensions': {},
                    'risk_factor': sum(data['risk_factors']) / len(data['risk_factors']) if data['risk_factors'] else None
                }
                
                for dim_id, scores in data['scores'].items():
                    if scores:
                        dept_summary['dimensions'][dim_id] = {
                            'score': sum(scores) / len(scores),
                            'confidence': calculate_confidence_interval(scores)
                        }
                
                departments_analysis[dept_id] = dept_summary
        
        # Generar insights culturales
        insights = _generate_cultural_insights(
            dimensions_data, 
            departments_analysis,
            participant_count, 
            organization.name
        )
        
        # Crear resumen ejecutivo
        executive_summary = _generate_executive_summary(
            dimensions_data,
            insights,
            participant_count,
            organization.name,
            report.report_type
        )
        
        # Guardar resultados en el reporte
        report.summary = executive_summary
        report.executive_summary = executive_summary[:500] + "..." if len(executive_summary) > 500 else executive_summary
        report.report_data = {
            'dimensions': dimensions_data,
            'departments': departments_analysis,
            'teams': teams_analysis,
            'overall_scores': overall_scores
        }
        report.cultural_insights = insights
        report.strengths = insights.get('strengths', [])
        report.areas_of_improvement = insights.get('improvement_areas', [])
        report.recommendations = insights.get('recommendations', [])
        report.action_items = insights.get('action_items', [])
        report.completion_percentage = org_culture.completion_percentage
        report.confidence_score = 95 if report.report_type == 'complete' else 85
        report.status = 'completed'
        report.completed_at = timezone.now()
        report.save()
        
        # Generar PDF del reporte
        generate_cultural_report_pdf_task.delay(report_id=report.id)
        
        logger.info(f"Procesado reporte cultural para {organization.name} completado")
        return True
            
    except CulturalReport.DoesNotExist:
        logger.error(f"No se encontró el reporte con ID {report_id}")
        return False
    except Exception as e:
        logger.exception(f"Error procesando datos culturales: {str(e)}")
        # Actualizar estado del reporte
        try:
            report = CulturalReport.objects.get(id=report_id)
            report.status = 'error'
            report.save()
        except:
            pass
        
        # Reintento con backoff exponencial
        self.retry(exc=e)
        return False


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def generate_cultural_report_pdf_task(self, report_id):
    """
    Genera un PDF del reporte cultural.
    
    Args:
        report_id (int): ID del reporte
        
    Returns:
        bool: True si se generó correctamente, False en caso contrario
    """
    try:
        from app.utils.pdf import generate_cultural_report_pdf
        
        # Recuperar el reporte
        report = CulturalReport.objects.select_related(
            'organization', 'organizational_culture'
        ).get(id=report_id)
        
        if report.status != 'completed':
            logger.warning(f"No se puede generar PDF para reporte {report_id} en estado {report.status}")
            return False
            
        # Generar el PDF
        pdf_file = generate_cultural_report_pdf(report)
        
        if pdf_file:
            # Actualizar el reporte con la ruta del PDF
            report.pdf_file = pdf_file
            report.save(update_fields=['pdf_file'])
            
            logger.info(f"PDF generado correctamente para reporte {report_id}")
            return True
        else:
            logger.error(f"Error generando PDF para reporte {report_id}")
            return False
            
    except CulturalReport.DoesNotExist:
        logger.error(f"No se encontró el reporte con ID {report_id}")
        return False
    except Exception as e:
        logger.exception(f"Error generando PDF: {str(e)}")
        # Reintento con backoff exponencial
        self.retry(exc=e)
        return False


def _calculate_distribution(scores):
    """Calcula la distribución de puntajes en rangos"""
    ranges = {
        '0-1': 0,
        '1-2': 0,
        '2-3': 0,
        '3-4': 0,
        '4-5': 0
    }
    
    for score in scores:
        if score < 1:
            ranges['0-1'] += 1
        elif score < 2:
            ranges['1-2'] += 1
        elif score < 3:
            ranges['2-3'] += 1
        elif score < 4:
            ranges['3-4'] += 1
        else:
            ranges['4-5'] += 1
    
    # Convertir a porcentajes
    total = len(scores)
    distribution = {}
    
    if total > 0:
        for range_name, count in ranges.items():
            distribution[range_name] = (count / total) * 100
    
    return distribution


def _generate_cultural_insights(dimensions_data, departments_analysis, participant_count, organization_name):
    """
    Genera insights culturales basados en los datos analizados.
    
    Args:
        dimensions_data (dict): Datos de dimensiones culturales
        departments_analysis (dict): Análisis por departamento
        participant_count (int): Cantidad de participantes
        organization_name (str): Nombre de la organización
        
    Returns:
        dict: Insights culturales generados
    """
    insights = {
        'highlights': [],
        'strengths': [],
        'improvement_areas': [],
        'recommendations': [],
        'action_items': [],
        'cultural_alignment': {}
    }
    
    # Generar fortalezas y áreas de mejora
    for dim_id, data in dimensions_data.items():
        score = data.get('score', 0)
        
        # Fortalezas (puntajes altos)
        if score >= 4.0:
            insights['strengths'].append({
                'dimension': data['name'],
                'score': score,
                'description': f"Alta puntuación en {data['name']} (Categoría: {data['category']})",
                'impact': "Alta alineación cultural en esta dimensión."
            })
        elif score >= 3.5:
            insights['strengths'].append({
                'dimension': data['name'],
                'score': score,
                'description': f"Buena puntuación en {data['name']} (Categoría: {data['category']})",
                'impact': "Buen nivel de alineación cultural."
            })
            
        # Áreas de mejora (puntajes bajos)
        if score < 2.5:
            insights['improvement_areas'].append({
                'dimension': data['name'],
                'score': score,
                'description': f"Baja puntuación en {data['name']} (Categoría: {data['category']})",
                'impact': "Potencial desalineación cultural."
            })
        elif score < 3.0:
            insights['improvement_areas'].append({
                'dimension': data['name'],
                'score': score,
                'description': f"Puntuación moderada-baja en {data['name']} (Categoría: {data['category']})",
                'impact': "Oportunidad de mejora cultural."
            })
    
    # Generar recomendaciones basadas en áreas de mejora
    for area in insights['improvement_areas']:
        dim_name = area['dimension']
        insights['recommendations'].append({
            'dimension': dim_name,
            'title': f"Fortalecer {dim_name}",
            'description': f"Implementar programas para mejorar la alineación en {dim_name}.",
            'priority': 'Alta' if area['score'] < 2.5 else 'Media'
        })
        
        # Generar acciones concretas
        insights['action_items'].append({
            'dimension': dim_name,
            'title': f"Workshop de {dim_name}",
            'description': f"Realizar talleres para identificar obstáculos y oportunidades en {dim_name}.",
            'responsible': "Recursos Humanos",
            'timeframe': "Próximos 30 días"
        })
    
    # Analizar variaciones entre departamentos si hay datos
    if departments_analysis:
        dept_variations = []
        for dept_id, data in departments_analysis.items():
            for dim_id, dim_data in data.get('dimensions', {}).items():
                # Comparar con promedio general
                if dim_id in dimensions_data:
                    general_score = dimensions_data[dim_id]['score']
                    dept_score = dim_data['score']
                    variation = dept_score - general_score
                    
                    if abs(variation) >= 0.7:  # Variación significativa
                        dept_variations.append({
                            'department': data['name'],
                            'dimension': dimensions_data[dim_id]['name'],
                            'variation': variation,
                            'general_score': general_score,
                            'department_score': dept_score
                        })
        
        # Añadir insights de variaciones departamentales
        if dept_variations:
            insights['departmental_variations'] = dept_variations
            insights['highlights'].append({
                'title': "Variaciones entre departamentos",
                'description': f"Se identificaron {len(dept_variations)} variaciones significativas entre departamentos.",
                'impact': "Alto - Indica posibles subculturas organizacionales"
            })
    
    return insights


def _generate_executive_summary(dimensions_data, insights, participant_count, organization_name, report_type):
    """
    Genera un resumen ejecutivo del reporte cultural.
    
    Args:
        dimensions_data (dict): Datos de dimensiones culturales
        insights (dict): Insights culturales
        participant_count (int): Cantidad de participantes
        organization_name (str): Nombre de la organización
        report_type (str): Tipo de reporte
        
    Returns:
        str: Resumen ejecutivo
    """
    # Calcular promedio global
    overall_score = 0
    if dimensions_data:
        scores_sum = sum(data.get('score', 0) for data in dimensions_data.values())
        overall_score = scores_sum / len(dimensions_data) if dimensions_data else 0
    
    # Determinar nivel cultural general
    if overall_score >= 4.0:
        cultural_level = "excelente"
    elif overall_score >= 3.5:
        cultural_level = "muy buena"
    elif overall_score >= 3.0:
        cultural_level = "buena"
    elif overall_score >= 2.5:
        cultural_level = "moderada"
    else:
        cultural_level = "en desarrollo"
    
    # Generar resumen
    summary = f"""
Resumen Ejecutivo - Análisis Cultural de {organization_name}

Este reporte {report_type} se basa en datos de {participant_count} participantes y evalúa la cultura organizacional 
a través de múltiples dimensiones.

Hallazgos Principales:
- La cultura organizacional general se clasifica como "{cultural_level}" con un puntaje promedio de {overall_score:.2f}/5.0
- Se identificaron {len(insights.get('strengths', []))} fortalezas y {len(insights.get('improvement_areas', []))} áreas de oportunidad.
"""

    # Añadir fortalezas principales
    if insights.get('strengths'):
        summary += "\nFortalezas destacadas:\n"
        for i, strength in enumerate(insights['strengths'][:3], 1):
            summary += f"- {strength['dimension']}: {strength['description']}\n"
    
    # Añadir áreas de mejora principales
    if insights.get('improvement_areas'):
        summary += "\nÁreas de mejora prioritarias:\n"
        for i, area in enumerate(insights['improvement_areas'][:3], 1):
            summary += f"- {area['dimension']}: {area['description']}\n"
    
    # Añadir recomendaciones clave
    if insights.get('recommendations'):
        summary += "\nRecomendaciones clave:\n"
        for i, rec in enumerate(insights['recommendations'][:3], 1):
            summary += f"- {rec['title']}: {rec['description']}\n"
    
    # Añadir nota según tipo de reporte
    if report_type == 'preliminary':
        summary += "\nNota: Este es un reporte preliminar basado en datos parciales. Un reporte completo estará disponible cuando se alcance el 100% de participación."
    
    return summary
