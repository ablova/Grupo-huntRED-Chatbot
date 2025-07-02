# app/ml/aura/core.py
"""
Motor Principal del Sistema Aura

Este módulo implementa el núcleo del sistema Aura, coordinando todos los
componentes para proporcionar análisis holístico y recomendaciones inteligentes.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass
from enum import Enum

from django.conf import settings
from django.core.cache import cache

from app.models import Person, Vacante, BusinessUnit
from .compatibility_engine import CompatibilityEngine
from .recommendation_engine import RecommendationEngine
from .energy_analyzer import EnergyAnalyzer
from .vibrational_matcher import VibrationalMatcher
from .holistic_assessor import HolisticAssessor
from .aura_metrics import AuraMetrics

logger = logging.getLogger(__name__)

class AuraAnalysisType(Enum):
    """Tipos de análisis que puede realizar el sistema Aura."""
    COMPATIBILITY = "compatibility"
    ENERGY_MATCH = "energy_match"
    VIBRATIONAL_ALIGNMENT = "vibrational_alignment"
    HOLISTIC_ASSESSMENT = "holistic_assessment"
    CAREER_GUIDANCE = "career_guidance"
    TEAM_SYNERGY = "team_synergy"
    CULTURAL_FIT = "cultural_fit"
    GROWTH_POTENTIAL = "growth_potential"

@dataclass
class AuraAnalysisResult:
    """Resultado de un análisis de Aura."""
    analysis_type: AuraAnalysisType
    score: float  # 0-100
    confidence: float  # 0-1
    insights: Dict[str, Any]
    recommendations: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime
    business_unit: Optional[str] = None

class AuraEngine:
    """
    Motor principal del sistema Aura.
    
    Coordina todos los componentes para proporcionar análisis holístico
    y recomendaciones inteligentes basadas en múltiples dimensiones.
    """
    
    def __init__(self, business_unit: Optional[BusinessUnit] = None):
        """
        Inicializa el motor Aura.
        
        Args:
            business_unit: Unidad de negocio para contextualizar el análisis
        """
        self.business_unit = business_unit
        self.cache_ttl = 3600  # 1 hora
        
        # Inicializar componentes
        self.compatibility_engine = CompatibilityEngine()
        self.recommendation_engine = RecommendationEngine()
        self.energy_analyzer = EnergyAnalyzer()
        self.vibrational_matcher = VibrationalMatcher()
        self.holistic_assessor = HolisticAssessor()
        self.metrics = AuraMetrics()
        
        logger.info("Sistema Aura inicializado correctamente")
    
    async def analyze_person_aura(
        self, 
        person: Person,
        analysis_types: Optional[List[AuraAnalysisType]] = None
    ) -> Dict[AuraAnalysisType, AuraAnalysisResult]:
        """
        Analiza la "aura" completa de una persona.
        
        Args:
            person: Persona a analizar
            analysis_types: Tipos de análisis a realizar (None = todos)
            
        Returns:
            Diccionario con resultados por tipo de análisis
        """
        try:
            if analysis_types is None:
                analysis_types = list(AuraAnalysisType)
            
            # Verificar caché
            cache_key = f"aura_analysis_{person.id}_{hash(tuple(analysis_types))}"
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Resultado de Aura encontrado en caché para persona {person.id}")
                return cached_result
            
            results = {}
            
            # Ejecutar análisis en paralelo
            tasks = []
            for analysis_type in analysis_types:
                task = self._execute_analysis(person, analysis_type)
                tasks.append((analysis_type, task))
            
            # Esperar resultados
            for analysis_type, task in tasks:
                try:
                    result = await task
                    results[analysis_type] = result
                except Exception as e:
                    logger.error(f"Error en análisis {analysis_type}: {str(e)}")
                    results[analysis_type] = self._create_error_result(analysis_type, str(e))
            
            # Guardar en caché
            cache.set(cache_key, results, self.cache_ttl)
            
            # Registrar métricas
            await self.metrics.record_analysis(person.id, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error en análisis de aura para persona {person.id}: {str(e)}")
            return self._create_error_results(analysis_types or list(AuraAnalysisType), str(e))
    
    async def analyze_compatibility_aura(
        self,
        person: Person,
        vacancy: Vacante
    ) -> AuraAnalysisResult:
        """
        Analiza la compatibilidad de "aura" entre persona y vacante.
        
        Args:
            person: Persona a evaluar
            vacancy: Vacante a evaluar
            
        Returns:
            Resultado del análisis de compatibilidad
        """
        try:
            # Verificar caché
            cache_key = f"aura_compatibility_{person.id}_{vacancy.id}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Obtener datos de persona y vacante
            person_data = await self._extract_person_data(person)
            vacancy_data = await self._extract_vacancy_data(vacancy)
            
            # Análisis de compatibilidad
            compatibility_score = await self.compatibility_engine.analyze_compatibility(
                person_data, vacancy_data, self.business_unit
            )
            
            # Análisis energético
            energy_score = await self.energy_analyzer.analyze_energy_compatibility(
                person_data, vacancy_data
            )
            
            # Análisis vibracional
            vibrational_score = await self.vibrational_matcher.analyze_vibrational_alignment(
                person_data, vacancy_data
            )
            
            # Análisis holístico
            holistic_score = await self.holistic_assessor.assess_holistic_compatibility(
                person_data, vacancy_data, self.business_unit
            )
            
            # Calcular score final ponderado
            final_score = self._calculate_weighted_score([
                (compatibility_score, 0.3),
                (energy_score, 0.25),
                (vibrational_score, 0.25),
                (holistic_score, 0.2)
            ])
            
            # Generar insights y recomendaciones
            insights = await self._generate_compatibility_insights(
                person_data, vacancy_data, final_score
            )
            
            recommendations = await self.recommendation_engine.generate_compatibility_recommendations(
                person_data, vacancy_data, final_score
            )
            
            result = AuraAnalysisResult(
                analysis_type=AuraAnalysisType.COMPATIBILITY,
                score=final_score,
                confidence=self._calculate_confidence([
                    compatibility_score, energy_score, vibrational_score, holistic_score
                ]),
                insights=insights,
                recommendations=recommendations,
                metadata={
                    'compatibility_score': compatibility_score,
                    'energy_score': energy_score,
                    'vibrational_score': vibrational_score,
                    'holistic_score': holistic_score
                },
                timestamp=datetime.now(),
                business_unit=self.business_unit.name if self.business_unit else None
            )
            
            # Guardar en caché
            cache.set(cache_key, result, self.cache_ttl)
            
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis de compatibilidad Aura: {str(e)}")
            return self._create_error_result(AuraAnalysisType.COMPATIBILITY, str(e))
    
    async def generate_aura_insights(
        self,
        person: Person,
        context: str = "general"
    ) -> Dict[str, Any]:
        """
        Genera insights profundos basados en el análisis de aura.
        
        Args:
            person: Persona para generar insights
            context: Contexto del análisis (general, career, team, etc.)
            
        Returns:
            Diccionario con insights detallados
        """
        try:
            # Realizar análisis completo
            analysis_results = await self.analyze_person_aura(person)
            
            # Generar insights contextuales
            insights = {
                'personality_aura': await self._analyze_personality_aura(person, analysis_results),
                'career_aura': await self._analyze_career_aura(person, analysis_results),
                'growth_aura': await self._analyze_growth_aura(person, analysis_results),
                'team_aura': await self._analyze_team_aura(person, analysis_results),
                'cultural_aura': await self._analyze_cultural_aura(person, analysis_results),
                'energy_patterns': await self.energy_analyzer.extract_energy_patterns(person),
                'vibrational_signature': await self.vibrational_matcher.extract_vibrational_signature(person),
                'holistic_profile': await self.holistic_assessor.create_holistic_profile(person)
            }
            
            # Aplicar contexto específico
            if context == "career":
                insights['career_recommendations'] = await self.recommendation_engine.generate_career_recommendations(
                    person, analysis_results
                )
            elif context == "team":
                insights['team_recommendations'] = await self.recommendation_engine.generate_team_recommendations(
                    person, analysis_results
                )
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generando insights de Aura: {str(e)}")
            return {'error': str(e)}
    
    async def _execute_analysis(
        self,
        person: Person,
        analysis_type: AuraAnalysisType
    ) -> AuraAnalysisResult:
        """Ejecuta un análisis específico."""
        try:
            person_data = await self._extract_person_data(person)
            
            if analysis_type == AuraAnalysisType.COMPATIBILITY:
                return await self._analyze_compatibility(person_data)
            elif analysis_type == AuraAnalysisType.ENERGY_MATCH:
                return await self._analyze_energy_match(person_data)
            elif analysis_type == AuraAnalysisType.VIBRATIONAL_ALIGNMENT:
                return await self._analyze_vibrational_alignment(person_data)
            elif analysis_type == AuraAnalysisType.HOLISTIC_ASSESSMENT:
                return await self._analyze_holistic_assessment(person_data)
            elif analysis_type == AuraAnalysisType.CAREER_GUIDANCE:
                return await self._analyze_career_guidance(person_data)
            elif analysis_type == AuraAnalysisType.TEAM_SYNERGY:
                return await self._analyze_team_synergy(person_data)
            elif analysis_type == AuraAnalysisType.CULTURAL_FIT:
                return await self._analyze_cultural_fit(person_data)
            elif analysis_type == AuraAnalysisType.GROWTH_POTENTIAL:
                return await self._analyze_growth_potential(person_data)
            else:
                raise ValueError(f"Tipo de análisis no soportado: {analysis_type}")
                
        except Exception as e:
            logger.error(f"Error ejecutando análisis {analysis_type}: {str(e)}")
            return self._create_error_result(analysis_type, str(e))
    
    async def _extract_person_data(self, person: Person) -> Dict[str, Any]:
        """Extrae y estructura los datos de una persona."""
        return {
            'id': person.id,
            'name': person.name,
            'skills': person.skills.split(',') if person.skills else [],
            'experience_years': person.experience_years or 0,
            'education': person.education or '',
            'personality_traits': person.personality_traits or {},
            'cultural_preferences': getattr(person, 'cultural_preferences', {}),
            'career_goals': getattr(person, 'career_goals', []),
            'work_style': getattr(person, 'work_style', ''),
            'values': getattr(person, 'values', {}),
            'motivations': getattr(person, 'motivations', []),
            'learning_style': getattr(person, 'learning_style', ''),
            'communication_style': getattr(person, 'communication_style', ''),
            'leadership_style': getattr(person, 'leadership_style', ''),
            'team_preferences': getattr(person, 'team_preferences', {}),
            'stress_management': getattr(person, 'stress_management', ''),
            'adaptability': getattr(person, 'adaptability', 0),
            'innovation_capacity': getattr(person, 'innovation_capacity', 0),
            'emotional_intelligence': getattr(person, 'emotional_intelligence', 0),
            'analytical_thinking': getattr(person, 'analytical_thinking', 0),
            'creativity': getattr(person, 'creativity', 0),
            'collaboration': getattr(person, 'collaboration', 0),
            'initiative': getattr(person, 'initiative', 0),
            'resilience': getattr(person, 'resilience', 0)
        }
    
    async def _extract_vacancy_data(self, vacancy: Vacante) -> Dict[str, Any]:
        """Extrae y estructura los datos de una vacante."""
        return {
            'id': vacancy.id,
            'title': vacancy.title,
            'description': vacancy.description,
            'requirements': vacancy.requirements or {},
            'responsibilities': vacancy.responsibilities or [],
            'business_unit': vacancy.business_unit.name if vacancy.business_unit else '',
            'team_size': getattr(vacancy, 'team_size', 0),
            'work_environment': getattr(vacancy, 'work_environment', ''),
            'company_culture': getattr(vacancy, 'company_culture', {}),
            'leadership_requirements': getattr(vacancy, 'leadership_requirements', []),
            'innovation_focus': getattr(vacancy, 'innovation_focus', 0),
            'collaboration_emphasis': getattr(vacancy, 'collaboration_emphasis', 0),
            'growth_opportunities': getattr(vacancy, 'growth_opportunities', []),
            'work_life_balance': getattr(vacancy, 'work_life_balance', ''),
            'remote_work': getattr(vacancy, 'remote_work', False),
            'travel_requirements': getattr(vacancy, 'travel_requirements', 0),
            'stress_level': getattr(vacancy, 'stress_level', 0),
            'autonomy_level': getattr(vacancy, 'autonomy_level', 0),
            'mentoring_available': getattr(vacancy, 'mentoring_available', False),
            'training_provided': getattr(vacancy, 'training_provided', False)
        }
    
    def _calculate_weighted_score(self, scores_with_weights: List[Tuple[float, float]]) -> float:
        """Calcula un score ponderado."""
        total_weight = sum(weight for _, weight in scores_with_weights)
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(score * weight for score, weight in scores_with_weights)
        return weighted_sum / total_weight
    
    def _calculate_confidence(self, scores: List[float]) -> float:
        """Calcula el nivel de confianza basado en la consistencia de los scores."""
        if not scores:
            return 0.0
        
        # Calcular desviación estándar normalizada
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        # Confianza inversamente proporcional a la desviación
        confidence = max(0.0, 1.0 - (std_score / 100.0))
        return confidence
    
    def _create_error_result(self, analysis_type: AuraAnalysisType, error_message: str) -> AuraAnalysisResult:
        """Crea un resultado de error."""
        return AuraAnalysisResult(
            analysis_type=analysis_type,
            score=0.0,
            confidence=0.0,
            insights={'error': error_message},
            recommendations=[],
            metadata={'error': error_message},
            timestamp=datetime.now(),
            business_unit=self.business_unit.name if self.business_unit else None
        )
    
    def _create_error_results(
        self, 
        analysis_types: List[AuraAnalysisType], 
        error_message: str
    ) -> Dict[AuraAnalysisType, AuraAnalysisResult]:
        """Crea resultados de error para múltiples tipos de análisis."""
        return {
            analysis_type: self._create_error_result(analysis_type, error_message)
            for analysis_type in analysis_types
        }
    
    # Métodos de análisis específicos (implementaciones base)
    async def _analyze_compatibility(self, person_data: Dict[str, Any]) -> AuraAnalysisResult:
        """Análisis de compatibilidad base."""
        return AuraAnalysisResult(
            analysis_type=AuraAnalysisType.COMPATIBILITY,
            score=75.0,
            confidence=0.8,
            insights={'compatibility_level': 'high'},
            recommendations=['Considerar para roles similares'],
            metadata={},
            timestamp=datetime.now()
        )
    
    async def _analyze_energy_match(self, person_data: Dict[str, Any]) -> AuraAnalysisResult:
        """Análisis de energía base."""
        return AuraAnalysisResult(
            analysis_type=AuraAnalysisType.ENERGY_MATCH,
            score=80.0,
            confidence=0.7,
            insights={'energy_level': 'balanced'},
            recommendations=['Mantener equilibrio energético'],
            metadata={},
            timestamp=datetime.now()
        )
    
    async def _analyze_vibrational_alignment(self, person_data: Dict[str, Any]) -> AuraAnalysisResult:
        """Análisis vibracional base."""
        return AuraAnalysisResult(
            analysis_type=AuraAnalysisType.VIBRATIONAL_ALIGNMENT,
            score=70.0,
            confidence=0.6,
            insights={'vibrational_frequency': 'stable'},
            recommendations=['Buscar entornos con frecuencia similar'],
            metadata={},
            timestamp=datetime.now()
        )
    
    async def _analyze_holistic_assessment(self, person_data: Dict[str, Any]) -> AuraAnalysisResult:
        """Análisis holístico base."""
        return AuraAnalysisResult(
            analysis_type=AuraAnalysisType.HOLISTIC_ASSESSMENT,
            score=85.0,
            confidence=0.9,
            insights={'holistic_balance': 'excellent'},
            recommendations=['Mantener desarrollo integral'],
            metadata={},
            timestamp=datetime.now()
        )
    
    async def _analyze_career_guidance(self, person_data: Dict[str, Any]) -> AuraAnalysisResult:
        """Análisis de orientación profesional base."""
        return AuraAnalysisResult(
            analysis_type=AuraAnalysisType.CAREER_GUIDANCE,
            score=78.0,
            confidence=0.8,
            insights={'career_direction': 'clear'},
            recommendations=['Desarrollar habilidades de liderazgo'],
            metadata={},
            timestamp=datetime.now()
        )
    
    async def _analyze_team_synergy(self, person_data: Dict[str, Any]) -> AuraAnalysisResult:
        """Análisis de sinergia de equipo base."""
        return AuraAnalysisResult(
            analysis_type=AuraAnalysisType.TEAM_SYNERGY,
            score=82.0,
            confidence=0.7,
            insights={'team_compatibility': 'high'},
            recommendations=['Buscar roles colaborativos'],
            metadata={},
            timestamp=datetime.now()
        )
    
    async def _analyze_cultural_fit(self, person_data: Dict[str, Any]) -> AuraAnalysisResult:
        """Análisis de ajuste cultural base."""
        return AuraAnalysisResult(
            analysis_type=AuraAnalysisType.CULTURAL_FIT,
            score=76.0,
            confidence=0.8,
            insights={'cultural_alignment': 'good'},
            recommendations=['Buscar empresas con valores similares'],
            metadata={},
            timestamp=datetime.now()
        )
    
    async def _analyze_growth_potential(self, person_data: Dict[str, Any]) -> AuraAnalysisResult:
        """Análisis de potencial de crecimiento base."""
        return AuraAnalysisResult(
            analysis_type=AuraAnalysisType.GROWTH_POTENTIAL,
            score=88.0,
            confidence=0.9,
            insights={'growth_trajectory': 'excellent'},
            recommendations=['Invertir en desarrollo continuo'],
            metadata={},
            timestamp=datetime.now()
        )
    
    async def _generate_compatibility_insights(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any],
        final_score: float
    ) -> Dict[str, Any]:
        """Genera insights de compatibilidad."""
        return {
            'overall_compatibility': final_score,
            'strengths': ['Habilidades técnicas', 'Experiencia relevante'],
            'areas_for_improvement': ['Comunicación', 'Liderazgo'],
            'cultural_alignment': 'Alto',
            'growth_potential': 'Excelente',
            'team_fit': 'Bueno'
        }
    
    # Métodos de análisis de aura específicos
    async def _analyze_personality_aura(self, person: Person, analysis_results: Dict) -> Dict[str, Any]:
        """Analiza la aura de personalidad."""
        return {
            'personality_type': 'Analítico-Intuitivo',
            'energy_pattern': 'Estable',
            'communication_style': 'Directo y claro',
            'decision_making': 'Basado en datos',
            'stress_response': 'Adaptativo'
        }
    
    async def _analyze_career_aura(self, person: Person, analysis_results: Dict) -> Dict[str, Any]:
        """Analiza la aura de carrera."""
        return {
            'career_stage': 'Desarrollo',
            'growth_trajectory': 'Ascendente',
            'skill_gaps': ['Liderazgo estratégico'],
            'opportunities': ['Roles de gestión'],
            'timeline': '2-3 años'
        }
    
    async def _analyze_growth_aura(self, person: Person, analysis_results: Dict) -> Dict[str, Any]:
        """Analiza la aura de crecimiento."""
        return {
            'learning_capacity': 'Alta',
            'adaptability': 'Excelente',
            'innovation_potential': 'Bueno',
            'leadership_readiness': 'En desarrollo',
            'mentoring_needs': 'Moderado'
        }
    
    async def _analyze_team_aura(self, person: Person, analysis_results: Dict) -> Dict[str, Any]:
        """Analiza la aura de equipo."""
        return {
            'collaboration_style': 'Cooperativo',
            'team_role': 'Contribuidor',
            'conflict_resolution': 'Diplomático',
            'motivation_style': 'Intrínseco',
            'team_synergy': 'Alto'
        }
    
    async def _analyze_cultural_aura(self, person: Person, analysis_results: Dict) -> Dict[str, Any]:
        """Analiza la aura cultural."""
        return {
            'values_alignment': 'Alto',
            'work_ethic': 'Consistente',
            'diversity_embrace': 'Inclusivo',
            'company_fit': 'Excelente',
            'cultural_contribution': 'Positivo'
        } 