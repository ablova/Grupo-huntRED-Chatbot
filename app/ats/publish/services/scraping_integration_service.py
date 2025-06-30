"""
Servicio de integración de scraping con ML y sistema de publicación.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.core.cache import cache

from app.models import DominioScraping, RegistroScraping, Vacante
from app.ats.publish.models import (
    DomainAnalysis, UsageFrequencyAnalysis, IntelligentProspecting,
    CrossSellingOpportunity, MarketingCampaign
)
from app.ats.publish.analyzers.scraping_ml_analyzer import ScrapingMLAnalyzer
from app.ml.aura.aura_engine import AuraEngine
from app.ml.aura.vibrational_matcher import VibrationalMatcher

logger = logging.getLogger(__name__)

class ScrapingIntegrationService:
    """
    Servicio que integra datos de scraping con ML y sistema de publicación.
    """
    
    def __init__(self):
        self.scraping_analyzer = ScrapingMLAnalyzer()
        self.aura_engine = AuraEngine()
        self.vibrational_matcher = VibrationalMatcher()
        self.cache_timeout = 1800  # 30 minutos
    
    async def analyze_and_generate_campaigns(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Analiza datos de scraping y genera campañas de marketing inteligentes.
        """
        try:
            # Analizar patrones de scraping
            scraping_analysis = await self.scraping_analyzer.analyze_scraping_patterns(business_unit)
            
            if not scraping_analysis['success']:
                return {
                    'success': False,
                    'error': scraping_analysis['error']
                }
            
            # Identificar dominios de alto valor
            high_value_domains = await self.scraping_analyzer.identify_high_value_domains(business_unit)
            
            # Generar campañas basadas en análisis
            campaigns = await self._generate_intelligent_campaigns(
                scraping_analysis, high_value_domains
            )
            
            # Optimizar horarios de scraping
            optimized_schedule = await self.scraping_analyzer.optimize_scraping_schedule(business_unit)
            
            # Generar recomendaciones de prospección
            prospecting_recommendations = await self._generate_prospecting_recommendations(
                scraping_analysis, high_value_domains
            )
            
            return {
                'success': True,
                'scraping_analysis': scraping_analysis,
                'high_value_domains': high_value_domains,
                'generated_campaigns': campaigns,
                'optimized_schedule': optimized_schedule,
                'prospecting_recommendations': prospecting_recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analizando y generando campañas: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def predict_domain_opportunities(self, domain: str) -> Dict[str, Any]:
        """
        Predice oportunidades para un dominio específico.
        """
        try:
            # Análisis del dominio
            domain_potential = await self.scraping_analyzer.predict_domain_potential(domain)
            
            if not domain_potential['success']:
                return domain_potential
            
            # Análisis de frecuencia de uso
            usage_analysis = await self._analyze_domain_usage(domain)
            
            # Análisis de cross-selling
            cross_selling_analysis = await self._analyze_cross_selling_potential(domain)
            
            # Generar recomendaciones específicas
            recommendations = await self._generate_domain_recommendations(
                domain_potential, usage_analysis, cross_selling_analysis
            )
            
            return {
                'success': True,
                'domain': domain,
                'potential_analysis': domain_potential,
                'usage_analysis': usage_analysis,
                'cross_selling_analysis': cross_selling_analysis,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error prediciendo oportunidades para dominio {domain}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def optimize_publishing_strategy(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Optimiza la estrategia de publicación basada en datos de scraping.
        """
        try:
            # Obtener datos de scraping
            scraping_data = await self._get_comprehensive_scraping_data(business_unit)
            
            # Analizar patrones de éxito
            success_patterns = await self._analyze_success_patterns(scraping_data)
            
            # Analizar patrones de vacantes
            vacancy_patterns = await self._analyze_vacancy_patterns(scraping_data)
            
            # Analizar patrones temporales
            temporal_patterns = await self._analyze_temporal_patterns(scraping_data)
            
            # Generar estrategia optimizada
            optimized_strategy = await self._generate_optimized_strategy(
                success_patterns, vacancy_patterns, temporal_patterns
            )
            
            # Generar recomendaciones de contenido
            content_recommendations = await self._generate_content_recommendations(
                scraping_data, optimized_strategy
            )
            
            return {
                'success': True,
                'success_patterns': success_patterns,
                'vacancy_patterns': vacancy_patterns,
                'temporal_patterns': temporal_patterns,
                'optimized_strategy': optimized_strategy,
                'content_recommendations': content_recommendations
            }
            
        except Exception as e:
            logger.error(f"Error optimizando estrategia de publicación: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def generate_ml_insights(self, business_unit: str = None) -> Dict[str, Any]:
        """
        Genera insights de ML basados en datos de scraping.
        """
        try:
            # Obtener datos de scraping
            scraping_data = await self._get_comprehensive_scraping_data(business_unit)
            
            # Análisis AURA
            aura_insights = await self._generate_aura_insights(scraping_data)
            
            # Análisis predictivo
            predictive_insights = await self._generate_predictive_insights(scraping_data)
            
            # Análisis de segmentación
            segmentation_insights = await self._generate_segmentation_insights(scraping_data)
            
            # Análisis de tendencias
            trend_insights = await self._generate_trend_insights(scraping_data)
            
            return {
                'success': True,
                'aura_insights': aura_insights,
                'predictive_insights': predictive_insights,
                'segmentation_insights': segmentation_insights,
                'trend_insights': trend_insights
            }
            
        except Exception as e:
            logger.error(f"Error generando insights de ML: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ===== MÉTODOS PRIVADOS =====
    
    async def _generate_intelligent_campaigns(self, scraping_analysis: Dict, 
                                            high_value_domains: Dict) -> List[Dict[str, Any]]:
        """Genera campañas inteligentes basadas en análisis de scraping."""
        campaigns = []
        
        # Campañas para dominios de alto valor
        if high_value_domains['success'] and high_value_domains['high_value_domains']:
            for domain_data in high_value_domains['high_value_domains'][:5]:  # Top 5
                domain = domain_data['domain']
                analysis = domain_data['analysis']
                
                campaign = {
                    'name': f"Campaña Premium - {domain.dominio}",
                    'type': 'premium_domain',
                    'target_domain': domain.dominio,
                    'business_unit': domain.business_units.first().name if domain.business_units.exists() else 'general',
                    'priority': 'high',
                    'budget': analysis['predictions']['potential_value'] * 0.1,  # 10% del valor potencial
                    'duration_days': 30,
                    'channels': ['email', 'linkedin', 'webinar'],
                    'objectives': [
                        'Demostrar valor de GenIA y AURA',
                        'Generar leads cualificados',
                        'Establecer relación estratégica'
                    ],
                    'ml_recommendations': analysis['recommendations']
                }
                campaigns.append(campaign)
        
        # Campañas basadas en patrones de frecuencia
        if scraping_analysis['frequency_patterns']['low_frequency_domains']:
            campaign = {
                'name': 'Campaña de Reactivación',
                'type': 'reactivation',
                'target_segment': 'low_frequency_domains',
                'business_unit': 'general',
                'priority': 'medium',
                'budget': 5000,
                'duration_days': 21,
                'channels': ['email', 'phone', 'linkedin'],
                'objectives': [
                    'Reactivar dominios inactivos',
                    'Incrementar frecuencia de uso',
                    'Identificar nuevas oportunidades'
                ],
                'ml_recommendations': scraping_analysis['recommendations']
            }
            campaigns.append(campaign)
        
        # Campañas basadas en patrones de éxito
        if scraping_analysis['success_patterns']['low_success_domains']:
            campaign = {
                'name': 'Campaña de Optimización',
                'type': 'optimization',
                'target_segment': 'low_success_domains',
                'business_unit': 'general',
                'priority': 'high',
                'budget': 8000,
                'duration_days': 28,
                'channels': ['email', 'webinar', 'consultation'],
                'objectives': [
                    'Optimizar configuración de scraping',
                    'Mejorar tasa de éxito',
                    'Proporcionar soporte técnico'
                ],
                'ml_recommendations': scraping_analysis['recommendations']
            }
            campaigns.append(campaign)
        
        return campaigns
    
    async def _generate_prospecting_recommendations(self, scraping_analysis: Dict, 
                                                  high_value_domains: Dict) -> List[Dict[str, Any]]:
        """Genera recomendaciones de prospección inteligente."""
        recommendations = []
        
        # Recomendaciones para dominios de alto valor
        if high_value_domains['success'] and high_value_domains['high_value_domains']:
            for domain_data in high_value_domains['high_value_domains'][:10]:  # Top 10
                domain = domain_data['domain']
                analysis = domain_data['analysis']
                
                recommendation = {
                    'type': 'high_value_domain',
                    'domain': domain.dominio,
                    'priority': 'critical',
                    'action': 'immediate_contact',
                    'reason': f"Dominio con score de {analysis['composite_score']:.2f}",
                    'recommended_approach': 'direct_outreach',
                    'estimated_value': analysis['predictions']['potential_value'],
                    'timeline': '1-2 semanas',
                    'ml_confidence': analysis['composite_score']
                }
                recommendations.append(recommendation)
        
        # Recomendaciones basadas en patrones de frecuencia
        if scraping_analysis['frequency_patterns']['high_frequency_domains']:
            recommendation = {
                'type': 'frequency_optimization',
                'priority': 'high',
                'action': 'schedule_optimization',
                'reason': 'Dominios con alta frecuencia de scraping',
                'recommended_approach': 'automated_scheduling',
                'estimated_value': 15000,
                'timeline': '1 semana',
                'ml_confidence': 0.85
            }
            recommendations.append(recommendation)
        
        # Recomendaciones basadas en patrones de vacantes
        if scraping_analysis['vacancy_patterns']['high_vacancy_domains']:
            recommendation = {
                'type': 'vacancy_opportunity',
                'priority': 'high',
                'action': 'content_campaign',
                'reason': 'Dominios con alto volumen de vacantes',
                'recommended_approach': 'targeted_content',
                'estimated_value': 25000,
                'timeline': '2-3 semanas',
                'ml_confidence': 0.90
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _analyze_domain_usage(self, domain: str) -> Dict[str, Any]:
        """Analiza el uso de un dominio específico."""
        try:
            # Obtener datos del dominio
            dominio = await DominioScraping.objects.filter(dominio=domain).afirst()
            if not dominio:
                return {'success': False, 'error': 'Dominio no encontrado'}
            
            # Obtener registros de scraping
            registros = await RegistroScraping.objects.filter(
                dominio=dominio
            ).order_by('-fecha_inicio').all()
            
            # Calcular métricas de uso
            total_registros = len(registros)
            registros_exitosos = len([r for r in registros if r.estado == 'exitoso'])
            tasa_exito = registros_exitosos / max(total_registros, 1)
            
            # Análisis de frecuencia
            if total_registros > 0:
                primer_registro = registros[-1].fecha_inicio
                ultimo_registro = registros[0].fecha_inicio
                dias_activo = (ultimo_registro - primer_registro).days
                frecuencia_promedio = total_registros / max(dias_activo, 1)
            else:
                frecuencia_promedio = 0
            
            # Análisis de tendencias
            registros_ultimo_mes = [r for r in registros if r.fecha_inicio >= timezone.now() - timedelta(days=30)]
            frecuencia_ultimo_mes = len(registros_ultimo_mes)
            
            return {
                'success': True,
                'total_registros': total_registros,
                'registros_exitosos': registros_exitosos,
                'tasa_exito': tasa_exito,
                'frecuencia_promedio': frecuencia_promedio,
                'frecuencia_ultimo_mes': frecuencia_ultimo_mes,
                'tendencia': 'increasing' if frecuencia_ultimo_mes > frecuencia_promedio else 'decreasing'
            }
            
        except Exception as e:
            logger.error(f"Error analizando uso del dominio {domain}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _analyze_cross_selling_potential(self, domain: str) -> Dict[str, Any]:
        """Analiza el potencial de cross-selling para un dominio."""
        try:
            # Obtener datos del dominio
            dominio = await DominioScraping.objects.filter(dominio=domain).afirst()
            if not dominio:
                return {'success': False, 'error': 'Dominio no encontrado'}
            
            # Obtener vacantes del dominio
            vacantes = await Vacante.objects.filter(dominio_scraping=dominio).all()
            
            # Analizar tipos de vacantes
            tipos_vacantes = {}
            for vacante in vacantes:
                tipo = vacante.tipo_vacante if hasattr(vacante, 'tipo_vacante') else 'general'
                if tipo not in tipos_vacantes:
                    tipos_vacantes[tipo] = 0
                tipos_vacantes[tipo] += 1
            
            # Calcular potencial de cross-selling
            total_vacantes = len(vacantes)
            diversidad_vacantes = len(tipos_vacantes)
            
            # Score de potencial (0-1)
            potencial_score = min((total_vacantes * diversidad_vacantes) / 100, 1.0)
            
            # Servicios recomendados
            servicios_recomendados = []
            if total_vacantes > 50:
                servicios_recomendados.append('GenIA para screening masivo')
            if diversidad_vacantes > 3:
                servicios_recomendados.append('AURA para matching avanzado')
            if total_vacantes > 100:
                servicios_recomendados.append('Chatbot personalizado')
            
            return {
                'success': True,
                'total_vacantes': total_vacantes,
                'diversidad_vacantes': diversidad_vacantes,
                'tipos_vacantes': tipos_vacantes,
                'potencial_score': potencial_score,
                'servicios_recomendados': servicios_recomendados,
                'estimated_value': potencial_score * 20000  # Valor base $20,000
            }
            
        except Exception as e:
            logger.error(f"Error analizando cross-selling para dominio {domain}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _generate_domain_recommendations(self, domain_potential: Dict, 
                                             usage_analysis: Dict, 
                                             cross_selling_analysis: Dict) -> List[str]:
        """Genera recomendaciones específicas para un dominio."""
        recommendations = []
        
        if domain_potential['success']:
            potential = domain_potential['composite_score']
            
            if potential >= 0.8:
                recommendations.extend([
                    "Dominio de alto potencial - Priorizar en estrategia de marketing",
                    "Implementar campaña premium con demostración personalizada",
                    "Asignar ejecutivo de cuenta senior"
                ])
            elif potential >= 0.6:
                recommendations.extend([
                    "Dominio de potencial medio - Incluir en campañas de nurturing",
                    "Programar demostración de productos",
                    "Enviar contenido educativo personalizado"
                ])
        
        if usage_analysis['success']:
            if usage_analysis['tendencia'] == 'decreasing':
                recommendations.append("Frecuencia de uso decreciente - Implementar campaña de reactivación")
            
            if usage_analysis['tasa_exito'] < 0.7:
                recommendations.append("Baja tasa de éxito - Ofrecer soporte técnico y optimización")
        
        if cross_selling_analysis['success']:
            if cross_selling_analysis['potencial_score'] > 0.7:
                recommendations.extend([
                    "Alto potencial de cross-selling - Desarrollar propuesta personalizada",
                    f"Servicios recomendados: {', '.join(cross_selling_analysis['servicios_recomendados'])}"
                ])
        
        return recommendations
    
    async def _get_comprehensive_scraping_data(self, business_unit: str = None) -> List[Dict[str, Any]]:
        """Obtiene datos comprehensivos de scraping."""
        query = DominioScraping.objects.all()
        
        if business_unit:
            query = query.filter(business_units__name=business_unit)
        
        domains = await query.all()
        comprehensive_data = []
        
        for domain in domains:
            # Obtener registros de scraping
            registros = await RegistroScraping.objects.filter(dominio=domain).all()
            
            # Obtener vacantes
            vacantes = await Vacante.objects.filter(dominio_scraping=domain).all()
            
            # Calcular métricas
            total_registros = len(registros)
            registros_exitosos = len([r for r in registros if r.estado == 'exitoso'])
            tasa_exito = registros_exitosos / max(total_registros, 1)
            
            comprehensive_data.append({
                'domain': domain,
                'registros': list(registros),
                'vacantes': list(vacantes),
                'total_registros': total_registros,
                'total_vacantes': len(vacantes),
                'tasa_exito': tasa_exito,
                'ultimo_registro': max([r.fecha_inicio for r in registros]) if registros else None,
                'primer_registro': min([r.fecha_inicio for r in registros]) if registros else None
            })
        
        return comprehensive_data
    
    async def _analyze_success_patterns(self, scraping_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza patrones de éxito en scraping."""
        patterns = {
            'high_success_domains': [],
            'low_success_domains': [],
            'success_factors': {},
            'failure_reasons': {}
        }
        
        success_rates = []
        for data in scraping_data:
            success_rate = data['tasa_exito']
            success_rates.append(success_rate)
            
            if success_rate > 0.8:
                patterns['high_success_domains'].append({
                    'domain': data['domain'].dominio,
                    'success_rate': success_rate,
                    'total_registros': data['total_registros']
                })
            elif success_rate < 0.5:
                patterns['low_success_domains'].append({
                    'domain': data['domain'].dominio,
                    'success_rate': success_rate,
                    'total_registros': data['total_registros']
                })
        
        if success_rates:
            patterns['avg_success_rate'] = sum(success_rates) / len(success_rates)
        
        return patterns
    
    async def _analyze_vacancy_patterns(self, scraping_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza patrones de vacantes."""
        patterns = {
            'high_vacancy_domains': [],
            'low_vacancy_domains': [],
            'vacancy_trends': {},
            'industry_distribution': {}
        }
        
        vacancy_counts = []
        for data in scraping_data:
            vacancy_count = data['total_vacantes']
            vacancy_counts.append(vacancy_count)
            
            if vacancy_count > 50:
                patterns['high_vacancy_domains'].append({
                    'domain': data['domain'].dominio,
                    'vacancy_count': vacancy_count
                })
            elif vacancy_count < 10:
                patterns['low_vacancy_domains'].append({
                    'domain': data['domain'].dominio,
                    'vacancy_count': vacancy_count
                })
        
        if vacancy_counts:
            patterns['avg_vacancy_count'] = sum(vacancy_counts) / len(vacancy_counts)
        
        return patterns
    
    async def _analyze_temporal_patterns(self, scraping_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza patrones temporales."""
        patterns = {
            'hourly_distribution': {},
            'daily_distribution': {},
            'seasonal_patterns': {},
            'optimal_times': []
        }
        
        # Agrupar por hora y día
        for data in scraping_data:
            for registro in data['registros']:
                hora = registro.fecha_inicio.hour
                dia = registro.fecha_inicio.weekday()
                
                if hora not in patterns['hourly_distribution']:
                    patterns['hourly_distribution'][hora] = 0
                patterns['hourly_distribution'][hora] += 1
                
                if dia not in patterns['daily_distribution']:
                    patterns['daily_distribution'][dia] = 0
                patterns['daily_distribution'][dia] += 1
        
        # Encontrar horarios óptimos
        if patterns['hourly_distribution']:
            best_hours = sorted(patterns['hourly_distribution'].items(), 
                              key=lambda x: x[1], reverse=True)[:3]
            patterns['optimal_times'] = [hora for hora, _ in best_hours]
        
        return patterns
    
    async def _generate_optimized_strategy(self, success_patterns: Dict, 
                                         vacancy_patterns: Dict, 
                                         temporal_patterns: Dict) -> Dict[str, Any]:
        """Genera estrategia optimizada basada en patrones."""
        strategy = {
            'priority_domains': [],
            'optimal_schedule': {},
            'content_strategy': {},
            'channel_strategy': {}
        }
        
        # Dominios prioritarios
        strategy['priority_domains'] = (
            success_patterns['high_success_domains'][:10] + 
            vacancy_patterns['high_vacancy_domains'][:10]
        )
        
        # Horario óptimo
        strategy['optimal_schedule'] = {
            'best_hours': temporal_patterns['optimal_times'],
            'best_days': [0, 1, 2, 3, 4],  # Lunes a Viernes
            'frequency': 'daily' if len(temporal_patterns['optimal_times']) >= 2 else 'weekly'
        }
        
        # Estrategia de contenido
        strategy['content_strategy'] = {
            'high_value_domains': 'contenido_premium',
            'low_success_domains': 'contenido_educativo',
            'high_vacancy_domains': 'contenido_especifico'
        }
        
        # Estrategia de canales
        strategy['channel_strategy'] = {
            'email': 'nurturing_y_educacion',
            'linkedin': 'networking_y_demostraciones',
            'webinar': 'producto_y_casos_uso',
            'phone': 'seguimiento_personalizado'
        }
        
        return strategy
    
    async def _generate_content_recommendations(self, scraping_data: List[Dict[str, Any]], 
                                              optimized_strategy: Dict) -> List[Dict[str, Any]]:
        """Genera recomendaciones de contenido."""
        recommendations = []
        
        # Contenido para dominios de alto valor
        high_value_domains = optimized_strategy['priority_domains'][:5]
        for domain_data in high_value_domains:
            recommendation = {
                'type': 'premium_content',
                'target_domain': domain_data['domain'],
                'content_type': 'case_study',
                'title': f"Casos de éxito: {domain_data['domain']}",
                'description': 'Demostración de valor con GenIA y AURA',
                'channels': ['email', 'linkedin', 'webinar'],
                'priority': 'high'
            }
            recommendations.append(recommendation)
        
        # Contenido educativo
        recommendation = {
            'type': 'educational_content',
            'content_type': 'webinar',
            'title': 'Optimización de Scraping con ML',
            'description': 'Mejora tus resultados con inteligencia artificial',
            'channels': ['email', 'linkedin'],
            'priority': 'medium'
        }
        recommendations.append(recommendation)
        
        # Contenido técnico
        recommendation = {
            'type': 'technical_content',
            'content_type': 'guide',
            'title': 'Guía de mejores prácticas',
            'description': 'Maximiza el éxito de tu scraping',
            'channels': ['email', 'blog'],
            'priority': 'medium'
        }
        recommendations.append(recommendation)
        
        return recommendations
    
    async def _generate_aura_insights(self, scraping_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Genera insights de AURA basados en datos de scraping."""
        insights = {
            'compatibility_scores': [],
            'vibrational_patterns': [],
            'predictions': []
        }
        
        for data in scraping_data:
            # Calcular compatibilidad AURA
            compatibility = await self.vibrational_matcher.calculate_compatibility_score(
                {
                    'domain': data['domain'].dominio,
                    'success_rate': data['tasa_exito'],
                    'vacancy_count': data['total_vacantes']
                },
                'scraping_domain'
            )
            
            insights['compatibility_scores'].append({
                'domain': data['domain'].dominio,
                'score': compatibility
            })
            
            # Predicciones AURA
            predictions = await self.aura_engine.predict_business_outcomes({
                'domain': data['domain'].dominio,
                'scraping_frequency': data['total_registros'],
                'vacancy_count': data['total_vacantes'],
                'success_rate': data['tasa_exito']
            })
            
            insights['predictions'].append({
                'domain': data['domain'].dominio,
                'predictions': predictions
            })
        
        return insights
    
    async def _generate_predictive_insights(self, scraping_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Genera insights predictivos."""
        insights = {
            'success_predictions': [],
            'vacancy_predictions': [],
            'trend_predictions': []
        }
        
        # Predicciones de éxito
        for data in scraping_data:
            if data['total_registros'] > 10:  # Solo dominios con suficientes datos
                # Predicción basada en tendencia
                recent_success = data['tasa_exito']
                predicted_success = min(recent_success * 1.1, 1.0)  # Mejora del 10%
                
                insights['success_predictions'].append({
                    'domain': data['domain'].dominio,
                    'current_success': recent_success,
                    'predicted_success': predicted_success,
                    'confidence': 0.8
                })
        
        # Predicciones de vacantes
        for data in scraping_data:
            if data['total_vacantes'] > 0:
                avg_vacancies_per_scraping = data['total_vacantes'] / max(data['total_registros'], 1)
                predicted_vacancies = avg_vacancies_per_scraping * 5  # Próximas 5 sesiones
                
                insights['vacancy_predictions'].append({
                    'domain': data['domain'].dominio,
                    'current_avg': avg_vacancies_per_scraping,
                    'predicted_total': predicted_vacancies,
                    'confidence': 0.7
                })
        
        return insights
    
    async def _generate_segmentation_insights(self, scraping_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Genera insights de segmentación."""
        insights = {
            'segments': {},
            'recommendations': []
        }
        
        # Segmentar por frecuencia
        high_frequency = [d for d in scraping_data if d['total_registros'] > 20]
        medium_frequency = [d for d in scraping_data if 5 <= d['total_registros'] <= 20]
        low_frequency = [d for d in scraping_data if d['total_registros'] < 5]
        
        insights['segments']['frequency'] = {
            'high': len(high_frequency),
            'medium': len(medium_frequency),
            'low': len(low_frequency)
        }
        
        # Segmentar por éxito
        high_success = [d for d in scraping_data if d['tasa_exito'] > 0.8]
        medium_success = [d for d in scraping_data if 0.5 <= d['tasa_exito'] <= 0.8]
        low_success = [d for d in scraping_data if d['tasa_exito'] < 0.5]
        
        insights['segments']['success'] = {
            'high': len(high_success),
            'medium': len(medium_success),
            'low': len(low_success)
        }
        
        # Recomendaciones por segmento
        if len(high_frequency) > 0:
            insights['recommendations'].append({
                'segment': 'high_frequency',
                'action': 'optimize_schedule',
                'priority': 'high'
            })
        
        if len(low_success) > 0:
            insights['recommendations'].append({
                'segment': 'low_success',
                'action': 'provide_support',
                'priority': 'critical'
            })
        
        return insights
    
    async def _generate_trend_insights(self, scraping_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Genera insights de tendencias."""
        insights = {
            'growth_trends': [],
            'decline_trends': [],
            'seasonal_patterns': {}
        }
        
        # Analizar tendencias por dominio
        for data in scraping_data:
            if data['total_registros'] > 5:  # Solo dominios con suficientes datos
                # Calcular tendencia basada en éxito reciente vs histórico
                recent_registros = [r for r in data['registros'] 
                                  if r.fecha_inicio >= timezone.now() - timedelta(days=30)]
                recent_success = len([r for r in recent_registros if r.estado == 'exitoso']) / max(len(recent_registros), 1)
                
                if recent_success > data['tasa_exito'] * 1.2:  # Mejora del 20%
                    insights['growth_trends'].append({
                        'domain': data['domain'].dominio,
                        'improvement': recent_success - data['tasa_exito']
                    })
                elif recent_success < data['tasa_exito'] * 0.8:  # Deterioro del 20%
                    insights['decline_trends'].append({
                        'domain': data['domain'].dominio,
                        'decline': data['tasa_exito'] - recent_success
                    })
        
        return insights 