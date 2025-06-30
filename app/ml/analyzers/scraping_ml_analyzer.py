"""
Analyzer que integra scraping con ML y sistema de publicación para análisis inteligente.
Incluye análisis de movimientos sectoriales, capacidades de venta y métricas globales/locales.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F
from django.core.cache import cache
import json

from app.models import DominioScraping, RegistroScraping, Vacante
from app.ats.publish.models import DomainAnalysis, UsageFrequencyAnalysis
from app.ml.aura.aura_engine import AuraEngine
from app.ml.aura.vibrational_matcher import VibrationalMatcher

logger = logging.getLogger(__name__)

class ScrapingMLAnalyzer:
    """
    Analyzer que integra datos de scraping con ML para análisis inteligente.
    Incluye análisis sectorial, capacidades de venta y métricas estratégicas.
    """
    
    def __init__(self):
        self.aura_engine = AuraEngine()
        self.vibrational_matcher = VibrationalMatcher()
        self.cache_timeout = 1800  # 30 minutos
    
    async def analyze_scraping_patterns(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Analiza patrones de scraping para identificar oportunidades.
        """
        try:
            # Obtener datos de scraping
            scraping_data = await self._get_scraping_data(business_unit)
            
            # Analizar patrones de frecuencia
            frequency_patterns = await self._analyze_frequency_patterns(scraping_data)
            
            # Analizar patrones de vacantes
            vacancy_patterns = await self._analyze_vacancy_patterns(scraping_data)
            
            # Analizar patrones de éxito/fallo
            success_patterns = await self._analyze_success_patterns(scraping_data)
            
            # Integrar con AURA
            aura_insights = await self._get_aura_insights(scraping_data)
            
            # Generar recomendaciones
            recommendations = await self._generate_recommendations(
                frequency_patterns, vacancy_patterns, success_patterns, aura_insights
            )
            
            return {
                'success': True,
                'frequency_patterns': frequency_patterns,
                'vacancy_patterns': vacancy_patterns,
                'success_patterns': success_patterns,
                'aura_insights': aura_insights,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analizando patrones de scraping: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def predict_domain_potential(self, domain: str) -> Dict[str, Any]:
        """
        Predice el potencial de un dominio basado en datos de scraping y ML.
        """
        try:
            # Obtener datos del dominio
            domain_data = await self._get_domain_scraping_data(domain)
            
            if not domain_data:
                return {
                    'success': False,
                    'error': 'Dominio no encontrado'
                }
            
            # Análisis de frecuencia
            frequency_score = await self._calculate_frequency_score(domain_data)
            
            # Análisis de vacantes
            vacancy_score = await self._calculate_vacancy_score(domain_data)
            
            # Análisis de éxito
            success_score = await self._calculate_success_score(domain_data)
            
            # Análisis AURA
            aura_score = await self._calculate_aura_score(domain_data)
            
            # Score compuesto
            composite_score = (frequency_score * 0.3 + 
                             vacancy_score * 0.3 + 
                             success_score * 0.2 + 
                             aura_score * 0.2)
            
            # Predicciones
            predictions = await self._generate_predictions(domain_data, composite_score)
            
            return {
                'success': True,
                'domain': domain,
                'composite_score': composite_score,
                'frequency_score': frequency_score,
                'vacancy_score': vacancy_score,
                'success_score': success_score,
                'aura_score': aura_score,
                'predictions': predictions,
                'recommendations': await self._get_domain_recommendations(composite_score)
            }
            
        except Exception as e:
            logger.error(f"Error prediciendo potencial del dominio {domain}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def optimize_scraping_schedule(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Optimiza el horario de scraping basado en análisis ML.
        """
        try:
            # Obtener datos históricos
            historical_data = await self._get_historical_scraping_data(business_unit)
            
            # Analizar patrones temporales
            temporal_patterns = await self._analyze_temporal_patterns(historical_data)
            
            # Analizar patrones de éxito por hora
            hourly_success = await self._analyze_hourly_success(historical_data)
            
            # Analizar patrones de vacantes por día
            daily_vacancies = await self._analyze_daily_vacancies(historical_data)
            
            # Generar horario optimizado
            optimized_schedule = await self._generate_optimized_schedule(
                temporal_patterns, hourly_success, daily_vacancies
            )
            
            return {
                'success': True,
                'temporal_patterns': temporal_patterns,
                'hourly_success': hourly_success,
                'daily_vacancies': daily_vacancies,
                'optimized_schedule': optimized_schedule
            }
            
        except Exception as e:
            logger.error(f"Error optimizando horario de scraping: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def identify_high_value_domains(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Identifica dominios de alto valor basado en análisis ML.
        """
        try:
            # Obtener todos los dominios
            domains = await self._get_all_domains(business_unit)
            
            # Analizar cada dominio
            domain_analyses = []
            for domain in domains:
                analysis = await self.predict_domain_potential(domain.dominio)
                if analysis['success']:
                    domain_analyses.append({
                        'domain': domain,
                        'analysis': analysis
                    })
            
            # Ordenar por score
            domain_analyses.sort(key=lambda x: x['analysis']['composite_score'], reverse=True)
            
            # Identificar dominios de alto valor
            high_value_domains = [
                da for da in domain_analyses 
                if da['analysis']['composite_score'] >= 0.7
            ]
            
            # Generar insights
            insights = await self._generate_high_value_insights(high_value_domains)
            
            return {
                'success': True,
                'total_domains': len(domains),
                'high_value_domains': len(high_value_domains),
                'domain_analyses': domain_analyses[:20],  # Top 20
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"Error identificando dominios de alto valor: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_sector_movements(self, business_unit: str = None, timeframe_days: int = 30) -> Dict[str, Any]:
        """
        Analiza movimientos sectoriales para identificar oportunidades de venta.
        """
        try:
            # Obtener datos de scraping por sector
            sector_data = await self._get_sector_scraping_data(business_unit, timeframe_days)
            
            # Analizar tendencias sectoriales
            sector_trends = await self._analyze_sector_trends(sector_data)
            
            # Identificar sectores en crecimiento
            growing_sectors = await self._identify_growing_sectors(sector_data)
            
            # Analizar movimientos de empresas
            company_movements = await self._analyze_company_movements(sector_data)
            
            # Generar oportunidades de venta
            sales_opportunities = await self._generate_sales_opportunities(
                sector_trends, growing_sectors, company_movements
            )
            
            # Análisis de competencia sectorial
            competitive_analysis = await self._analyze_sector_competition(sector_data)
            
            return {
                'success': True,
                'sector_trends': sector_trends,
                'growing_sectors': growing_sectors,
                'company_movements': company_movements,
                'sales_opportunities': sales_opportunities,
                'competitive_analysis': competitive_analysis,
                'timeframe_days': timeframe_days
            }
            
        except Exception as e:
            logger.error(f"Error analizando movimientos sectoriales: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_global_local_metrics(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Analiza métricas globales y locales para insights estratégicos.
        """
        try:
            # Métricas globales
            global_metrics = await self._get_global_metrics(business_unit)
            
            # Métricas locales por región/ciudad
            local_metrics = await self._get_local_metrics(business_unit)
            
            # Análisis de pagos y monetización
            payment_analysis = await self._analyze_payment_metrics(business_unit)
            
            # Comparativa global vs local
            comparison_analysis = await self._compare_global_local(global_metrics, local_metrics)
            
            # Insights estratégicos
            strategic_insights = await self._generate_strategic_insights(
                global_metrics, local_metrics, payment_analysis
            )
            
            return {
                'success': True,
                'global_metrics': global_metrics,
                'local_metrics': local_metrics,
                'payment_analysis': payment_analysis,
                'comparison_analysis': comparison_analysis,
                'strategic_insights': strategic_insights
            }
            
        except Exception as e:
            logger.error(f"Error analizando métricas globales/locales: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_environmental_factors(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Analiza factores del entorno que afectan el mercado laboral.
        """
        try:
            # Análisis económico
            economic_analysis = await self._analyze_economic_factors(business_unit)
            
            # Análisis tecnológico
            tech_analysis = await self._analyze_tech_trends(business_unit)
            
            # Análisis regulatorio
            regulatory_analysis = await self._analyze_regulatory_changes(business_unit)
            
            # Análisis de mercado
            market_analysis = await self._analyze_market_conditions(business_unit)
            
            # Impacto en estrategia
            strategy_impact = await self._analyze_strategy_impact(
                economic_analysis, tech_analysis, regulatory_analysis, market_analysis
            )
            
            return {
                'success': True,
                'economic_analysis': economic_analysis,
                'tech_analysis': tech_analysis,
                'regulatory_analysis': regulatory_analysis,
                'market_analysis': market_analysis,
                'strategy_impact': strategy_impact
            }
            
        except Exception as e:
            logger.error(f"Error analizando factores del entorno: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def generate_periodic_insights(self, business_unit: str = None, period: str = 'weekly') -> Dict[str, Any]:
        """
        Genera insights periódicos para el equipo.
        """
        try:
            # Análisis de creación de vacantes
            creation_analysis = await self._analyze_vacancy_creation_patterns(business_unit, period)
            
            # Análisis de pagos y monetización
            payment_insights = await self._analyze_payment_patterns(business_unit, period)
            
            # Análisis de rendimiento por proceso
            process_performance = await self._analyze_process_performance(business_unit, period)
            
            # Análisis de tendencias del mercado
            market_trends = await self._analyze_market_trends(business_unit, period)
            
            # Recomendaciones para el equipo
            team_recommendations = await self._generate_team_recommendations(
                creation_analysis, payment_insights, process_performance, market_trends
            )
            
            return {
                'success': True,
                'period': period,
                'creation_analysis': creation_analysis,
                'payment_insights': payment_insights,
                'process_performance': process_performance,
                'market_trends': market_trends,
                'team_recommendations': team_recommendations,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generando insights periódicos: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_scraping_data(self, business_unit: str = None) -> List[Dict[str, Any]]:
        """
        Obtiene datos de scraping con cache.
        """
        cache_key = f"scraping_data_{business_unit or 'all'}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Query base
        query = RegistroScraping.objects.select_related('dominio')
        
        if business_unit:
            query = query.filter(dominio__business_unit=business_unit)
        
        # Obtener datos de los últimos 30 días
        thirty_days_ago = timezone.now() - timedelta(days=30)
        registros = query.filter(fecha_scraping__gte=thirty_days_ago)
        
        # Agrupar por dominio
        data = []
        for registro in registros:
            data.append({
                'dominio': registro.dominio.dominio,
                'fecha': registro.fecha_scraping,
                'vacantes_encontradas': registro.vacantes_encontradas,
                'vacantes_nuevas': registro.vacantes_nuevas,
                'estado': registro.estado,
                'business_unit': registro.dominio.business_unit
            })
        
        cache.set(cache_key, data, self.cache_timeout)
        return data
    
    async def _analyze_frequency_patterns(self, scraping_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza patrones de frecuencia de scraping.
        """
        if not scraping_data:
            return {'error': 'No hay datos disponibles'}
        
        # Agrupar por dominio
        domain_frequency = {}
        for record in scraping_data:
            domain = record['dominio']
            if domain not in domain_frequency:
                domain_frequency[domain] = []
            domain_frequency[domain].append(record['fecha'])
        
        # Calcular métricas de frecuencia
        frequency_metrics = {}
        for domain, dates in domain_frequency.items():
            dates.sort()
            intervals = []
            for i in range(1, len(dates)):
                interval = (dates[i] - dates[i-1]).total_seconds() / 3600  # horas
                intervals.append(interval)
            
            if intervals:
                frequency_metrics[domain] = {
                    'total_scrapes': len(dates),
                    'avg_interval_hours': sum(intervals) / len(intervals),
                    'min_interval_hours': min(intervals),
                    'max_interval_hours': max(intervals),
                    'consistency_score': 1 / (max(intervals) - min(intervals) + 1) if max(intervals) != min(intervals) else 1
                }
        
        return {
            'domain_frequency': frequency_metrics,
            'total_domains': len(frequency_metrics),
            'avg_scrapes_per_domain': sum(m['total_scrapes'] for m in frequency_metrics.values()) / len(frequency_metrics) if frequency_metrics else 0
        }
    
    async def _analyze_vacancy_patterns(self, scraping_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza patrones de vacantes encontradas.
        """
        if not scraping_data:
            return {'error': 'No hay datos disponibles'}
        
        # Agrupar por dominio
        domain_vacancies = {}
        for record in scraping_data:
            domain = record['dominio']
            if domain not in domain_vacancies:
                domain_vacancies[domain] = {
                    'total_found': 0,
                    'total_new': 0,
                    'scrapes': 0
                }
            
            domain_vacancies[domain]['total_found'] += record['vacantes_encontradas']
            domain_vacancies[domain]['total_new'] += record['vacantes_nuevas']
            domain_vacancies[domain]['scrapes'] += 1
        
        # Calcular métricas
        vacancy_metrics = {}
        for domain, data in domain_vacancies.items():
            vacancy_metrics[domain] = {
                'total_vacancies_found': data['total_found'],
                'total_new_vacancies': data['total_new'],
                'avg_vacancies_per_scrape': data['total_found'] / data['scrapes'],
                'avg_new_vacancies_per_scrape': data['total_new'] / data['scrapes'],
                'conversion_rate': data['total_new'] / data['total_found'] if data['total_found'] > 0 else 0
            }
        
        return {
            'domain_vacancies': vacancy_metrics,
            'total_vacancies_found': sum(m['total_vacancies_found'] for m in vacancy_metrics.values()),
            'total_new_vacancies': sum(m['total_new_vacancies'] for m in vacancy_metrics.values()),
            'overall_conversion_rate': sum(m['total_new_vacancies'] for m in vacancy_metrics.values()) / sum(m['total_vacancies_found'] for m in vacancy_metrics.values()) if sum(m['total_vacancies_found'] for m in vacancy_metrics.values()) > 0 else 0
        }
    
    async def _analyze_success_patterns(self, scraping_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza patrones de éxito/fallo del scraping.
        """
        if not scraping_data:
            return {'error': 'No hay datos disponibles'}
        
        # Contar estados
        status_counts = {}
        domain_success = {}
        
        for record in scraping_data:
            status = record['estado']
            domain = record['dominio']
            
            # Contar estados generales
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Contar por dominio
            if domain not in domain_success:
                domain_success[domain] = {'total': 0, 'success': 0}
            
            domain_success[domain]['total'] += 1
            if status == 'exitoso':
                domain_success[domain]['success'] += 1
        
        # Calcular tasas de éxito por dominio
        success_rates = {}
        for domain, data in domain_success.items():
            success_rates[domain] = data['success'] / data['total']
        
        return {
            'status_distribution': status_counts,
            'domain_success_rates': success_rates,
            'overall_success_rate': sum(data['success'] for data in domain_success.values()) / sum(data['total'] for data in domain_success.values()) if domain_success else 0
        }
    
    async def _get_aura_insights(self, scraping_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Obtiene insights de AURA basados en datos de scraping.
        """
        try:
            # Preparar datos para AURA
            aura_data = []
            for record in scraping_data:
                aura_data.append({
                    'domain': record['dominio'],
                    'vacancies_found': record['vacantes_encontradas'],
                    'new_vacancies': record['vacantes_nuevas'],
                    'success': record['estado'] == 'exitoso',
                    'business_unit': record['business_unit']
                })
            
            # Obtener insights de AURA
            aura_insights = await self.aura_engine.analyze_scraping_patterns(aura_data)
            
            return {
                'vibrational_score': aura_insights.get('vibrational_score', 0),
                'pattern_insights': aura_insights.get('pattern_insights', []),
                'recommendations': aura_insights.get('recommendations', [])
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo insights de AURA: {str(e)}")
            return {
                'vibrational_score': 0,
                'pattern_insights': [],
                'recommendations': []
            }
    
    async def _generate_recommendations(self, frequency_patterns: Dict, 
                                      vacancy_patterns: Dict, 
                                      success_patterns: Dict, 
                                      aura_insights: Dict) -> List[str]:
        """
        Genera recomendaciones basadas en todos los análisis.
        """
        recommendations = []
        
        # Recomendaciones basadas en frecuencia
        if 'domain_frequency' in frequency_patterns:
            for domain, metrics in frequency_patterns['domain_frequency'].items():
                if metrics['avg_interval_hours'] > 24:
                    recommendations.append(f"Considerar aumentar frecuencia de scraping para {domain}")
                if metrics['consistency_score'] < 0.5:
                    recommendations.append(f"Mejorar consistencia de scraping para {domain}")
        
        # Recomendaciones basadas en vacantes
        if 'domain_vacancies' in vacancy_patterns:
            for domain, metrics in vacancy_patterns['domain_vacancies'].items():
                if metrics['conversion_rate'] < 0.1:
                    recommendations.append(f"Revisar filtros de vacantes para {domain}")
                if metrics['avg_vacancies_per_scrape'] < 5:
                    recommendations.append(f"Evaluar si {domain} sigue siendo relevante")
        
        # Recomendaciones basadas en éxito
        if 'domain_success_rates' in success_patterns:
            for domain, rate in success_patterns['domain_success_rates'].items():
                if rate < 0.8:
                    recommendations.append(f"Investigar fallos en scraping de {domain}")
        
        # Recomendaciones de AURA
        if 'recommendations' in aura_insights:
            recommendations.extend(aura_insights['recommendations'])
        
        return recommendations[:10]  # Limitar a 10 recomendaciones
    
    async def _get_domain_scraping_data(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos específicos de un dominio.
        """
        try:
            dominio_obj = DominioScraping.objects.get(dominio=domain)
            registros = RegistroScraping.objects.filter(dominio=dominio_obj)
            
            if not registros.exists():
                return None
            
            # Calcular métricas
            total_registros = registros.count()
            registros_exitosos = registros.filter(estado='exitoso').count()
            total_vacantes = registros.aggregate(total=Sum('vacantes_encontradas'))['total'] or 0
            total_nuevas = registros.aggregate(total=Sum('vacantes_nuevas'))['total'] or 0
            
            return {
                'dominio': dominio_obj,
                'total_registros': total_registros,
                'registros_exitosos': registros_exitosos,
                'tasa_exito': registros_exitosos / total_registros,
                'total_vacantes': total_vacantes,
                'total_nuevas': total_nuevas,
                'tasa_conversion': total_nuevas / total_vacantes if total_vacantes > 0 else 0,
                'registros': list(registros.values())
            }
            
        except DominioScraping.DoesNotExist:
            return None
    
    async def _calculate_frequency_score(self, domain_data: Dict[str, Any]) -> float:
        """
        Calcula score de frecuencia basado en consistencia y regularidad.
        """
        registros = domain_data['registros']
        if len(registros) < 2:
            return 0.5
        
        # Calcular intervalos entre scraping
        fechas = sorted([r['fecha_scraping'] for r in registros])
        intervalos = []
        for i in range(1, len(fechas)):
            intervalo = (fechas[i] - fechas[i-1]).total_seconds() / 3600
            intervalos.append(intervalo)
        
        if not intervalos:
            return 0.5
        
        # Score basado en consistencia
        avg_intervalo = sum(intervalos) / len(intervalos)
        desviacion = sum(abs(i - avg_intervalo) for i in intervalos) / len(intervalos)
        
        # Normalizar score
        consistency_score = 1 / (1 + desviacion / avg_intervalo) if avg_intervalo > 0 else 0
        frequency_score = min(1.0, len(registros) / 30)  # Normalizar por 30 días
        
        return (consistency_score * 0.7 + frequency_score * 0.3)
    
    async def _calculate_vacancy_score(self, domain_data: Dict[str, Any]) -> float:
        """
        Calcula score de vacantes basado en cantidad y calidad.
        """
        total_vacantes = domain_data['total_vacantes']
        total_nuevas = domain_data['total_nuevas']
        tasa_conversion = domain_data['tasa_conversion']
        
        # Score de cantidad
        quantity_score = min(1.0, total_vacantes / 100)  # Normalizar por 100 vacantes
        
        # Score de calidad
        quality_score = tasa_conversion
        
        # Score de novedad
        novelty_score = min(1.0, total_nuevas / 50)  # Normalizar por 50 nuevas
        
        return (quantity_score * 0.4 + quality_score * 0.4 + novelty_score * 0.2)
    
    async def _calculate_success_score(self, domain_data: Dict[str, Any]) -> float:
        """
        Calcula score de éxito basado en tasa de éxito.
        """
        return domain_data['tasa_exito']
    
    async def _calculate_aura_score(self, domain_data: Dict[str, Any]) -> float:
        """
        Calcula score de AURA basado en análisis vibracional.
        """
        try:
            # Preparar datos para AURA
            aura_data = {
                'domain': domain_data['dominio'].dominio,
                'success_rate': domain_data['tasa_exito'],
                'conversion_rate': domain_data['tasa_conversion'],
                'total_vacancies': domain_data['total_vacantes'],
                'business_unit': domain_data['dominio'].business_unit
            }
            
            # Obtener score de AURA
            aura_score = await self.aura_engine.calculate_domain_vibrational_score(aura_data)
            return min(1.0, max(0.0, aura_score))
            
        except Exception as e:
            logger.error(f"Error calculando score de AURA: {str(e)}")
            return 0.5
    
    async def _generate_predictions(self, domain_data: Dict[str, Any], composite_score: float) -> Dict[str, Any]:
        """
        Genera predicciones basadas en el score compuesto.
        """
        predictions = {
            'next_week_vacancies': int(domain_data['total_vacantes'] * 0.25 * composite_score),
            'next_month_vacancies': int(domain_data['total_vacantes'] * 0.5 * composite_score),
            'success_probability': composite_score,
            'recommended_frequency_hours': int(24 / composite_score) if composite_score > 0 else 24,
            'expected_conversion_rate': domain_data['tasa_conversion'] * composite_score
        }
        
        return predictions
    
    async def _get_domain_recommendations(self, composite_score: float) -> List[str]:
        """
        Genera recomendaciones específicas para el dominio.
        """
        recommendations = []
        
        if composite_score >= 0.8:
            recommendations.extend([
                "Dominio de alto valor - mantener scraping frecuente",
                "Considerar aumentar frecuencia de scraping",
                "Evaluar oportunidades de monetización"
            ])
        elif composite_score >= 0.6:
            recommendations.extend([
                "Dominio de valor medio - optimizar configuración",
                "Revisar filtros de vacantes",
                "Monitorear tendencias"
            ])
        elif composite_score >= 0.4:
            recommendations.extend([
                "Dominio de valor bajo - evaluar continuidad",
                "Reducir frecuencia de scraping",
                "Considerar alternativas"
            ])
        else:
            recommendations.extend([
                "Dominio de muy bajo valor - considerar eliminación",
                "Suspender scraping temporalmente",
                "Revisar estrategia de sourcing"
            ])
        
        return recommendations
    
    async def _get_historical_scraping_data(self, business_unit: str = None) -> List[Dict[str, Any]]:
        """
        Obtiene datos históricos de scraping para análisis temporal.
        """
        query = RegistroScraping.objects.select_related('dominio')
        
        if business_unit:
            query = query.filter(dominio__business_unit=business_unit)
        
        # Obtener datos de los últimos 90 días
        ninety_days_ago = timezone.now() - timedelta(days=90)
        registros = query.filter(fecha_scraping__gte=ninety_days_ago)
        
        data = []
        for registro in registros:
            data.append({
                'dominio': registro.dominio.dominio,
                'fecha': registro.fecha_scraping,
                'hora': registro.fecha_scraping.hour,
                'dia_semana': registro.fecha_scraping.weekday(),
                'vacantes_encontradas': registro.vacantes_encontradas,
                'vacantes_nuevas': registro.vacantes_nuevas,
                'estado': registro.estado,
                'business_unit': registro.dominio.business_unit
            })
        
        return data
    
    async def _analyze_temporal_patterns(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza patrones temporales en los datos de scraping.
        """
        if not historical_data:
            return {'error': 'No hay datos históricos disponibles'}
        
        # Análisis por día de la semana
        daily_patterns = {}
        for i in range(7):
            daily_data = [d for d in historical_data if d['dia_semana'] == i]
            if daily_data:
                daily_patterns[i] = {
                    'total_scrapes': len(daily_data),
                    'avg_vacancies': sum(d['vacantes_encontradas'] for d in daily_data) / len(daily_data),
                    'avg_new_vacancies': sum(d['vacantes_nuevas'] for d in daily_data) / len(daily_data),
                    'success_rate': sum(1 for d in daily_data if d['estado'] == 'exitoso') / len(daily_data)
                }
        
        # Análisis por mes
        monthly_patterns = {}
        for record in historical_data:
            month_key = f"{record['fecha'].year}-{record['fecha'].month:02d}"
            if month_key not in monthly_patterns:
                monthly_patterns[month_key] = {
                    'total_scrapes': 0,
                    'total_vacancies': 0,
                    'total_new_vacancies': 0,
                    'successful_scrapes': 0
                }
            
            monthly_patterns[month_key]['total_scrapes'] += 1
            monthly_patterns[month_key]['total_vacancies'] += record['vacantes_encontradas']
            monthly_patterns[month_key]['total_new_vacancies'] += record['vacantes_nuevas']
            if record['estado'] == 'exitoso':
                monthly_patterns[month_key]['successful_scrapes'] += 1
        
        # Calcular tasas
        for month_data in monthly_patterns.values():
            month_data['success_rate'] = month_data['successful_scrapes'] / month_data['total_scrapes']
            month_data['avg_vacancies_per_scrape'] = month_data['total_vacancies'] / month_data['total_scrapes']
        
        return {
            'daily_patterns': daily_patterns,
            'monthly_patterns': monthly_patterns,
            'best_days': sorted(daily_patterns.items(), key=lambda x: x[1]['avg_vacancies'], reverse=True)[:3],
            'worst_days': sorted(daily_patterns.items(), key=lambda x: x[1]['avg_vacancies'])[:3]
        }
    
    async def _analyze_hourly_success(self, historical_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Analiza tasas de éxito por hora del día.
        """
        hourly_success = {}
        
        for hour in range(24):
            hour_data = [d for d in historical_data if d['hora'] == hour]
            if hour_data:
                success_count = sum(1 for d in hour_data if d['estado'] == 'exitoso')
                hourly_success[hour] = success_count / len(hour_data)
            else:
                hourly_success[hour] = 0.0
        
        return hourly_success
    
    async def _analyze_daily_vacancies(self, historical_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Analiza cantidad de vacantes por día de la semana.
        """
        daily_vacancies = {}
        
        for day in range(7):
            day_data = [d for d in historical_data if d['dia_semana'] == day]
            daily_vacancies[day] = sum(d['vacantes_encontradas'] for d in day_data)
        
        return daily_vacancies
    
    async def _generate_optimized_schedule(self, temporal_patterns: Dict, 
                                         hourly_success: Dict, 
                                         daily_vacancies: Dict) -> Dict[str, Any]:
        """
        Genera horario optimizado basado en análisis temporal.
        """
        # Encontrar mejores horas
        best_hours = sorted(hourly_success.items(), key=lambda x: x[1], reverse=True)[:6]
        
        # Encontrar mejores días
        best_days = sorted(daily_vacancies.items(), key=lambda x: x[1], reverse=True)[:4]
        
        # Generar horario
        schedule = {
            'recommended_hours': [hour for hour, _ in best_hours],
            'recommended_days': [day for day, _ in best_days],
            'frequency_recommendation': 'daily' if len(best_days) >= 5 else 'weekly',
            'peak_hours': [hour for hour, rate in best_hours if rate > 0.8],
            'avoid_hours': [hour for hour, rate in hourly_success.items() if rate < 0.5]
        }
        
        return schedule
    
    async def _get_all_domains(self, business_unit: str = None) -> List[DominioScraping]:
        """
        Obtiene todos los dominios de scraping.
        """
        query = DominioScraping.objects.all()
        
        if business_unit:
            query = query.filter(business_unit=business_unit)
        
        return list(query)
    
    async def _generate_high_value_insights(self, high_value_domains: List[Dict]) -> Dict[str, Any]:
        """
        Genera insights sobre dominios de alto valor.
        """
        if not high_value_domains:
            return {'message': 'No se encontraron dominios de alto valor'}
        
        # Análisis de patrones
        total_score = sum(da['analysis']['composite_score'] for da in high_value_domains)
        avg_score = total_score / len(high_value_domains)
        
        # Dominios con mejor score
        top_domains = sorted(high_value_domains, 
                           key=lambda x: x['analysis']['composite_score'], 
                           reverse=True)[:5]
        
        # Análisis por business unit
        business_unit_analysis = {}
        for da in high_value_domains:
            bu = da['domain'].business_unit
            if bu not in business_unit_analysis:
                business_unit_analysis[bu] = []
            business_unit_analysis[bu].append(da['analysis']['composite_score'])
        
        bu_insights = {}
        for bu, scores in business_unit_analysis.items():
            bu_insights[bu] = {
                'count': len(scores),
                'avg_score': sum(scores) / len(scores),
                'total_score': sum(scores)
            }
        
        return {
            'total_high_value_domains': len(high_value_domains),
            'average_score': avg_score,
            'top_domains': [{'domain': da['domain'].dominio, 'score': da['analysis']['composite_score']} 
                           for da in top_domains],
            'business_unit_insights': bu_insights,
            'recommendations': [
                f"Enfocar recursos en los {len(top_domains)} dominios principales",
                f"Optimizar configuración para dominios con score > {avg_score:.2f}",
                "Considerar expansión en business units con más dominios de alto valor"
            ]
        }
    
    async def _get_sector_scraping_data(self, business_unit: str = None, timeframe_days: int = 30) -> List[Dict[str, Any]]:
        """
        Obtiene datos de scraping agrupados por sector.
        """
        cache_key = f"sector_data_{business_unit or 'all'}_{timeframe_days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Query base
        query = RegistroScraping.objects.select_related('dominio')
        
        if business_unit:
            query = query.filter(dominio__business_unit=business_unit)
        
        # Filtrar por timeframe
        start_date = timezone.now() - timedelta(days=timeframe_days)
        registros = query.filter(fecha_scraping__gte=start_date)
        
        # Agrupar por sector
        sector_data = {}
        for registro in registros:
            sector = registro.dominio.sector if hasattr(registro.dominio, 'sector') else 'General'
            
            if sector not in sector_data:
                sector_data[sector] = {
                    'total_scrapes': 0,
                    'total_vacancies': 0,
                    'total_new_vacancies': 0,
                    'successful_scrapes': 0,
                    'domains': set(),
                    'daily_data': {}
                }
            
            sector_data[sector]['total_scrapes'] += 1
            sector_data[sector]['total_vacancies'] += registro.vacantes_encontradas
            sector_data[sector]['total_new_vacancies'] += registro.vacantes_nuevas
            sector_data[sector]['domains'].add(registro.dominio.dominio)
            
            if registro.estado == 'exitoso':
                sector_data[sector]['successful_scrapes'] += 1
            
            # Datos diarios
            date_key = registro.fecha_scraping.date().isoformat()
            if date_key not in sector_data[sector]['daily_data']:
                sector_data[sector]['daily_data'][date_key] = {
                    'vacancies': 0,
                    'new_vacancies': 0,
                    'scrapes': 0
                }
            
            sector_data[sector]['daily_data'][date_key]['vacancies'] += registro.vacantes_encontradas
            sector_data[sector]['daily_data'][date_key]['new_vacancies'] += registro.vacantes_nuevas
            sector_data[sector]['daily_data'][date_key]['scrapes'] += 1
        
        # Convertir sets a listas para JSON serialization
        for sector in sector_data:
            sector_data[sector]['domains'] = list(sector_data[sector]['domains'])
        
        cache.set(cache_key, sector_data, self.cache_timeout)
        return sector_data
    
    async def _analyze_sector_trends(self, sector_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza tendencias por sector.
        """
        trends = {}
        
        for sector, data in sector_data.items():
            # Calcular métricas básicas
            success_rate = data['successful_scrapes'] / data['total_scrapes'] if data['total_scrapes'] > 0 else 0
            avg_vacancies_per_scrape = data['total_vacancies'] / data['total_scrapes'] if data['total_scrapes'] > 0 else 0
            conversion_rate = data['total_new_vacancies'] / data['total_vacancies'] if data['total_vacancies'] > 0 else 0
            
            # Analizar tendencia temporal
            daily_vacancies = []
            for date_key, daily_data in sorted(data['daily_data'].items()):
                daily_vacancies.append(daily_data['vacancies'])
            
            # Calcular tendencia (pendiente de la línea de regresión simple)
            trend_direction = 'stable'
            if len(daily_vacancies) > 1:
                # Cálculo simple de tendencia
                first_half = sum(daily_vacancies[:len(daily_vacancies)//2])
                second_half = sum(daily_vacancies[len(daily_vacancies)//2:])
                
                if second_half > first_half * 1.2:
                    trend_direction = 'growing'
                elif second_half < first_half * 0.8:
                    trend_direction = 'declining'
            
            trends[sector] = {
                'total_vacancies': data['total_vacancies'],
                'total_new_vacancies': data['total_new_vacancies'],
                'success_rate': success_rate,
                'avg_vacancies_per_scrape': avg_vacancies_per_scrape,
                'conversion_rate': conversion_rate,
                'trend_direction': trend_direction,
                'active_domains': len(data['domains']),
                'growth_score': self._calculate_growth_score(data)
            }
        
        return trends
    
    async def _identify_growing_sectors(self, sector_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identifica sectores en crecimiento.
        """
        growing_sectors = []
        
        for sector, data in sector_data.items():
            growth_score = self._calculate_growth_score(data)
            
            if growth_score > 0.7:  # Umbral de crecimiento
                growing_sectors.append({
                    'sector': sector,
                    'growth_score': growth_score,
                    'total_vacancies': data['total_vacancies'],
                    'active_domains': len(data['domains']),
                    'trend_analysis': await self._analyze_sector_growth_trend(data),
                    'opportunity_level': 'high' if growth_score > 0.8 else 'medium'
                })
        
        # Ordenar por score de crecimiento
        growing_sectors.sort(key=lambda x: x['growth_score'], reverse=True)
        return growing_sectors
    
    async def _analyze_company_movements(self, sector_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza movimientos de empresas por sector.
        """
        company_movements = {}
        
        for sector, data in sector_data.items():
            # Analizar patrones de empresas
            domain_patterns = {}
            for domain in data['domains']:
                # Aquí podrías integrar con datos de empresas
                domain_patterns[domain] = {
                    'activity_level': 'high',  # Placeholder
                    'hiring_intensity': 'medium',  # Placeholder
                    'growth_trajectory': 'positive'  # Placeholder
                }
            
            company_movements[sector] = {
                'active_companies': len(data['domains']),
                'high_activity_companies': len([d for d in domain_patterns.values() if d['activity_level'] == 'high']),
                'hiring_companies': len([d for d in domain_patterns.values() if d['hiring_intensity'] in ['high', 'medium']]),
                'growing_companies': len([d for d in domain_patterns.values() if d['growth_trajectory'] == 'positive']),
                'company_patterns': domain_patterns
            }
        
        return company_movements
    
    async def _generate_sales_opportunities(self, sector_trends: Dict, 
                                          growing_sectors: List, 
                                          company_movements: Dict) -> List[Dict[str, Any]]:
        """
        Genera oportunidades de venta basadas en análisis sectorial.
        """
        opportunities = []
        
        # Oportunidades por sectores en crecimiento
        for sector_info in growing_sectors:
            sector = sector_info['sector']
            opportunities.append({
                'type': 'sector_growth',
                'sector': sector,
                'priority': 'high' if sector_info['growth_score'] > 0.8 else 'medium',
                'description': f"Sector {sector} en crecimiento fuerte - {sector_info['total_vacancies']} vacantes",
                'recommended_action': f"Enfocar esfuerzos de venta en {sector}",
                'expected_roi': 'high',
                'timeline': 'immediate'
            })
        
        # Oportunidades por movimientos de empresas
        for sector, movements in company_movements.items():
            if movements['hiring_companies'] > movements['active_companies'] * 0.7:
                opportunities.append({
                    'type': 'company_hiring_spike',
                    'sector': sector,
                    'priority': 'high',
                    'description': f"Pico de contratación en {sector} - {movements['hiring_companies']} empresas contratando",
                    'recommended_action': f"Contactar empresas en {sector} con servicios de reclutamiento",
                    'expected_roi': 'high',
                    'timeline': 'urgent'
                })
        
        return opportunities
    
    async def _analyze_sector_competition(self, sector_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza competencia en cada sector.
        """
        competition_analysis = {}
        
        for sector, data in sector_data.items():
            # Métricas de competencia
            vacancy_density = data['total_vacancies'] / len(data['domains']) if data['domains'] else 0
            market_saturation = len(data['domains']) / 100  # Normalizado
            
            competition_analysis[sector] = {
                'vacancy_density': vacancy_density,
                'market_saturation': market_saturation,
                'competition_level': 'high' if market_saturation > 0.7 else 'medium' if market_saturation > 0.3 else 'low',
                'opportunity_gap': 1 - market_saturation,
                'recommended_strategy': self._get_competition_strategy(market_saturation, vacancy_density)
            }
        
        return competition_analysis
    
    async def _get_global_metrics(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Obtiene métricas globales del sistema.
        """
        # Query base
        query = RegistroScraping.objects.select_related('dominio')
        
        if business_unit:
            query = query.filter(dominio__business_unit=business_unit)
        
        # Métricas de los últimos 30 días
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_data = query.filter(fecha_scraping__gte=thirty_days_ago)
        
        # Métricas de los últimos 7 días
        seven_days_ago = timezone.now() - timedelta(days=7)
        weekly_data = query.filter(fecha_scraping__gte=seven_days_ago)
        
        global_metrics = {
            'total_domains': DominioScraping.objects.filter(business_unit=business_unit).count() if business_unit else DominioScraping.objects.count(),
            'total_scrapes_30d': recent_data.count(),
            'total_scrapes_7d': weekly_data.count(),
            'total_vacancies_30d': recent_data.aggregate(total=Sum('vacantes_encontradas'))['total'] or 0,
            'total_vacancies_7d': weekly_data.aggregate(total=Sum('vacantes_encontradas'))['total'] or 0,
            'total_new_vacancies_30d': recent_data.aggregate(total=Sum('vacantes_nuevas'))['total'] or 0,
            'total_new_vacancies_7d': weekly_data.aggregate(total=Sum('vacantes_nuevas'))['total'] or 0,
            'success_rate_30d': recent_data.filter(estado='exitoso').count() / recent_data.count() if recent_data.count() > 0 else 0,
            'success_rate_7d': weekly_data.filter(estado='exitoso').count() / weekly_data.count() if weekly_data.count() > 0 else 0,
            'growth_rate_7d': self._calculate_growth_rate(weekly_data, recent_data),
            'conversion_rate_30d': recent_data.aggregate(total=Sum('vacantes_nuevas'))['total'] / recent_data.aggregate(total=Sum('vacantes_encontradas'))['total'] if recent_data.aggregate(total=Sum('vacantes_encontradas'))['total'] > 0 else 0
        }
        
        return global_metrics
    
    async def _get_local_metrics(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Obtiene métricas locales por región/ciudad.
        """
        # Query base
        query = RegistroScraping.objects.select_related('dominio')
        
        if business_unit:
            query = query.filter(dominio__business_unit=business_unit)
        
        # Agrupar por región/ciudad (asumiendo que hay un campo location en DominioScraping)
        local_metrics = {}
        
        # Placeholder - aquí integrarías con datos reales de ubicación
        regions = ['Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao']
        
        for region in regions:
            # Simular datos por región
            local_metrics[region] = {
                'total_domains': 10,  # Placeholder
                'total_vacancies_30d': 150,  # Placeholder
                'total_new_vacancies_30d': 45,  # Placeholder
                'success_rate': 0.85,  # Placeholder
                'growth_rate': 0.12,  # Placeholder
                'market_density': 0.6,  # Placeholder
                'competition_level': 'medium'  # Placeholder
            }
        
        return local_metrics
    
    async def _analyze_payment_metrics(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Analiza métricas de pagos y monetización.
        """
        # Placeholder - integrar con sistema de pagos real
        payment_metrics = {
            'total_revenue_30d': 50000,  # Placeholder
            'total_revenue_7d': 12000,  # Placeholder
            'revenue_growth_rate': 0.15,  # Placeholder
            'avg_transaction_value': 250,  # Placeholder
            'payment_success_rate': 0.95,  # Placeholder
            'recurring_revenue': 35000,  # Placeholder
            'new_customers_30d': 25,  # Placeholder
            'customer_retention_rate': 0.88,  # Placeholder
            'top_revenue_sectors': ['Tech', 'Finance', 'Healthcare'],  # Placeholder
            'payment_methods_distribution': {
                'credit_card': 0.6,
                'bank_transfer': 0.3,
                'digital_wallet': 0.1
            }
        }
        
        return payment_metrics
    
    async def _compare_global_local(self, global_metrics: Dict, local_metrics: Dict) -> Dict[str, Any]:
        """
        Compara métricas globales vs locales.
        """
        comparison = {
            'global_vs_local_performance': {},
            'regional_insights': [],
            'opportunity_gaps': []
        }
        
        # Comparar rendimiento por región
        for region, local_data in local_metrics.items():
            comparison['global_vs_local_performance'][region] = {
                'success_rate_diff': local_data['success_rate'] - global_metrics['success_rate_30d'],
                'growth_rate_diff': local_data['growth_rate'] - global_metrics['growth_rate_7d'],
                'market_efficiency': local_data['total_new_vacancies_30d'] / local_data['total_vacancies_30d'] if local_data['total_vacancies_30d'] > 0 else 0
            }
        
        # Identificar gaps de oportunidad
        for region, local_data in local_metrics.items():
            if local_data['growth_rate'] > global_metrics['growth_rate_7d'] * 1.2:
                comparison['opportunity_gaps'].append({
                    'region': region,
                    'type': 'high_growth',
                    'description': f"{region} muestra crecimiento superior al promedio",
                    'recommendation': f"Invertir más recursos en {region}"
                })
        
        return comparison
    
    async def _generate_strategic_insights(self, global_metrics: Dict, 
                                         local_metrics: Dict, 
                                         payment_metrics: Dict) -> List[Dict[str, Any]]:
        """
        Genera insights estratégicos basados en todas las métricas.
        """
        insights = []
        
        # Insight de crecimiento global
        if global_metrics['growth_rate_7d'] > 0.1:
            insights.append({
                'type': 'growth_opportunity',
                'priority': 'high',
                'title': 'Crecimiento Sólido Detectado',
                'description': f"El sistema muestra un crecimiento del {global_metrics['growth_rate_7d']*100:.1f}% en la última semana",
                'action': 'Mantener momentum y escalar operaciones'
            })
        
        # Insight de monetización
        if payment_metrics['revenue_growth_rate'] > 0.1:
            insights.append({
                'type': 'revenue_opportunity',
                'priority': 'high',
                'title': 'Crecimiento de Ingresos',
                'description': f"Los ingresos crecen al {payment_metrics['revenue_growth_rate']*100:.1f}%",
                'action': 'Optimizar estrategias de monetización'
            })
        
        # Insight regional
        best_region = max(local_metrics.items(), key=lambda x: x[1]['growth_rate'])
        insights.append({
            'type': 'regional_opportunity',
            'priority': 'medium',
            'title': f'Mejor Rendimiento Regional: {best_region[0]}',
            'description': f"{best_region[0]} muestra el mejor crecimiento regional",
            'action': f'Replicar estrategias exitosas de {best_region[0]} en otras regiones'
        })
        
        return insights
    
    async def _analyze_economic_factors(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Analiza factores económicos que afectan el mercado laboral.
        """
        # Placeholder - integrar con APIs de datos económicos
        economic_factors = {
            'gdp_growth_rate': 0.025,  # Placeholder
            'unemployment_rate': 0.12,  # Placeholder
            'inflation_rate': 0.035,  # Placeholder
            'interest_rate': 0.045,  # Placeholder
            'market_confidence': 0.7,  # Placeholder
            'sector_performance': {
                'tech': 0.15,
                'finance': 0.08,
                'healthcare': 0.12,
                'retail': -0.02,
                'manufacturing': 0.05
            },
            'impact_on_hiring': 'positive' if 0.025 > 0 else 'negative',
            'recommendations': [
                'Monitorear cambios en tasas de interés',
                'Ajustar estrategias según sector',
                'Preparar para cambios en demanda laboral'
            ]
        }
        
        return economic_factors
    
    async def _analyze_tech_trends(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Analiza tendencias tecnológicas relevantes.
        """
        # Placeholder - integrar con análisis de tendencias tech
        tech_trends = {
            'emerging_technologies': ['AI/ML', 'Blockchain', 'IoT', '5G', 'Quantum Computing'],
            'skill_demand_changes': {
                'increasing': ['Python', 'Data Science', 'Cloud Computing', 'Cybersecurity'],
                'decreasing': ['Legacy Systems', 'Manual Testing', 'Traditional Marketing']
            },
            'remote_work_adoption': 0.75,  # Placeholder
            'automation_impact': 0.3,  # Placeholder
            'digital_transformation_rate': 0.6,  # Placeholder
            'recommendations': [
                'Enfocar en habilidades digitales emergentes',
                'Adaptar servicios para trabajo remoto',
                'Preparar para automatización creciente'
            ]
        }
        
        return tech_trends
    
    async def _analyze_regulatory_changes(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Analiza cambios regulatorios relevantes.
        """
        # Placeholder - integrar con seguimiento regulatorio
        regulatory_changes = {
            'recent_changes': [
                'Nueva ley de protección de datos',
                'Cambios en regulación laboral',
                'Actualizaciones en compliance'
            ],
            'pending_changes': [
                'Reforma fiscal empresarial',
                'Nuevas regulaciones de IA'
            ],
            'compliance_requirements': {
                'data_protection': 'high',
                'labor_law': 'medium',
                'ai_regulation': 'low'
            },
            'impact_assessment': {
                'operational_impact': 'medium',
                'cost_impact': 'low',
                'opportunity_impact': 'high'
            },
            'recommendations': [
                'Actualizar políticas de compliance',
                'Preparar para nuevas regulaciones',
                'Monitorear cambios regulatorios'
            ]
        }
        
        return regulatory_changes
    
    async def _analyze_market_conditions(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Analiza condiciones generales del mercado.
        """
        # Placeholder - integrar con análisis de mercado
        market_conditions = {
            'market_sentiment': 'positive',
            'competition_level': 'high',
            'market_maturity': 'growing',
            'customer_preferences': {
                'digital_first': 0.8,
                'ai_integration': 0.7,
                'sustainability': 0.6,
                'flexibility': 0.9
            },
            'market_segments': {
                'enterprise': {'growth': 0.1, 'competition': 'high'},
                'sme': {'growth': 0.2, 'competition': 'medium'},
                'startup': {'growth': 0.3, 'competition': 'low'}
            },
            'recommendations': [
                'Enfocar en segmentos de alto crecimiento',
                'Diferenciar con servicios digitales',
                'Adaptar a preferencias del cliente'
            ]
        }
        
        return market_conditions
    
    async def _analyze_strategy_impact(self, economic_analysis: Dict, 
                                     tech_analysis: Dict, 
                                     regulatory_analysis: Dict, 
                                     market_analysis: Dict) -> Dict[str, Any]:
        """
        Analiza el impacto de factores del entorno en la estrategia.
        """
        impact_analysis = {
            'overall_impact': 'positive',
            'key_factors': [],
            'strategy_adjustments': [],
            'risk_assessment': {},
            'opportunity_identification': []
        }
        
        # Evaluar impacto económico
        if economic_analysis['impact_on_hiring'] == 'positive':
            impact_analysis['key_factors'].append('Crecimiento económico favorable')
            impact_analysis['opportunity_identification'].append('Expansión de servicios de reclutamiento')
        
        # Evaluar impacto tecnológico
        if tech_analysis['digital_transformation_rate'] > 0.5:
            impact_analysis['strategy_adjustments'].append('Acelerar digitalización de servicios')
            impact_analysis['opportunity_identification'].append('Servicios de transformación digital')
        
        # Evaluar impacto regulatorio
        if regulatory_analysis['impact_assessment']['opportunity_impact'] == 'high':
            impact_analysis['opportunity_identification'].append('Servicios de compliance y regulación')
        
        # Evaluar condiciones de mercado
        if market_analysis['market_sentiment'] == 'positive':
            impact_analysis['strategy_adjustments'].append('Aumentar inversión en marketing')
        
        return impact_analysis
    
    async def _analyze_vacancy_creation_patterns(self, business_unit: str = None, period: str = 'weekly') -> Dict[str, Any]:
        """
        Analiza patrones de creación de vacantes.
        """
        # Determinar timeframe
        if period == 'daily':
            timeframe = 1
        elif period == 'weekly':
            timeframe = 7
        elif period == 'monthly':
            timeframe = 30
        else:
            timeframe = 7
        
        start_date = timezone.now() - timedelta(days=timeframe)
        
        # Query datos
        query = RegistroScraping.objects.select_related('dominio')
        if business_unit:
            query = query.filter(dominio__business_unit=business_unit)
        
        recent_data = query.filter(fecha_scraping__gte=start_date)
        
        # Análisis temporal
        temporal_analysis = {}
        for record in recent_data:
            date_key = record.fecha_scraping.date().isoformat()
            if date_key not in temporal_analysis:
                temporal_analysis[date_key] = {
                    'total_vacancies': 0,
                    'new_vacancies': 0,
                    'scrapes': 0
                }
            
            temporal_analysis[date_key]['total_vacancies'] += record.vacantes_encontradas
            temporal_analysis[date_key]['new_vacancies'] += record.vacantes_nuevas
            temporal_analysis[date_key]['scrapes'] += 1
        
        # Calcular métricas
        total_vacancies = sum(data['total_vacancies'] for data in temporal_analysis.values())
        total_new_vacancies = sum(data['new_vacancies'] for data in temporal_analysis.values())
        avg_daily_vacancies = total_vacancies / len(temporal_analysis) if temporal_analysis else 0
        
        return {
            'period': period,
            'total_vacancies': total_vacancies,
            'total_new_vacancies': total_new_vacancies,
            'avg_daily_vacancies': avg_daily_vacancies,
            'conversion_rate': total_new_vacancies / total_vacancies if total_vacancies > 0 else 0,
            'temporal_pattern': temporal_analysis,
            'trend_direction': self._calculate_trend_direction(temporal_analysis)
        }
    
    async def _analyze_payment_patterns(self, business_unit: str = None, period: str = 'weekly') -> Dict[str, Any]:
        """
        Analiza patrones de pagos.
        """
        # Placeholder - integrar con sistema de pagos real
        payment_patterns = {
            'period': period,
            'total_revenue': 15000,  # Placeholder
            'transaction_count': 60,  # Placeholder
            'avg_transaction_value': 250,  # Placeholder
            'payment_methods': {
                'credit_card': 0.6,
                'bank_transfer': 0.3,
                'digital_wallet': 0.1
            },
            'customer_segments': {
                'enterprise': {'revenue': 8000, 'transactions': 20},
                'sme': {'revenue': 5000, 'transactions': 25},
                'startup': {'revenue': 2000, 'transactions': 15}
            },
            'trends': {
                'revenue_growth': 0.15,
                'transaction_growth': 0.1,
                'avg_value_growth': 0.05
            }
        }
        
        return payment_patterns
    
    async def _analyze_process_performance(self, business_unit: str = None, period: str = 'weekly') -> Dict[str, Any]:
        """
        Analiza rendimiento por tipo de proceso.
        """
        # Placeholder - integrar con métricas de proceso reales
        process_performance = {
            'period': period,
            'processes': {
                'scraping': {
                    'success_rate': 0.92,
                    'avg_duration': 300,  # segundos
                    'error_rate': 0.08,
                    'efficiency_score': 0.85
                },
                'data_processing': {
                    'success_rate': 0.95,
                    'avg_duration': 120,
                    'error_rate': 0.05,
                    'efficiency_score': 0.90
                },
                'publishing': {
                    'success_rate': 0.88,
                    'avg_duration': 180,
                    'error_rate': 0.12,
                    'efficiency_score': 0.82
                },
                'marketing': {
                    'success_rate': 0.85,
                    'avg_duration': 600,
                    'error_rate': 0.15,
                    'efficiency_score': 0.78
                }
            },
            'bottlenecks': ['publishing', 'marketing'],
            'optimization_opportunities': [
                'Mejorar tasa de éxito de publishing',
                'Optimizar duración de marketing',
                'Reducir errores en scraping'
            ]
        }
        
        return process_performance
    
    async def _analyze_market_trends(self, business_unit: str = None, period: str = 'weekly') -> Dict[str, Any]:
        """
        Analiza tendencias del mercado.
        """
        # Placeholder - integrar con análisis de mercado real
        market_trends = {
            'period': period,
            'market_sentiment': 'positive',
            'key_trends': [
                'Aumento en demanda de talento tech',
                'Crecimiento del trabajo remoto',
                'Mayor enfoque en diversidad',
                'Adopción acelerada de IA'
            ],
            'sector_performance': {
                'technology': {'growth': 0.25, 'demand': 'high'},
                'healthcare': {'growth': 0.15, 'demand': 'high'},
                'finance': {'growth': 0.10, 'demand': 'medium'},
                'retail': {'growth': 0.05, 'demand': 'low'}
            },
            'skill_demand_changes': {
                'increasing': ['AI/ML', 'Data Science', 'Cloud Computing'],
                'decreasing': ['Manual Testing', 'Legacy Systems']
            },
            'geographic_trends': {
                'high_growth_regions': ['Madrid', 'Barcelona', 'Valencia'],
                'emerging_regions': ['Bilbao', 'Sevilla', 'Málaga']
            }
        }
        
        return market_trends
    
    async def _generate_team_recommendations(self, creation_analysis: Dict, 
                                           payment_insights: Dict, 
                                           process_performance: Dict, 
                                           market_trends: Dict) -> List[Dict[str, Any]]:
        """
        Genera recomendaciones específicas para el equipo.
        """
        recommendations = []
        
        # Recomendaciones basadas en creación de vacantes
        if creation_analysis['conversion_rate'] < 0.3:
            recommendations.append({
                'category': 'optimization',
                'priority': 'high',
                'title': 'Optimizar Filtros de Vacantes',
                'description': f"La tasa de conversión es {creation_analysis['conversion_rate']*100:.1f}% - mejorar filtros",
                'action': 'Revisar y ajustar criterios de filtrado',
                'expected_impact': 'Aumentar conversión en 20%'
            })
        
        # Recomendaciones basadas en pagos
        if payment_insights['trends']['revenue_growth'] < 0.1:
            recommendations.append({
                'category': 'revenue',
                'priority': 'medium',
                'title': 'Impulsar Crecimiento de Ingresos',
                'description': 'El crecimiento de ingresos está por debajo del objetivo',
                'action': 'Implementar estrategias de upselling y cross-selling',
                'expected_impact': 'Aumentar ingresos en 15%'
            })
        
        # Recomendaciones basadas en rendimiento de procesos
        for process, metrics in process_performance['processes'].items():
            if metrics['efficiency_score'] < 0.8:
                recommendations.append({
                    'category': 'process_optimization',
                    'priority': 'medium',
                    'title': f'Optimizar Proceso: {process.title()}',
                    'description': f"Eficiencia del {metrics['efficiency_score']*100:.1f}% - mejorar rendimiento",
                    'action': f'Revisar y optimizar flujo de {process}',
                    'expected_impact': f'Aumentar eficiencia en {process} en 15%'
                })
        
        # Recomendaciones basadas en tendencias de mercado
        for trend in market_trends['key_trends']:
            if 'tech' in trend.lower() or 'ai' in trend.lower():
                recommendations.append({
                    'category': 'market_opportunity',
                    'priority': 'high',
                    'title': 'Capitalizar Tendencias Tech',
                    'description': f"Tendencia identificada: {trend}",
                    'action': 'Desarrollar servicios especializados en tech/AI',
                    'expected_impact': 'Capturar 25% del mercado tech emergente'
                })
        
        return recommendations[:10]  # Limitar a 10 recomendaciones
    
    def _calculate_growth_score(self, data: Dict[str, Any]) -> float:
        """
        Calcula score de crecimiento basado en datos sectoriales.
        """
        if not data['daily_data']:
            return 0.0
        
        # Calcular tendencia de vacantes
        daily_vacancies = []
        for date_key, daily_data in sorted(data['daily_data'].items()):
            daily_vacancies.append(daily_data['vacancies'])
        
        if len(daily_vacancies) < 2:
            return 0.5
        
        # Calcular crecimiento
        first_half = sum(daily_vacancies[:len(daily_vacancies)//2])
        second_half = sum(daily_vacancies[len(daily_vacancies)//2:])
        
        if first_half == 0:
            return 1.0 if second_half > 0 else 0.0
        
        growth_rate = (second_half - first_half) / first_half
        
        # Normalizar score
        return min(1.0, max(0.0, (growth_rate + 1) / 2))
    
    def _calculate_growth_rate(self, recent_data, historical_data) -> float:
        """
        Calcula tasa de crecimiento entre dos períodos.
        """
        recent_count = recent_data.count()
        historical_count = historical_data.count()
        
        if historical_count == 0:
            return 0.0
        
        return (recent_count - historical_count) / historical_count
    
    def _calculate_trend_direction(self, temporal_data: Dict) -> str:
        """
        Calcula dirección de tendencia basada en datos temporales.
        """
        if len(temporal_data) < 2:
            return 'stable'
        
        values = list(temporal_data.values())
        first_half = sum(v['total_vacancies'] for v in values[:len(values)//2])
        second_half = sum(v['total_vacancies'] for v in values[len(values)//2:])
        
        if second_half > first_half * 1.1:
            return 'growing'
        elif second_half < first_half * 0.9:
            return 'declining'
        else:
            return 'stable'
    
    def _get_competition_strategy(self, market_saturation: float, vacancy_density: float) -> str:
        """
        Determina estrategia de competencia basada en saturación y densidad.
        """
        if market_saturation < 0.3:
            return 'market_penetration'
        elif market_saturation < 0.7:
            return 'differentiation'
        else:
            return 'niche_focus'
    
    async def _analyze_sector_growth_trend(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza tendencia de crecimiento de un sector específico.
        """
        # Placeholder - análisis más detallado de tendencias sectoriales
        return {
            'growth_acceleration': 0.15,
            'sustainability_score': 0.8,
            'market_maturity': 'growing',
            'competitive_intensity': 'medium'
        } 