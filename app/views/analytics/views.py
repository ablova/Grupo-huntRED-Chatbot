# /home/pablo/app/views/analytics/views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from django.shortcuts import render
from django.http import JsonResponse
from app.analytics.reports import AnalyticsEngine
import json

class AnalyticsDashboardView:
    def get(self, request):
        """
        Muestra el dashboard de analytics.
        
        Args:
            request: HttpRequest
            
        Returns:
            HttpResponse: Renderizado del dashboard
        """
        # Inicializar engine de analytics
        analytics = AnalyticsEngine()
        
        # Generar reportes
        conversion_report = analytics.generate_opportunity_conversion_report()
        industry_trends = analytics.generate_industry_trends()
        location_heatmap = analytics.generate_location_heatmap()
        
        # Preparar datos para gráficos
        charts_data = {
            'conversion_rate': conversion_report['conversion_rate'],
            'industry_trends': self._prepare_industry_data(industry_trends),
            'location_heatmap': self._prepare_location_data(location_heatmap)
        }
        
        return render(request, 'analytics/dashboard.html', {
            'reports': {
                'conversion': conversion_report,
                'industry': industry_trends,
                'location': location_heatmap
            },
            'charts_data': charts_data
        })
        
    def _prepare_industry_data(self, industry_data):
        """
        Prepara los datos de industria para el gráfico.
        
        Args:
            industry_data: Datos de industria
            
        Returns:
            dict: Datos formateados para el gráfico
        """
        return {
            'labels': [d['industry'] for d in industry_data['by_industry']],
            'data': [d['count'] for d in industry_data['by_industry']],
            'avg_salaries': [float(d['avg_salary']) for d in industry_data['by_industry']]
        }
        
    def _prepare_location_data(self, location_data):
        """
        Prepara los datos de ubicación para el heatmap.
        
        Args:
            location_data: Datos de ubicación
            
        Returns:
            dict: Datos formateados para el heatmap
        """
        return {
            'locations': [d['location'] for d in location_data['locations']],
            'counts': [d['count'] for d in location_data['locations']],
            'avg_salaries': [float(d['avg_salary']) for d in location_data['locations']]
        }
        
    def predict_conversion(self, request):
        """
        Predice la probabilidad de conversión de una oportunidad.
        
        Args:
            request: HttpRequest con los datos de la oportunidad
            
        Returns:
            JsonResponse: Probabilidad de conversión
        """
        if request.method == 'POST':
            opportunity_data = json.loads(request.body)
            
            # Crear instancia simulada de Opportunity
            from app.models import Opportunity
            opportunity = Opportunity(**opportunity_data)
            
            # Obtener predicción
            analytics = AnalyticsEngine()
            probability = analytics.predict_conversion_probability(opportunity)
            
            return JsonResponse({
                'probability': probability,
                'recommendation': self._get_recommendation(probability)
            })
            
    def _get_recommendation(self, probability):
        """
        Genera una recomendación basada en la probabilidad.
        
        Args:
            probability: Probabilidad de conversión
            
        Returns:
            str: Recomendación
        """
        if probability > 0.8:
            return "Alta probabilidad de éxito. Proceder con la conversión."
        elif probability > 0.5:
            return "Buena probabilidad. Considerar la conversión."
        else:
            return "Baja probabilidad. Revisar la oportunidad antes de proceder."
