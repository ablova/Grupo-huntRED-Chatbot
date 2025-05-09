from django.db import models
from django.db.models import Count, Avg, Sum
from app.models import Opportunity, Contract, Vacancy, Person
from datetime import datetime, timedelta
import pandas as pd

class AnalyticsEngine:
    def __init__(self):
        self._initialize_cache()
        
    def _initialize_cache(self):
        """
        Inicializa el sistema de caché.
        """
        from django.core.cache import cache
        self.cache = cache
        
    def generate_opportunity_conversion_report(self):
        """
        Genera un reporte de conversión de oportunidades.
        
        Returns:
            dict: Reporte con métricas de conversión
        """
        # Obtener oportunidades scrapeadas
        scraped_opportunities = Opportunity.objects.filter(
            source='scraping',
            status='active'
        )
        
        # Obtener oportunidades convertidas
        converted_opportunities = Contract.objects.filter(
            status='SIGNED'
        ).values('proposal__opportunity')
        
        # Calcular métricas
        conversion_rate = len(converted_opportunities) / len(scraped_opportunities)
        
        return {
            'total_scraped': len(scraped_opportunities),
            'total_converted': len(converted_opportunities),
            'conversion_rate': conversion_rate,
            'average_conversion_time': self._calculate_average_conversion_time()
        }
        
    def _calculate_average_conversion_time(self):
        """
        Calcula el tiempo promedio de conversión.
        
        Returns:
            float: Tiempo promedio en días
        """
        from django.db.models import F
        
        # Obtener tiempos de conversión
        conversions = Contract.objects.filter(
            status='SIGNED'
        ).annotate(
            conversion_time=models.ExpressionWrapper(
                F('created_at') - F('proposal__created_at'),
                output_field=models.DurationField()
            )
        )
        
        # Calcular promedio
        total_time = sum(c.conversion_time.total_seconds() for c in conversions)
        avg_time = total_time / len(conversions) if conversions else 0
        
        return avg_time / (24 * 60 * 60)  # Convertir a días
        
    def generate_industry_trends(self):
        """
        Genera tendencias por industria.
        
        Returns:
            dict: Tendencias por industria
        """
        # Obtener oportunidades por industria
        industry_data = Opportunity.objects.values('industry')\
            .annotate(
                count=Count('id'),
                avg_salary=Avg('vacancies__salary')
            )
            
        return {
            'by_industry': list(industry_data),
            'total_opportunities': Opportunity.objects.count(),
            'total_vacancies': Vacancy.objects.count()
        }
        
    def generate_location_heatmap(self):
        """
        Genera un heatmap de ubicaciones.
        
        Returns:
            dict: Datos para heatmap
        """
        # Obtener ubicaciones
        location_data = Opportunity.objects.values('location')\
            .annotate(
                count=Count('id'),
                avg_salary=Avg('vacancies__salary')
            )
            
        return {
            'locations': list(location_data),
            'total_opportunities': Opportunity.objects.count()
        }
        
    def predict_conversion_probability(self, opportunity):
        """
        Predice la probabilidad de conversión de una oportunidad.
        
        Args:
            opportunity: Instancia de Opportunity
            
        Returns:
            float: Probabilidad de conversión (0-1)
        """
        # Características relevantes
        features = {
            'industry': opportunity.industry,
            'seniority_level': opportunity.seniority_level,
            'location': opportunity.location,
            'salary_range': opportunity.salary_range,
            'skills_required': len(opportunity.skills_required)
        }
        
        # Usar modelo ML entrenado
        return self._predict_with_ml_model(features)
        
    def _predict_with_ml_model(self, features):
        """
        Realiza la predicción usando el modelo ML.
        
        Args:
            features: Diccionario con características
            
        Returns:
            float: Probabilidad predicha
        """
        # Simulación de predicción (en producción usaría un modelo real)
        base_prob = 0.5
        
        # Ajustar probabilidad basada en características
        if features['industry'] in ['tech', 'finance']:
            base_prob += 0.1
        if features['seniority_level'] in ['senior', 'lead']:
            base_prob += 0.1
        if features['skills_required'] > 5:
            base_prob += 0.1
            
        return min(base_prob, 1.0)
