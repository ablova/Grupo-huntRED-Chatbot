# /home/pablo/app/com/talent/retention_predictor.py
"""
Predictor de Retención de Talento.

Este módulo analiza patrones de comportamiento para identificar señales tempranas
de posible desvinculación de talento valioso.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

import numpy as np
from asgiref.sync import sync_to_async
from django.conf import settings

from app.models import Person, JobSatisfaction, PerformanceReview, Activity
from app.ats.talent.cultural_fit import CulturalFitAnalyzer
from app.ats.chatbot.values.core import ValuesPrinciples

logger = logging.getLogger(__name__)

class RetentionPredictor:
    """
    Detector de señales tempranas de posible desvinculación.
    
    Analiza patrones de comportamiento, satisfacción y rendimiento para
    predecir riesgo de rotación y recomendar acciones proactivas.
    """
    
    # Factores de riesgo y sus pesos
    RISK_FACTORS = {
        'job_satisfaction': 0.25,
        'performance_trend': 0.20,
        'compensation_satisfaction': 0.15,
        'work_life_balance': 0.15,
        'engagement': 0.15,
        'career_growth': 0.10
    }
    
    def __init__(self):
        """Inicializa el predictor de retención."""
        self.cultural_fit_analyzer = CulturalFitAnalyzer()
        self.values_principles = ValuesPrinciples()
        self.model = self._load_model()
        
        # Usar el nuevo implementador para el análisis real
        try:
            from app.ats.ml.analyzers.retention_analyzer import RetentionAnalyzerImpl
            self._impl = RetentionAnalyzerImpl()
            self._using_new_impl = True
            logger.info("RetentionPredictor usando implementación mejorada")
        except ImportError:
            self._using_new_impl = False
            logger.warning("RetentionPredictor usando implementación original (no se encontró la mejorada)")
        except Exception as e:
            self._using_new_impl = False
            logger.error(f"Error al inicializar implementación mejorada: {str(e)}")
        
    async def analyze_retention_risk(self, 
                                   person_id: int,
                                   business_unit: Optional[str] = None) -> Dict:
        """
        Analiza el riesgo de desvinculación para una persona.
        
        Args:
            person_id: ID de la persona
            business_unit: Unidad de negocio (opcional)
            
        Returns:
            Dict con análisis de riesgo y recomendaciones
        """
        # Si tenemos disponible la implementación mejorada, usarla
        if hasattr(self, '_using_new_impl') and self._using_new_impl:
            try:
                # Preparar datos para el nuevo analyzer
                data = {
                    'person_id': person_id
                }
                
                # Llamar al implementador con los datos
                # Usamos sync_to_async para convertir el método sincrónico a asíncrono
                # ya que los analyzers implementan interfaces sincrónicas
                from asgiref.sync import sync_to_async
                analyze_async = sync_to_async(self._impl.analyze)
                result = await analyze_async(data, business_unit)
                
                # Añadir análisis de valores - mantenemos esta funcionalidad de la impl original
                values_alignment = await self._check_values_alignment(person_id)
                result['values_alignment'] = values_alignment
                
                # Registrar uso exitoso
                logger.info(f"Usando implementación mejorada para analizar retención de persona {person_id}")
                
                return result
            except Exception as e:
                # Si falla la nueva implementación, caer al método original
                logger.error(f"Error en implementación mejorada: {str(e)}. Usando original.")
        
        # Implementación original como fallback
        try:
            # Obtener datos de la persona
            person = await self._get_person(person_id)
            if not person:
                logger.warning(f"Persona con ID {person_id} no encontrada")
                return self._get_default_analysis(person_id)
            
            # Análisis de satisfacción laboral
            satisfaction_data = await self._analyze_job_satisfaction(person_id)
            
            # Análisis de tendencia de desempeño
            performance_data = await self._analyze_performance_trend(person_id)
            
            # Análisis de compensación
            compensation_data = await self._analyze_compensation_satisfaction(person_id)
            
            # Análisis de balance vida-trabajo
            work_life_data = await self._analyze_work_life_balance(person_id)
            
            # Análisis de engagement
            engagement_data = await self._analyze_engagement(person_id)
            
            # Análisis de crecimiento profesional
            growth_data = await self._analyze_career_growth(person_id)
            
            # Análisis de compatibilidad cultural si es una empresa activa
            cultural_data = None
            if hasattr(person, 'current_company_id') and person.current_company_id:
                cultural_data = await self.cultural_fit_analyzer.analyze_cultural_fit(
                    person_id=person_id,
                    company_id=person.current_company_id,
                    business_unit=business_unit
                )
            
            # Calcular puntuación global de riesgo
            risk_score = self._calculate_risk_score({
                'job_satisfaction': satisfaction_data,
                'performance_trend': performance_data,
                'compensation_satisfaction': compensation_data,
                'work_life_balance': work_life_data,
                'engagement': engagement_data,
                'career_growth': growth_data
            })
            
            # Determinar nivel de riesgo
            risk_level = self._determine_risk_level(risk_score)
            
            # Identificar factores causales
            causal_factors = self._identify_causal_factors({
                'job_satisfaction': satisfaction_data,
                'performance_trend': performance_data,
                'compensation_satisfaction': compensation_data,
                'work_life_balance': work_life_data,
                'engagement': engagement_data,
                'career_growth': growth_data
            })
            
            # Generar recomendaciones
            recommendations = await self._generate_recommendations(
                causal_factors,
                person_id,
                business_unit
            )
            
            # Verificar alineación con valores
            values_alignment = await self._check_values_alignment(person_id)
            
            # Registrar análisis para seguimiento
            await self._log_analysis(person_id, risk_score, risk_level, causal_factors)
            
            # Componer resultado final
            result = {
                'person_id': person_id,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'causal_factors': causal_factors,
                'recommendations': recommendations,
                'values_alignment': values_alignment,
                'cultural_fit': cultural_data.get('compatibility_score', None) if cultural_data else None,
                'analyzed_at': datetime.now().isoformat(),
                'confidence': 'high'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analizando riesgo de retención: {str(e)}")
            return self._get_default_analysis(person_id)
    
    def _load_model(self):
        """Carga el modelo predictivo (simplificado)."""
        # Aquí se cargaría o inicializaría un modelo ML real
        return {'initialized': True}
        
    async def _get_person(self, person_id: int) -> Optional[Any]:
        """Obtiene los datos de la persona desde la base de datos."""
        try:
            # Usando Django sync_to_async para operaciones de BD
            from app.models import Person
            get_person = sync_to_async(lambda: Person.objects.filter(id=person_id).first())()
            return await get_person
        except Exception as e:
            logger.error(f"Error obteniendo datos de persona {person_id}: {str(e)}")
            return None
            
    async def _analyze_job_satisfaction(self, person_id: int) -> Dict:
        """Analiza la satisfacción laboral basada en encuestas y feedbacks."""
        try:
            # Simulación: en producción consultaría base de datos de encuestas
            # Obtener datos históricos de satisfacción
            satisfaction_entries = await sync_to_async(lambda: list(JobSatisfaction.objects.filter(
                person_id=person_id
            ).order_by('-created_at')[:5]))()
            
            if not satisfaction_entries:
                return {
                    'score': 70,  # Valor neutro por defecto
                    'trend': 'stable',
                    'key_issues': [],
                    'confidence': 'low'
                }
                
            # Calcular puntuación actual
            current_score = satisfaction_entries[0].overall_score if satisfaction_entries else 70
            
            # Analizar tendencia
            if len(satisfaction_entries) >= 2:
                previous_scores = [entry.overall_score for entry in satisfaction_entries]
                avg_change = sum([previous_scores[i] - previous_scores[i+1] 
                                for i in range(len(previous_scores)-1)]) / (len(previous_scores)-1)
                if avg_change > 3:
                    trend = 'improving'
                elif avg_change < -3:
                    trend = 'declining'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'
                
            # Identificar problemas clave
            key_issues = []
            if satisfaction_entries:
                categories = ['work_environment', 'management', 'compensation', 'growth']
                category_scores = {}
                
                for category in categories:
                    if hasattr(satisfaction_entries[0], category):
                        score = getattr(satisfaction_entries[0], category)
                        category_scores[category] = score
                        if score < 60:
                            key_issues.append(category)
            
            return {
                'score': current_score,
                'trend': trend,
                'key_issues': key_issues,
                'confidence': 'high' if len(satisfaction_entries) >= 3 else 'medium'
            }
            
        except Exception as e:
            logger.error(f"Error analizando satisfacción laboral: {str(e)}")
            return {
                'score': 70,
                'trend': 'stable',
                'key_issues': [],
                'confidence': 'low'
            }
            
    async def _analyze_performance_trend(self, person_id: int) -> Dict:
        """Analiza la tendencia de desempeño basada en evaluaciones."""
        try:
            # Simulación: en producción consultaría base de datos de evaluaciones
            performance_reviews = await sync_to_async(lambda: list(PerformanceReview.objects.filter(
                person_id=person_id
            ).order_by('-evaluation_date')[:5]))()
            
            if not performance_reviews:
                return {
                    'score': 75,  # Valor neutro por defecto
                    'trend': 'stable',
                    'areas_of_concern': [],
                    'confidence': 'low'
                }
                
            # Calcular puntuación actual
            current_score = performance_reviews[0].overall_score if performance_reviews else 75
            
            # Analizar tendencia
            if len(performance_reviews) >= 2:
                previous_scores = [review.overall_score for review in performance_reviews]
                avg_change = sum([previous_scores[i] - previous_scores[i+1] 
                                for i in range(len(previous_scores)-1)]) / (len(previous_scores)-1)
                if avg_change > 3:
                    trend = 'improving'
                elif avg_change < -3:
                    trend = 'declining'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'
                
            # Identificar áreas de preocupación
            areas_of_concern = []
            if performance_reviews:
                categories = ['technical_skills', 'soft_skills', 'leadership', 'innovation']
                for category in categories:
                    if hasattr(performance_reviews[0], category):
                        score = getattr(performance_reviews[0], category)
                        if score < 60:
                            areas_of_concern.append(category)
            
            return {
                'score': current_score,
                'trend': trend,
                'areas_of_concern': areas_of_concern,
                'confidence': 'high' if len(performance_reviews) >= 3 else 'medium'
            }
            
        except Exception as e:
            logger.error(f"Error analizando tendencia de desempeño: {str(e)}")
            return {
                'score': 75,
                'trend': 'stable',
                'areas_of_concern': [],
                'confidence': 'low'
            }
    
    async def _analyze_compensation_satisfaction(self, person_id: int) -> Dict:
        """Analiza la satisfacción con la compensación."""
        # En un escenario real, este método analizaría datos de salario
        # comparados con los del mercado y datos de satisfacción específicos
        return {
            'score': 72,
            'trend': 'stable',
            'market_comparison': 'competitive',
            'confidence': 'medium'
        }
        
    async def _analyze_work_life_balance(self, person_id: int) -> Dict:
        """Analiza el balance vida-trabajo basado en patrones laborales."""
        # En un escenario real, este método analizaría horas trabajadas,
        # tiempo de vacaciones tomadas y otros indicadores relevantes
        return {
            'score': 68,
            'trend': 'stable',
            'flags': ['overtime_frequency'],
            'confidence': 'medium'
        }
        
    async def _analyze_engagement(self, person_id: int) -> Dict:
        """Analiza el nivel de engagement basado en participación y contribuciones."""
        try:
            # Simulación: en producción consultaría actividades registradas
            activities = await sync_to_async(lambda: list(Activity.objects.filter(
                person_id=person_id, 
                created_at__gte=datetime.now().replace(month=datetime.now().month-3)
            ).order_by('-created_at')))()
            
            if not activities:
                return {
                    'score': 65,
                    'trend': 'stable',
                    'activity_level': 'moderate',
                    'confidence': 'low'
                }
                
            # Calcular nivel de actividad
            activity_count = len(activities)
            if activity_count > 20:
                activity_level = 'high'
                score = 85
            elif activity_count > 10:
                activity_level = 'moderate'
                score = 70
            else:
                activity_level = 'low'
                score = 55
                
            # Analizar tendencia
            # En un escenario real, compararía con períodos anteriores
            
            return {
                'score': score,
                'trend': 'stable',  # Simplificado para el ejemplo
                'activity_level': activity_level,
                'confidence': 'medium'
            }
            
        except Exception as e:
            logger.error(f"Error analizando engagement: {str(e)}")
            return {
                'score': 65,
                'trend': 'stable',
                'activity_level': 'moderate',
                'confidence': 'low'
            }
            
    async def _analyze_career_growth(self, person_id: int) -> Dict:
        """Analiza las oportunidades de crecimiento profesional."""
        # En un escenario real, este método analizaría historial de
        # promociones, tiempo en posición actual y oportunidades disponibles
        return {
            'score': 60,
            'trend': 'declining',
            'time_in_position': '24 months',
            'promotion_potential': 'moderate',
            'confidence': 'high'
        }
        
    def _calculate_risk_score(self, factor_data: Dict) -> int:
        """Calcula la puntuación global de riesgo basada en factores ponderados."""
        score = 0
        total_weight = sum(self.RISK_FACTORS.values())
        
        for factor, weight in self.RISK_FACTORS.items():
            if factor in factor_data and 'score' in factor_data[factor]:
                # Convertir a riesgo (scores más bajos = más riesgo)
                risk_contribution = (100 - factor_data[factor]['score']) * (weight / total_weight)
                score += risk_contribution
                
        return int(score)
        
    def _determine_risk_level(self, risk_score: int) -> str:
        """Determina el nivel de riesgo basado en la puntuación."""
        if risk_score >= 75:
            return 'high'
        elif risk_score >= 50:
            return 'medium'
        else:
            return 'low'
            
    def _identify_causal_factors(self, factor_data: Dict) -> List[Dict]:
        """Identifica los factores causales principales del riesgo."""
        causal_factors = []
        
        for factor, data in factor_data.items():
            if 'score' in data:
                risk = 100 - data['score']  # Convertir a métrica de riesgo
                causal_factors.append({
                    'factor': factor,
                    'score': data['score'],
                    'risk': risk,
                    'trend': data.get('trend', 'stable'),
                    'confidence': data.get('confidence', 'medium')
                })
                
        # Ordenar por riesgo descendente
        causal_factors.sort(key=lambda x: x['risk'], reverse=True)
        
        # Retornar los top factores (limitado a 3 para no sobrecargar)
        return causal_factors[:3]
        
    async def _generate_recommendations(self, causal_factors: List[Dict], person_id: int, business_unit: Optional[str] = None) -> List[Dict]:
        """Genera recomendaciones basadas en factores causales identificados."""
        recommendations = []
        
        for factor in causal_factors:
            factor_name = factor['factor']
            risk_level = 'high' if factor['risk'] >= 75 else 'medium' if factor['risk'] >= 50 else 'low'
            
            if factor_name == 'job_satisfaction':
                if 'key_issues' in factor and 'work_environment' in factor['key_issues']:
                    recommendations.append({
                        'action': 'Realizar encuesta de clima laboral enfocada',
                        'urgency': risk_level,
                        'expected_impact': 'high',
                        'owner': 'hr',
                        'timeline': '2 weeks'
                    })
                else:
                    recommendations.append({
                        'action': 'Programar sesión de feedback 1:1',
                        'urgency': risk_level,
                        'expected_impact': 'medium',
                        'owner': 'manager',
                        'timeline': '1 week'
                    })
                    
            elif factor_name == 'career_growth':
                recommendations.append({
                    'action': 'Revisar plan de carrera y oportunidades de desarrollo',
                    'urgency': risk_level,
                    'expected_impact': 'high',
                    'owner': 'manager',
                    'timeline': '1 month'
                })
                
            elif factor_name == 'compensation_satisfaction':
                recommendations.append({
                    'action': 'Realizar revisión salarial comparativa con mercado',
                    'urgency': risk_level,
                    'expected_impact': 'high',
                    'owner': 'hr',
                    'timeline': '1 month'
                })
                
            elif factor_name == 'work_life_balance':
                recommendations.append({
                    'action': 'Revisar carga de trabajo y distribución de tareas',
                    'urgency': risk_level,
                    'expected_impact': 'medium',
                    'owner': 'manager',
                    'timeline': '2 weeks'
                })
                
            elif factor_name == 'engagement':
                recommendations.append({
                    'action': 'Asignar a proyecto de alto impacto alineado con intereses',
                    'urgency': risk_level,
                    'expected_impact': 'high',
                    'owner': 'manager',
                    'timeline': '1 month'
                })
                
            elif factor_name == 'performance_trend':
                recommendations.append({
                    'action': 'Crear plan de mejora de desempeño personalizado',
                    'urgency': risk_level,
                    'expected_impact': 'medium',
                    'owner': 'manager',
                    'timeline': '2 weeks'
                })
                
        # Si no hay recomendaciones específicas, agregar una genérica
        if not recommendations:
            recommendations.append({
                'action': 'Realizar sesión de check-in para evaluar satisfacción',
                'urgency': 'medium',
                'expected_impact': 'medium',
                'owner': 'manager',
                'timeline': '2 weeks'
            })
            
        return recommendations
        
    async def _log_analysis(self, person_id: int, risk_score: int, risk_level: str, causal_factors: List[Dict]) -> None:
        """Registra el análisis de retención para seguimiento futuro."""
        # En un escenario real, guardaría estos datos en la base de datos
        # para análisis históricos y seguimiento de tendencias
        logger.info(f"Análisis de retención completado para persona {person_id}: Riesgo {risk_level.upper()} ({risk_score})")
        
    async def _check_values_alignment(self, person_id: int) -> Dict:
        """Verifica alineación con valores de Grupo huntRED®."""
        # Obtener valores de la persona
        # En un escenario real, esto consultaría una tabla o cuestionario
        person_values = ['Innovación', 'Colaboración', 'Excelencia']
        
        # Valores de Grupo huntRED®
        huntred_values = ['Apoyo', 'Solidaridad', 'Sinergia', 'Innovación']
        
        # Calcular alineación
        matching_values = [val for val in person_values if val in huntred_values]
        alignment_score = (len(matching_values) / len(huntred_values)) * 100
        
        return {
            'alignment_score': int(alignment_score),
            'matching_values': matching_values,
            'huntred_values': huntred_values,
            'person_values': person_values
        }
        
    def _get_default_analysis(self, person_id: int) -> Dict:
        """Retorna un análisis por defecto cuando no hay datos suficientes."""
        return {
            'person_id': person_id,
            'risk_score': 50,  # Neutral
            'risk_level': 'medium',
            'causal_factors': [
                {'factor': 'insufficient_data', 'score': 50, 'trend': 'stable'}
            ],
            'recommendations': [
                {
                    'action': 'Recolectar más datos para análisis preciso',
                    'urgency': 'medium',
                    'expected_impact': 'high'
                }
            ],
            'analyzed_at': datetime.now().isoformat(),
            'confidence': 'low'
        }