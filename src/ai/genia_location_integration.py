"""
🎯 GenIA Location Integration - HuntRED® v2
Integración avanzada entre GenIA Matchmaking y Location Analytics
Incluye análisis de ubicación, tráfico y movilidad en el matching
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from .genia_advanced_matchmaking import GeniaAdvancedMatchmaking, MatchingResult
from ..services.location_analytics_service import get_location_service, LocationAnalyticsService

logger = logging.getLogger(__name__)

@dataclass
class LocationEnhancedMatchingResult:
    """Resultado de matching mejorado con análisis de ubicación"""
    base_matching_result: MatchingResult
    location_analysis: Dict[str, Any]
    commute_feasibility: Dict[str, Any]
    transport_recommendations: List[Dict[str, Any]]
    work_flexibility_score: float
    location_adjusted_score: float
    geographic_insights: List[str]

class GeniaLocationIntegration:
    """
    Integración avanzada entre GenIA y Location Analytics
    """
    
    def __init__(self, db, redis_client):
        self.db = db
        self.redis_client = redis_client
        
        # Inicializar componentes
        self.genia_engine = GeniaAdvancedMatchmaking()
        self.location_service = get_location_service(db, redis_client)
        
        # Pesos para ajuste de score por ubicación
        self.location_weight_by_business_unit = {
            'huntred_executive': 0.25,    # Ubicación muy importante para ejecutivos
            'huntred_general': 0.20,      # Importante para profesionales
            'huntU': 0.15,                # Menos crítico para estudiantes
            'amigro': 0.10                # Flexible para base de pirámide
        }
        
        # Configuraciones de análisis por unidad de negocio
        self.analysis_config = {
            'huntred_executive': {
                'max_commute_tolerance': 90,      # minutos
                'stress_threshold': 6.0,          # score máximo aceptable
                'cost_sensitivity': 0.3,          # peso del costo
                'flexibility_preference': 0.7     # preferencia por flexibilidad
            },
            'huntred_general': {
                'max_commute_tolerance': 75,
                'stress_threshold': 7.0,
                'cost_sensitivity': 0.4,
                'flexibility_preference': 0.6
            },
            'huntU': {
                'max_commute_tolerance': 60,
                'stress_threshold': 8.0,
                'cost_sensitivity': 0.6,          # Más sensible al costo
                'flexibility_preference': 0.4
            },
            'amigro': {
                'max_commute_tolerance': 120,     # Más tolerante
                'stress_threshold': 8.5,
                'cost_sensitivity': 0.7,          # Muy sensible al costo
                'flexibility_preference': 0.3
            }
        }
        
        self.initialized = False
    
    async def initialize_integration(self):
        """Inicializar la integración"""
        if self.initialized:
            return
            
        logger.info("🎯 Inicializando GenIA Location Integration...")
        
        # Inicializar componentes
        await self.genia_engine.initialize_matching_engine()
        await self.location_service.initialize_service()
        
        self.initialized = True
        logger.info("✅ GenIA Location Integration inicializado")
    
    async def perform_location_enhanced_matching(self,
                                               candidate_data: Dict[str, Any],
                                               job_requirements: Dict[str, Any],
                                               business_unit_id: str,
                                               include_commute_analysis: bool = True) -> LocationEnhancedMatchingResult:
        """
        Realizar matching mejorado con análisis de ubicación
        
        Args:
            candidate_data: Datos del candidato
            job_requirements: Requerimientos del trabajo
            business_unit_id: ID de la unidad de negocio
            include_commute_analysis: Si incluir análisis detallado de commute
            
        Returns:
            Resultado de matching mejorado con ubicación
        """
        
        if not self.initialized:
            await self.initialize_integration()
        
        try:
            logger.info(f"🎯 Iniciando matching con ubicación para {candidate_data.get('id', 'unknown')}")
            
            # 1. Realizar matching base con GenIA
            base_result = await self.genia_engine.perform_advanced_matching(
                candidate_data, job_requirements
            )
            
            # 2. Análisis de ubicación
            location_analysis = await self._analyze_location_compatibility(
                candidate_data, job_requirements, business_unit_id
            )
            
            # 3. Análisis de commute si está habilitado
            commute_analysis = {}
            if include_commute_analysis and candidate_data.get('address'):
                commute_analysis = await self._analyze_commute_detailed(
                    candidate_data['address'], business_unit_id
                )
            
            # 4. Generar recomendaciones de transporte
            transport_recommendations = await self._generate_transport_recommendations(
                location_analysis, commute_analysis, business_unit_id
            )
            
            # 5. Calcular score de flexibilidad laboral
            flexibility_score = await self._calculate_work_flexibility_score(
                location_analysis, commute_analysis, business_unit_id
            )
            
            # 6. Ajustar score base con factores de ubicación
            location_adjusted_score = await self._adjust_score_with_location(
                base_result.overall_score, location_analysis, business_unit_id
            )
            
            # 7. Generar insights geográficos
            geographic_insights = await self._generate_geographic_insights(
                location_analysis, commute_analysis, business_unit_id
            )
            
            # 8. Crear resultado integrado
            enhanced_result = LocationEnhancedMatchingResult(
                base_matching_result=base_result,
                location_analysis=location_analysis,
                commute_feasibility=commute_analysis,
                transport_recommendations=transport_recommendations,
                work_flexibility_score=flexibility_score,
                location_adjusted_score=location_adjusted_score,
                geographic_insights=geographic_insights
            )
            
            logger.info(f"✅ Matching con ubicación completado: Score ajustado {location_adjusted_score:.1%}")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ Error en matching con ubicación: {e}")
            raise
    
    async def _analyze_location_compatibility(self,
                                            candidate_data: Dict[str, Any],
                                            job_requirements: Dict[str, Any],
                                            business_unit_id: str) -> Dict[str, Any]:
        """Analizar compatibilidad de ubicación"""
        
        candidate_address = candidate_data.get('address', '')
        job_location = job_requirements.get('location', '')
        
        if not candidate_address or not job_location:
            return {
                'compatibility_score': 0.5,
                'analysis_available': False,
                'reason': 'Información de ubicación incompleta'
            }
        
        try:
            # Obtener insights de ubicación del servicio
            location_insights = await self.location_service.get_location_insights_for_matching(
                candidate_address, job_location, business_unit_id
            )
            
            return {
                'compatibility_score': location_insights.get('location_match_score', 0.5),
                'analysis_available': True,
                'commute_feasible': location_insights.get('commute_feasible', False),
                'commute_time_minutes': location_insights.get('commute_time_minutes', 0),
                'commute_distance_km': location_insights.get('commute_distance_km', 0),
                'monthly_cost': location_insights.get('monthly_commute_cost', 0),
                'stress_score': location_insights.get('stress_score', 5.0),
                'recommended_transport': location_insights.get('recommended_transport', 'driving'),
                'flexibility_recommendation': location_insights.get('work_flexibility_recommendation', 'office_work_optimal'),
                'insights': location_insights.get('insights', [])
            }
            
        except Exception as e:
            logger.error(f"❌ Error analizando compatibilidad de ubicación: {e}")
            return {
                'compatibility_score': 0.5,
                'analysis_available': False,
                'reason': f'Error en análisis: {str(e)}'
            }
    
    async def _analyze_commute_detailed(self,
                                      candidate_address: str,
                                      business_unit_id: str) -> Dict[str, Any]:
        """Análisis detallado de commute"""
        
        try:
            commute_analysis = await self.location_service.analyze_commute_comprehensive(
                candidate_address, business_unit_id
            )
            
            if not commute_analysis:
                return {
                    'analysis_available': False,
                    'reason': 'No se pudo analizar el commute'
                }
            
            return {
                'analysis_available': True,
                'morning_commute': {
                    'duration_minutes': commute_analysis.morning_commute.duration_minutes,
                    'duration_with_traffic': commute_analysis.morning_commute.duration_in_traffic_minutes,
                    'distance_km': commute_analysis.morning_commute.distance_km,
                    'route_quality': commute_analysis.morning_commute.route_quality,
                    'transport_mode': commute_analysis.morning_commute.transport_mode
                },
                'evening_commute': {
                    'duration_minutes': commute_analysis.evening_commute.duration_minutes,
                    'duration_with_traffic': commute_analysis.evening_commute.duration_in_traffic_minutes,
                    'distance_km': commute_analysis.evening_commute.distance_km,
                    'route_quality': commute_analysis.evening_commute.route_quality,
                    'transport_mode': commute_analysis.evening_commute.transport_mode
                },
                'costs': {
                    'weekly': commute_analysis.weekly_commute_cost,
                    'monthly': commute_analysis.monthly_commute_cost
                },
                'stress_score': commute_analysis.commute_stress_score,
                'recommended_transport': commute_analysis.recommended_transport,
                'flexibility_recommendation': commute_analysis.flexible_work_recommendation
            }
            
        except Exception as e:
            logger.error(f"❌ Error en análisis detallado de commute: {e}")
            return {
                'analysis_available': False,
                'reason': f'Error en análisis: {str(e)}'
            }
    
    async def _generate_transport_recommendations(self,
                                                location_analysis: Dict[str, Any],
                                                commute_analysis: Dict[str, Any],
                                                business_unit_id: str) -> List[Dict[str, Any]]:
        """Generar recomendaciones de transporte"""
        
        recommendations = []
        
        if not location_analysis.get('analysis_available', False):
            return recommendations
        
        # Configuración para la unidad de negocio
        config = self.analysis_config.get(business_unit_id, self.analysis_config['huntred_general'])
        
        # Recomendación principal
        primary_transport = location_analysis.get('recommended_transport', 'driving')
        recommendations.append({
            'type': 'primary',
            'mode': primary_transport,
            'reason': f'Modo de transporte óptimo para esta distancia',
            'estimated_time': location_analysis.get('commute_time_minutes', 0) // 2,
            'estimated_cost_monthly': location_analysis.get('monthly_cost', 0),
            'stress_level': location_analysis.get('stress_score', 5.0)
        })
        
        # Recomendaciones alternativas
        commute_time = location_analysis.get('commute_time_minutes', 0)
        commute_distance = location_analysis.get('commute_distance_km', 0)
        
        # Transporte público como alternativa
        if primary_transport != 'transit' and commute_distance <= 25:
            recommendations.append({
                'type': 'alternative',
                'mode': 'transit',
                'reason': 'Opción más económica y sustentable',
                'estimated_time': int(commute_time * 1.3),  # 30% más tiempo
                'estimated_cost_monthly': location_analysis.get('monthly_cost', 0) * 0.4,
                'stress_level': max(1.0, location_analysis.get('stress_score', 5.0) - 1.0)
            })
        
        # Bicicleta para distancias cortas
        if commute_distance <= 8:
            recommendations.append({
                'type': 'alternative',
                'mode': 'bicycling',
                'reason': 'Opción saludable y económica',
                'estimated_time': int(commute_distance * 4),  # ~15 km/h
                'estimated_cost_monthly': 200,  # Costo mínimo
                'stress_level': 2.0,
                'benefits': ['Ejercicio', 'Cero emisiones', 'Bajo costo']
            })
        
        # Caminata para distancias muy cortas
        if commute_distance <= 3:
            recommendations.append({
                'type': 'alternative',
                'mode': 'walking',
                'reason': 'Opción más saludable',
                'estimated_time': int(commute_distance * 12),  # ~5 km/h
                'estimated_cost_monthly': 0,
                'stress_level': 1.0,
                'benefits': ['Ejercicio', 'Cero costo', 'Cero emisiones']
            })
        
        return recommendations
    
    async def _calculate_work_flexibility_score(self,
                                              location_analysis: Dict[str, Any],
                                              commute_analysis: Dict[str, Any],
                                              business_unit_id: str) -> float:
        """Calcular score de flexibilidad laboral recomendada"""
        
        if not location_analysis.get('analysis_available', False):
            return 0.5
        
        flexibility_recommendation = location_analysis.get('flexibility_recommendation', 'office_work_optimal')
        
        # Mapear recomendaciones a scores
        flexibility_scores = {
            'remote_work_recommended': 0.9,
            'hybrid_work_recommended': 0.7,
            'flexible_hours_recommended': 0.5,
            'office_work_optimal': 0.3
        }
        
        base_score = flexibility_scores.get(flexibility_recommendation, 0.5)
        
        # Ajustar según factores adicionales
        adjustments = []
        
        # Tiempo de commute
        commute_time = location_analysis.get('commute_time_minutes', 0)
        if commute_time > 120:
            adjustments.append(0.2)  # Incrementar flexibilidad
        elif commute_time > 90:
            adjustments.append(0.1)
        
        # Costo de transporte
        monthly_cost = location_analysis.get('monthly_cost', 0)
        if monthly_cost > 4000:
            adjustments.append(0.15)
        elif monthly_cost > 2000:
            adjustments.append(0.05)
        
        # Estrés de commute
        stress_score = location_analysis.get('stress_score', 5.0)
        if stress_score > 7:
            adjustments.append(0.2)
        elif stress_score > 5:
            adjustments.append(0.1)
        
        # Aplicar ajustes
        final_score = base_score + sum(adjustments)
        return min(1.0, max(0.0, final_score))
    
    async def _adjust_score_with_location(self,
                                        base_score: float,
                                        location_analysis: Dict[str, Any],
                                        business_unit_id: str) -> float:
        """Ajustar score base con factores de ubicación"""
        
        if not location_analysis.get('analysis_available', False):
            return base_score
        
        # Obtener peso de ubicación para la unidad de negocio
        location_weight = self.location_weight_by_business_unit.get(business_unit_id, 0.15)
        
        # Score de compatibilidad de ubicación
        location_compatibility = location_analysis.get('compatibility_score', 0.5)
        
        # Factores de penalización/bonificación
        adjustments = []
        
        # Commute factible
        if location_analysis.get('commute_feasible', False):
            adjustments.append(0.05)  # Bonificación por commute factible
        else:
            adjustments.append(-0.1)  # Penalización por commute no factible
        
        # Tiempo de commute
        commute_time = location_analysis.get('commute_time_minutes', 0)
        config = self.analysis_config.get(business_unit_id, self.analysis_config['huntred_general'])
        
        if commute_time <= config['max_commute_tolerance'] * 0.5:
            adjustments.append(0.05)  # Bonificación por commute corto
        elif commute_time > config['max_commute_tolerance']:
            adjustments.append(-0.15)  # Penalización por commute largo
        
        # Estrés de commute
        stress_score = location_analysis.get('stress_score', 5.0)
        if stress_score <= config['stress_threshold'] * 0.6:
            adjustments.append(0.03)  # Bonificación por bajo estrés
        elif stress_score > config['stress_threshold']:
            adjustments.append(-0.08)  # Penalización por alto estrés
        
        # Costo de transporte
        monthly_cost = location_analysis.get('monthly_cost', 0)
        cost_sensitivity = config['cost_sensitivity']
        
        if monthly_cost <= 1500:
            adjustments.append(0.02 * cost_sensitivity)  # Bonificación por bajo costo
        elif monthly_cost > 5000:
            adjustments.append(-0.05 * cost_sensitivity)  # Penalización por alto costo
        
        # Calcular score ajustado
        location_factor = location_compatibility + sum(adjustments)
        location_factor = max(0.0, min(1.0, location_factor))
        
        # Aplicar peso de ubicación
        adjusted_score = base_score * (1 - location_weight) + location_factor * location_weight
        
        return min(1.0, max(0.0, adjusted_score))
    
    async def _generate_geographic_insights(self,
                                          location_analysis: Dict[str, Any],
                                          commute_analysis: Dict[str, Any],
                                          business_unit_id: str) -> List[str]:
        """Generar insights geográficos"""
        
        insights = []
        
        if not location_analysis.get('analysis_available', False):
            insights.append("Análisis de ubicación no disponible")
            return insights
        
        # Insights de ubicación base
        base_insights = location_analysis.get('insights', [])
        insights.extend(base_insights)
        
        # Insights específicos por unidad de negocio
        config = self.analysis_config.get(business_unit_id, self.analysis_config['huntred_general'])
        
        commute_time = location_analysis.get('commute_time_minutes', 0)
        monthly_cost = location_analysis.get('monthly_cost', 0)
        stress_score = location_analysis.get('stress_score', 5.0)
        
        # Insights de tiempo
        if commute_time <= config['max_commute_tolerance'] * 0.5:
            insights.append(f"Ubicación óptima para {business_unit_id} - commute muy eficiente")
        elif commute_time > config['max_commute_tolerance']:
            insights.append(f"Ubicación desafiante para {business_unit_id} - considerar trabajo remoto")
        
        # Insights de costo
        if config['cost_sensitivity'] > 0.5:  # Unidades sensibles al costo
            if monthly_cost <= 2000:
                insights.append("Costo de transporte muy favorable")
            elif monthly_cost > 4000:
                insights.append("Costo de transporte significativo - evaluar alternativas")
        
        # Insights de estrés
        if stress_score > config['stress_threshold']:
            insights.append("Commute de alto estrés - recomendar flexibilidad laboral")
        elif stress_score <= 3.0:
            insights.append("Commute de bajo estrés - excelente calidad de vida")
        
        # Insights de flexibilidad
        flexibility_rec = location_analysis.get('flexibility_recommendation', '')
        if flexibility_rec == 'remote_work_recommended':
            insights.append("Candidato ideal para trabajo remoto")
        elif flexibility_rec == 'hybrid_work_recommended':
            insights.append("Candidato ideal para modelo híbrido")
        
        # Insights de transporte
        recommended_transport = location_analysis.get('recommended_transport', '')
        if recommended_transport == 'transit':
            insights.append("Excelente acceso a transporte público")
        elif recommended_transport == 'walking':
            insights.append("Ubicación premium - caminable a la oficina")
        elif recommended_transport == 'bicycling':
            insights.append("Ubicación bike-friendly - opción sustentable")
        
        return insights
    
    async def batch_location_matching(self,
                                    candidates_data: List[Dict[str, Any]],
                                    job_requirements: Dict[str, Any],
                                    business_unit_id: str) -> List[LocationEnhancedMatchingResult]:
        """Procesar múltiples candidatos con análisis de ubicación"""
        
        logger.info(f"🎯 Procesando {len(candidates_data)} candidatos con análisis de ubicación")
        
        results = []
        
        # Procesar en lotes para optimizar rendimiento
        batch_size = 10
        for i in range(0, len(candidates_data), batch_size):
            batch = candidates_data[i:i + batch_size]
            
            # Procesar lote en paralelo
            batch_tasks = [
                self.perform_location_enhanced_matching(
                    candidate, job_requirements, business_unit_id
                )
                for candidate in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Filtrar errores y agregar resultados válidos
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"❌ Error procesando candidato: {result}")
                else:
                    results.append(result)
        
        # Ordenar por score ajustado
        results.sort(key=lambda x: x.location_adjusted_score, reverse=True)
        
        logger.info(f"✅ Procesamiento completado: {len(results)} candidatos analizados")
        return results
    
    async def get_location_matching_summary(self,
                                          results: List[LocationEnhancedMatchingResult],
                                          business_unit_id: str) -> Dict[str, Any]:
        """Generar resumen de matching con ubicación"""
        
        if not results:
            return {
                'total_candidates': 0,
                'summary': 'No hay candidatos para analizar'
            }
        
        # Estadísticas generales
        total_candidates = len(results)
        feasible_commutes = sum(1 for r in results if r.location_analysis.get('commute_feasible', False))
        
        # Distribución de scores
        scores = [r.location_adjusted_score for r in results]
        avg_score = sum(scores) / len(scores)
        
        # Distribución de tiempos de commute
        commute_times = [r.location_analysis.get('commute_time_minutes', 0) for r in results]
        avg_commute = sum(commute_times) / len(commute_times)
        
        # Distribución de costos
        costs = [r.location_analysis.get('monthly_cost', 0) for r in results]
        avg_cost = sum(costs) / len(costs)
        
        # Recomendaciones de flexibilidad
        flexibility_recommendations = {}
        for result in results:
            flex_rec = result.location_analysis.get('flexibility_recommendation', 'office_work_optimal')
            flexibility_recommendations[flex_rec] = flexibility_recommendations.get(flex_rec, 0) + 1
        
        # Modos de transporte recomendados
        transport_modes = {}
        for result in results:
            transport = result.location_analysis.get('recommended_transport', 'driving')
            transport_modes[transport] = transport_modes.get(transport, 0) + 1
        
        return {
            'total_candidates': total_candidates,
            'feasible_commutes': feasible_commutes,
            'feasible_percentage': (feasible_commutes / total_candidates) * 100,
            'average_score': round(avg_score, 3),
            'average_commute_minutes': round(avg_commute, 1),
            'average_monthly_cost': round(avg_cost, 2),
            'top_candidates': [
                {
                    'candidate_id': r.base_matching_result.candidate_id,
                    'adjusted_score': r.location_adjusted_score,
                    'commute_time': r.location_analysis.get('commute_time_minutes', 0),
                    'monthly_cost': r.location_analysis.get('monthly_cost', 0),
                    'flexibility_score': r.work_flexibility_score
                }
                for r in results[:5]  # Top 5
            ],
            'flexibility_distribution': flexibility_recommendations,
            'transport_distribution': transport_modes,
            'business_unit_config': self.analysis_config.get(business_unit_id, {})
        }

# Instancia global
genia_location_integration = None

def get_genia_location_integration(db, redis_client) -> GeniaLocationIntegration:
    """Obtener instancia de la integración GenIA-Location"""
    global genia_location_integration
    
    if genia_location_integration is None:
        genia_location_integration = GeniaLocationIntegration(db, redis_client)
    
    return genia_location_integration