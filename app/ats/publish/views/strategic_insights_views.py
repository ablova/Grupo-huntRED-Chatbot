"""
Vistas para el dashboard de insights estratégicos y análisis sectorial.
"""
import logging
from typing import Dict, Any
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
import json

from app.ml.analyzers.scraping_ml_analyzer import ScrapingMLAnalyzer

logger = logging.getLogger(__name__)

@login_required
def strategic_insights_dashboard(request):
    """
    Vista principal del dashboard de insights estratégicos.
    """
    return render(request, 'admin/strategic_insights_dashboard.html', {
        'page_title': 'Dashboard de Insights Estratégicos',
        'active_tab': 'strategic_insights'
    })

@method_decorator(csrf_exempt, name='dispatch')
class StrategicInsightsAPIView(View):
    """
    API para obtener insights estratégicos.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.analyzer = ScrapingMLAnalyzer()
    
    async def get_sector_movements(self, request):
        """
        Obtiene análisis de movimientos sectoriales.
        """
        try:
            business_unit = request.GET.get('business_unit')
            timeframe_days = int(request.GET.get('timeframe_days', 30))
            
            result = await self.analyzer.analyze_sector_movements(
                business_unit=business_unit,
                timeframe_days=timeframe_days
            )
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error obteniendo movimientos sectoriales: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def get_global_local_metrics(self, request):
        """
        Obtiene métricas globales y locales.
        """
        try:
            business_unit = request.GET.get('business_unit')
            
            result = await self.analyzer.analyze_global_local_metrics(
                business_unit=business_unit
            )
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas globales/locales: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def get_environmental_factors(self, request):
        """
        Obtiene análisis de factores del entorno.
        """
        try:
            business_unit = request.GET.get('business_unit')
            
            result = await self.analyzer.analyze_environmental_factors(
                business_unit=business_unit
            )
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error obteniendo factores del entorno: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def get_periodic_insights(self, request):
        """
        Obtiene insights periódicos.
        """
        try:
            business_unit = request.GET.get('business_unit')
            period = request.GET.get('period', 'weekly')
            
            result = await self.analyzer.generate_periodic_insights(
                business_unit=business_unit,
                period=period
            )
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error obteniendo insights periódicos: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def get(self, request, *args, **kwargs):
        """
        Maneja las peticiones GET para diferentes tipos de análisis.
        """
        analysis_type = kwargs.get('analysis_type')
        
        if analysis_type == 'sector-movements':
            return await self.get_sector_movements(request)
        elif analysis_type == 'global-local-metrics':
            return await self.get_global_local_metrics(request)
        elif analysis_type == 'environmental-factors':
            return await self.get_environmental_factors(request)
        elif analysis_type == 'periodic-insights':
            return await self.get_periodic_insights(request)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Tipo de análisis no válido'
            }, status=400)

@require_http_methods(["GET"])
@login_required
def sector_movements_api(request):
    """
    API endpoint para movimientos sectoriales.
    """
    analyzer = ScrapingMLAnalyzer()
    
    try:
        business_unit = request.GET.get('business_unit')
        timeframe_days = int(request.GET.get('timeframe_days', 30))
        
        # Importar asyncio para manejar async
        import asyncio
        
        # Ejecutar función async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            analyzer.analyze_sector_movements(
                business_unit=business_unit,
                timeframe_days=timeframe_days
            )
        )
        loop.close()
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en sector_movements_api: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
@login_required
def global_local_metrics_api(request):
    """
    API endpoint para métricas globales y locales.
    """
    analyzer = ScrapingMLAnalyzer()
    
    try:
        business_unit = request.GET.get('business_unit')
        
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            analyzer.analyze_global_local_metrics(
                business_unit=business_unit
            )
        )
        loop.close()
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en global_local_metrics_api: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
@login_required
def environmental_factors_api(request):
    """
    API endpoint para factores del entorno.
    """
    analyzer = ScrapingMLAnalyzer()
    
    try:
        business_unit = request.GET.get('business_unit')
        
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            analyzer.analyze_environmental_factors(
                business_unit=business_unit
            )
        )
        loop.close()
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en environmental_factors_api: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
@login_required
def periodic_insights_api(request):
    """
    API endpoint para insights periódicos.
    """
    analyzer = ScrapingMLAnalyzer()
    
    try:
        business_unit = request.GET.get('business_unit')
        period = request.GET.get('period', 'weekly')
        
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            analyzer.generate_periodic_insights(
                business_unit=business_unit,
                period=period
            )
        )
        loop.close()
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en periodic_insights_api: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["POST"])
@login_required
def export_insights_report(request):
    """
    Exporta reporte de insights en diferentes formatos.
    """
    try:
        data = json.loads(request.body)
        report_type = data.get('report_type', 'pdf')
        analysis_type = data.get('analysis_type', 'all')
        business_unit = data.get('business_unit')
        period = data.get('period', 'weekly')
        
        # Aquí implementarías la lógica de exportación
        # Por ahora retornamos un placeholder
        
        return JsonResponse({
            'success': True,
            'message': f'Reporte {report_type} generado exitosamente',
            'download_url': f'/media/reports/insights_report_{analysis_type}_{period}.{report_type}'
        })
        
    except Exception as e:
        logger.error(f"Error exportando reporte: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
@login_required
def insights_comparison_view(request):
    """
    Vista para comparar insights entre diferentes períodos.
    """
    try:
        period1 = request.GET.get('period1', 'weekly')
        period2 = request.GET.get('period2', 'monthly')
        business_unit = request.GET.get('business_unit')
        
        analyzer = ScrapingMLAnalyzer()
        
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Obtener insights para ambos períodos
        insights1 = loop.run_until_complete(
            analyzer.generate_periodic_insights(
                business_unit=business_unit,
                period=period1
            )
        )
        
        insights2 = loop.run_until_complete(
            analyzer.generate_periodic_insights(
                business_unit=business_unit,
                period=period2
            )
        )
        
        loop.close()
        
        # Comparar insights
        comparison = {
            'period1': {
                'period': period1,
                'insights': insights1
            },
            'period2': {
                'period': period2,
                'insights': insights2
            },
            'differences': _calculate_insights_differences(insights1, insights2)
        }
        
        return JsonResponse({
            'success': True,
            'comparison': comparison
        })
        
    except Exception as e:
        logger.error(f"Error comparando insights: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def _calculate_insights_differences(insights1: Dict, insights2: Dict) -> Dict[str, Any]:
    """
    Calcula diferencias entre dos conjuntos de insights.
    """
    differences = {
        'creation_analysis': {},
        'payment_insights': {},
        'process_performance': {},
        'market_trends': {}
    }
    
    # Comparar análisis de creación
    if 'creation_analysis' in insights1 and 'creation_analysis' in insights2:
        ca1 = insights1['creation_analysis']
        ca2 = insights2['creation_analysis']
        
        differences['creation_analysis'] = {
            'total_vacancies_diff': ca2.get('total_vacancies', 0) - ca1.get('total_vacancies', 0),
            'total_new_vacancies_diff': ca2.get('total_new_vacancies', 0) - ca1.get('total_new_vacancies', 0),
            'conversion_rate_diff': ca2.get('conversion_rate', 0) - ca1.get('conversion_rate', 0),
            'trend_direction_change': ca2.get('trend_direction') != ca1.get('trend_direction')
        }
    
    # Comparar insights de pagos
    if 'payment_insights' in insights1 and 'payment_insights' in insights2:
        pi1 = insights1['payment_insights']
        pi2 = insights2['payment_insights']
        
        differences['payment_insights'] = {
            'total_revenue_diff': pi2.get('total_revenue', 0) - pi1.get('total_revenue', 0),
            'transaction_count_diff': pi2.get('transaction_count', 0) - pi1.get('transaction_count', 0),
            'avg_transaction_value_diff': pi2.get('avg_transaction_value', 0) - pi1.get('avg_transaction_value', 0)
        }
    
    return differences

@require_http_methods(["GET"])
@login_required
def sector_opportunity_alert(request):
    """
    Genera alertas de oportunidades sectoriales.
    """
    try:
        business_unit = request.GET.get('business_unit')
        threshold = float(request.GET.get('threshold', 0.7))
        
        analyzer = ScrapingMLAnalyzer()
        
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        sector_data = loop.run_until_complete(
            analyzer.analyze_sector_movements(
                business_unit=business_unit,
                timeframe_days=30
            )
        )
        
        loop.close()
        
        # Filtrar oportunidades por threshold
        high_opportunity_sectors = [
            sector for sector in sector_data.get('growing_sectors', [])
            if sector.get('growth_score', 0) >= threshold
        ]
        
        return JsonResponse({
            'success': True,
            'alerts': high_opportunity_sectors,
            'threshold': threshold,
            'total_alerts': len(high_opportunity_sectors)
        })
        
    except Exception as e:
        logger.error(f"Error generando alertas sectoriales: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500) 