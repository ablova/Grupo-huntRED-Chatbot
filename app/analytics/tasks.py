from celery import shared_task
from django.core.cache import cache
from app.analytics.reports import AnalyticsEngine
import json

@shared_task
@shared_task
@shared_task
@shared_task
@shared_task
@shared_task
@shared_task
@shared_task
@shared_task
@shared_task
@shared_task
@shared_task
@shared_task
@shared_task
@shared_task
@shared_task
def generate_conversion_report():
    """
    Genera el reporte de conversión de oportunidades.
    """
    analytics = AnalyticsEngine()
    report = analytics.generate_opportunity_conversion_report()
    
    # Almacenar en cache
    cache.set('conversion_report', json.dumps(report), timeout=3600)
    return report

@shared_task
def generate_industry_trends():
    """
    Genera las tendencias por industria.
    """
    analytics = AnalyticsEngine()
    report = analytics.generate_industry_trends()
    
    # Almacenar en cache
    cache.set('industry_trends', json.dumps(report), timeout=3600)
    return report

@shared_task
def generate_location_heatmap():
    """
    Genera el heatmap de ubicaciones.
    """
    analytics = AnalyticsEngine()
    report = analytics.generate_location_heatmap()
    
    # Almacenar en cache
    cache.set('location_heatmap', json.dumps(report), timeout=3600)
    return report

@shared_task
def predict_conversion(opportunity_data):
    """
    Predice la probabilidad de conversión de una oportunidad.
    
    Args:
        opportunity_data: Datos de la oportunidad
        
    Returns:
        dict: Resultado de la predicción
    """
    analytics = AnalyticsEngine()
    opportunity = Opportunity(**opportunity_data)
    probability = analytics.predict_conversion_probability(opportunity)
    
    return {
        'probability': probability,
        'recommendation': analytics._get_recommendation(probability)
    }
