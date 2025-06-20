"""
Evaluador Holístico del Sistema Aura

Este módulo implementa la evaluación holística que integra todos los análisis
del sistema Aura para proporcionar una visión completa y profunda.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime

from app.models import Person, Vacante, BusinessUnit

logger = logging.getLogger(__name__)

class HolisticDimension(Enum):
    """Dimensiones del análisis holístico."""
    PHYSICAL = "physical"
    MENTAL = "mental"
    EMOTIONAL = "emotional"
    SPIRITUAL = "spiritual"
    SOCIAL = "social"
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    INTELLECTUAL = "intellectual"

class HolisticBalance(Enum):
    """Tipos de balance holístico."""
    HARMONIOUS = "harmonious"
    BALANCED = "balanced"
    UNBALANCED = "unbalanced"
    DISCORDANT = "discordant"

@dataclass
class HolisticProfile:
    """Perfil holístico completo de una persona o entorno."""
    dimensions: Dict[HolisticDimension, float]
    overall_balance: HolisticBalance
    harmony_score: float
    growth_potential: float
    resilience_index: float
    adaptability_quotient: float
    integration_level: float
    timestamp: datetime

class HolisticAssessor:
    """
    Evaluador holístico que integra todos los análisis del sistema Aura.
    
    Proporciona una evaluación completa considerando múltiples dimensiones
    y la interconexión entre todos los aspectos del ser humano.
    """
    
    def __init__(self):
        """Inicializa el evaluador holístico."""
        self.dimension_weights = {
            HolisticDimension.PHYSICAL: 0.15,
            HolisticDimension.MENTAL: 0.20,
            HolisticDimension.EMOTIONAL: 0.15,
            HolisticDimension.SPIRITUAL: 0.10,
            HolisticDimension.SOCIAL: 0.15,
            HolisticDimension.PROFESSIONAL: 0.15,
            HolisticDimension.CREATIVE: 0.05,
            HolisticDimension.INTELLECTUAL: 0.05
        }
        
        # Configuraciones de balance holístico
        self.balance_thresholds = {
            HolisticBalance.HARMONIOUS: 85,
            HolisticBalance.BALANCED: 70,
            HolisticBalance.UNBALANCED: 50,
            HolisticBalance.DISCORDANT: 30
        }
        
        logger.info("Evaluador holístico inicializado")
    
    async def assess_holistic_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any],
        business_unit: Optional[BusinessUnit] = None
    ) -> float:
        """
        Evalúa la compatibilidad holística entre persona y vacante.
        
        Args:
            person_data: Datos de la persona
            vacancy_data: Datos de la vacante
            business_unit: Unidad de negocio para contexto
            
        Returns:
            Score de compatibilidad holística (0-100)
        """
        try:
            # Crear perfiles holísticos
            person_profile = await self.create_holistic_profile(person_data)
            vacancy_profile = await self.create_vacancy_holistic_profile(vacancy_data)
            
            # Calcular compatibilidad holística
            compatibility_score = await self._calculate_holistic_compatibility(
                person_profile, vacancy_profile
            )
            
            # Ajustar por contexto de negocio
            adjusted_score = await self._adjust_holistic_score(
                compatibility_score, business_unit
            )
            
            return adjusted_score
            
        except Exception as e:
            logger.error(f"Error en evaluación holística: {str(e)}")
            return 0.0
    
    async def create_holistic_profile(self, person_data: Dict[str, Any]) -> HolisticProfile:
        """
        Crea un perfil holístico completo de una persona.
        
        Args:
            person_data: Datos de la persona
            
        Returns:
            Perfil holístico de la persona
        """
        try:
            # Evaluar cada dimensión holística
            dimensions = {}
            
            dimensions[HolisticDimension.PHYSICAL] = await self._assess_physical_dimension(person_data)
            dimensions[HolisticDimension.MENTAL] = await self._assess_mental_dimension(person_data)
            dimensions[HolisticDimension.EMOTIONAL] = await self._assess_emotional_dimension(person_data)
            dimensions[HolisticDimension.SPIRITUAL] = await self._assess_spiritual_dimension(person_data)
            dimensions[HolisticDimension.SOCIAL] = await self._assess_social_dimension(person_data)
            dimensions[HolisticDimension.PROFESSIONAL] = await self._assess_professional_dimension(person_data)
            dimensions[HolisticDimension.CREATIVE] = await self._assess_creative_dimension(person_data)
            dimensions[HolisticDimension.INTELLECTUAL] = await self._assess_intellectual_dimension(person_data)
            
            # Calcular métricas holísticas
            overall_balance = self._determine_holistic_balance(dimensions)
            harmony_score = self._calculate_harmony_score(dimensions)
            growth_potential = self._calculate_growth_potential(dimensions)
            resilience_index = self._calculate_resilience_index(dimensions)
            adaptability_quotient = self._calculate_adaptability_quotient(dimensions)
            integration_level = self._calculate_integration_level(dimensions)
            
            return HolisticProfile(
                dimensions=dimensions,
                overall_balance=overall_balance,
                harmony_score=harmony_score,
                growth_potential=growth_potential,
                resilience_index=resilience_index,
                adaptability_quotient=adaptability_quotient,
                integration_level=integration_level,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error creando perfil holístico: {str(e)}")
            return self._create_default_holistic_profile()
    
    async def create_vacancy_holistic_profile(self, vacancy_data: Dict[str, Any]) -> HolisticProfile:
        """
        Crea un perfil holístico de una vacante.
        
        Args:
            vacancy_data: Datos de la vacante
            
        Returns:
            Perfil holístico de la vacante
        """
        try:
            # Evaluar dimensiones holísticas del entorno
            dimensions = {}
            
            dimensions[HolisticDimension.PHYSICAL] = await self._assess_vacancy_physical_dimension(vacancy_data)
            dimensions[HolisticDimension.MENTAL] = await self._assess_vacancy_mental_dimension(vacancy_data)
            dimensions[HolisticDimension.EMOTIONAL] = await self._assess_vacancy_emotional_dimension(vacancy_data)
            dimensions[HolisticDimension.SPIRITUAL] = await self._assess_vacancy_spiritual_dimension(vacancy_data)
            dimensions[HolisticDimension.SOCIAL] = await self._assess_vacancy_social_dimension(vacancy_data)
            dimensions[HolisticDimension.PROFESSIONAL] = await self._assess_vacancy_professional_dimension(vacancy_data)
            dimensions[HolisticDimension.CREATIVE] = await self._assess_vacancy_creative_dimension(vacancy_data)
            dimensions[HolisticDimension.INTELLECTUAL] = await self._assess_vacancy_intellectual_dimension(vacancy_data)
            
            # Calcular métricas holísticas del entorno
            overall_balance = self._determine_holistic_balance(dimensions)
            harmony_score = self._calculate_harmony_score(dimensions)
            growth_potential = self._calculate_growth_potential(dimensions)
            resilience_index = self._calculate_resilience_index(dimensions)
            adaptability_quotient = self._calculate_adaptability_quotient(dimensions)
            integration_level = self._calculate_integration_level(dimensions)
            
            return HolisticProfile(
                dimensions=dimensions,
                overall_balance=overall_balance,
                harmony_score=harmony_score,
                growth_potential=growth_potential,
                resilience_index=resilience_index,
                adaptability_quotient=adaptability_quotient,
                integration_level=integration_level,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error creando perfil holístico de vacante: {str(e)}")
            return self._create_default_holistic_profile()
    
    async def generate_holistic_insights(
        self,
        person: Person,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Genera insights holísticos profundos.
        
        Args:
            person: Persona para generar insights
            analysis_results: Resultados de análisis previos
            
        Returns:
            Insights holísticos completos
        """
        try:
            person_data = await self._extract_person_data(person)
            holistic_profile = await self.create_holistic_profile(person_data)
            
            insights = {
                'holistic_balance': holistic_profile.overall_balance.value,
                'harmony_level': holistic_profile.harmony_score,
                'growth_potential': holistic_profile.growth_potential,
                'resilience_capacity': holistic_profile.resilience_index,
                'adaptability_level': holistic_profile.adaptability_quotient,
                'integration_quality': holistic_profile.integration_level,
                'dimension_analysis': {},
                'strengths': [],
                'areas_for_development': [],
                'holistic_recommendations': []
            }
            
            # Análisis por dimensión
            for dimension, score in holistic_profile.dimensions.items():
                insights['dimension_analysis'][dimension.value] = {
                    'score': score,
                    'status': 'strong' if score >= 80 else 'good' if score >= 60 else 'developing',
                    'description': self._get_dimension_description(dimension, score)
                }
                
                # Clasificar como fortaleza o área de desarrollo
                if score >= 80:
                    insights['strengths'].append({
                        'dimension': dimension.value,
                        'score': score,
                        'description': self._get_dimension_description(dimension, score)
                    })
                elif score < 60:
                    insights['areas_for_development'].append({
                        'dimension': dimension.value,
                        'score': score,
                        'description': self._get_dimension_description(dimension, score),
                        'recommendations': self._get_dimension_recommendations(dimension)
                    })
            
            # Generar recomendaciones holísticas
            insights['holistic_recommendations'] = await self._generate_holistic_recommendations(
                holistic_profile, insights
            )
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generando insights holísticos: {str(e)}")
            return {'error': str(e)}
    
    async def _assess_physical_dimension(self, person_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión física."""
        # Factores físicos
        stress_management = person_data.get('stress_management', '')
        work_style = person_data.get('work_style', '')
        
        score = 70.0  # Base
        
        # Ajustar por manejo del estrés
        if 'exercise' in stress_management.lower():
            score += 15
        if 'mindfulness' in stress_management.lower():
            score += 10
        
        # Ajustar por estilo de trabajo
        if 'active' in work_style.lower():
            score += 10
        elif 'sedentary' in work_style.lower():
            score -= 5
        
        return min(100.0, max(0.0, score))
    
    async def _assess_mental_dimension(self, person_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión mental."""
        # Factores mentales
        analytical_thinking = person_data.get('analytical_thinking', 0)
        adaptability = person_data.get('adaptability', 0)
        learning_style = person_data.get('learning_style', '')
        
        score = 70.0  # Base
        
        # Ajustar por capacidad analítica
        score += analytical_thinking * 0.2
        
        # Ajustar por adaptabilidad
        score += adaptability * 0.2
        
        # Ajustar por estilo de aprendizaje
        if 'continuous' in learning_style.lower():
            score += 10
        elif 'structured' in learning_style.lower():
            score += 5
        
        return min(100.0, max(0.0, score))
    
    async def _assess_emotional_dimension(self, person_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión emocional."""
        # Factores emocionales
        emotional_intelligence = person_data.get('emotional_intelligence', 0)
        stress_management = person_data.get('stress_management', '')
        resilience = person_data.get('resilience', 0)
        
        score = 70.0  # Base
        
        # Ajustar por inteligencia emocional
        score += emotional_intelligence * 0.2
        
        # Ajustar por manejo del estrés
        if stress_management:
            score += 15
        
        # Ajustar por resiliencia
        score += resilience * 0.1
        
        return min(100.0, max(0.0, score))
    
    async def _assess_spiritual_dimension(self, person_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión espiritual."""
        # Factores espirituales
        values = person_data.get('values', {})
        stress_management = person_data.get('stress_management', '')
        personality_traits = person_data.get('personality_traits', {})
        
        score = 70.0  # Base
        
        # Ajustar por valores
        if values:
            score += 10
        
        # Ajustar por prácticas espirituales
        if 'meditation' in stress_management.lower():
            score += 15
        if 'mindfulness' in stress_management.lower():
            score += 10
        
        # Ajustar por apertura a la experiencia
        if personality_traits.get('openness', 0) > 70:
            score += 10
        
        return min(100.0, max(0.0, score))
    
    async def _assess_social_dimension(self, person_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión social."""
        # Factores sociales
        collaboration = person_data.get('collaboration', 0)
        communication_style = person_data.get('communication_style', '')
        personality_traits = person_data.get('personality_traits', {})
        
        score = 70.0  # Base
        
        # Ajustar por colaboración
        score += collaboration * 0.2
        
        # Ajustar por estilo de comunicación
        if 'empathetic' in communication_style.lower():
            score += 15
        elif 'direct' in communication_style.lower():
            score += 10
        
        # Ajustar por extraversión
        if personality_traits.get('extraversion', 0) > 70:
            score += 10
        
        return min(100.0, max(0.0, score))
    
    async def _assess_professional_dimension(self, person_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión profesional."""
        # Factores profesionales
        experience_years = person_data.get('experience_years', 0)
        skills = person_data.get('skills', [])
        career_goals = person_data.get('career_goals', [])
        
        score = 70.0  # Base
        
        # Ajustar por experiencia
        score += min(20, experience_years * 2)
        
        # Ajustar por habilidades
        score += min(15, len(skills) * 2)
        
        # Ajustar por objetivos de carrera
        if career_goals:
            score += 10
        
        return min(100.0, max(0.0, score))
    
    async def _assess_creative_dimension(self, person_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión creativa."""
        # Factores creativos
        creativity = person_data.get('creativity', 0)
        innovation_capacity = person_data.get('innovation_capacity', 0)
        personality_traits = person_data.get('personality_traits', {})
        
        score = 70.0  # Base
        
        # Ajustar por creatividad
        score += creativity * 0.2
        
        # Ajustar por capacidad de innovación
        score += innovation_capacity * 0.2
        
        # Ajustar por apertura a la experiencia
        if personality_traits.get('openness', 0) > 70:
            score += 10
        
        return min(100.0, max(0.0, score))
    
    async def _assess_intellectual_dimension(self, person_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión intelectual."""
        # Factores intelectuales
        analytical_thinking = person_data.get('analytical_thinking', 0)
        education = person_data.get('education', '')
        learning_style = person_data.get('learning_style', '')
        
        score = 70.0  # Base
        
        # Ajustar por pensamiento analítico
        score += analytical_thinking * 0.2
        
        # Ajustar por educación
        if 'phd' in education.lower():
            score += 15
        elif 'master' in education.lower():
            score += 10
        elif 'bachelor' in education.lower():
            score += 5
        
        # Ajustar por estilo de aprendizaje
        if 'continuous' in learning_style.lower():
            score += 10
        
        return min(100.0, max(0.0, score))
    
    # Métodos para evaluar dimensiones de vacantes
    async def _assess_vacancy_physical_dimension(self, vacancy_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión física de la vacante."""
        work_environment = vacancy_data.get('work_environment', '')
        stress_level = vacancy_data.get('stress_level', 0)
        work_life_balance = vacancy_data.get('work_life_balance', '')
        
        score = 70.0  # Base
        
        # Ajustar por entorno de trabajo
        if 'flexible' in work_environment.lower():
            score += 15
        elif 'active' in work_environment.lower():
            score += 10
        
        # Ajustar por nivel de estrés
        if stress_level < 30:
            score += 15
        elif stress_level > 70:
            score -= 10
        
        # Ajustar por balance vida-trabajo
        if 'excellent' in work_life_balance.lower():
            score += 15
        elif 'good' in work_life_balance.lower():
            score += 10
        
        return min(100.0, max(0.0, score))
    
    async def _assess_vacancy_mental_dimension(self, vacancy_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión mental de la vacante."""
        requirements = vacancy_data.get('requirements', {})
        responsibilities = vacancy_data.get('responsibilities', [])
        
        score = 70.0  # Base
        
        # Ajustar por complejidad de requisitos
        if requirements:
            score += 10
        
        # Ajustar por responsabilidades
        score += min(15, len(responsibilities) * 2)
        
        return min(100.0, max(0.0, score))
    
    async def _assess_vacancy_emotional_dimension(self, vacancy_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión emocional de la vacante."""
        team_size = vacancy_data.get('team_size', 0)
        collaboration_emphasis = vacancy_data.get('collaboration_emphasis', 0)
        
        score = 70.0  # Base
        
        # Ajustar por tamaño del equipo
        if team_size > 5:
            score += 10
        
        # Ajustar por énfasis en colaboración
        score += collaboration_emphasis * 0.2
        
        return min(100.0, max(0.0, score))
    
    async def _assess_vacancy_spiritual_dimension(self, vacancy_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión espiritual de la vacante."""
        company_culture = vacancy_data.get('company_culture', {})
        
        score = 70.0  # Base
        
        # Ajustar por cultura de empresa
        if company_culture:
            score += 10
        
        return min(100.0, max(0.0, score))
    
    async def _assess_vacancy_social_dimension(self, vacancy_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión social de la vacante."""
        team_size = vacancy_data.get('team_size', 0)
        collaboration_emphasis = vacancy_data.get('collaboration_emphasis', 0)
        
        score = 70.0  # Base
        
        # Ajustar por tamaño del equipo
        if team_size > 5:
            score += 15
        elif team_size > 2:
            score += 10
        
        # Ajustar por énfasis en colaboración
        score += collaboration_emphasis * 0.2
        
        return min(100.0, max(0.0, score))
    
    async def _assess_vacancy_professional_dimension(self, vacancy_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión profesional de la vacante."""
        requirements = vacancy_data.get('requirements', {})
        growth_opportunities = vacancy_data.get('growth_opportunities', [])
        mentoring_available = vacancy_data.get('mentoring_available', False)
        
        score = 70.0  # Base
        
        # Ajustar por requisitos
        if requirements:
            score += 10
        
        # Ajustar por oportunidades de crecimiento
        score += min(15, len(growth_opportunities) * 3)
        
        # Ajustar por mentoría disponible
        if mentoring_available:
            score += 10
        
        return min(100.0, max(0.0, score))
    
    async def _assess_vacancy_creative_dimension(self, vacancy_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión creativa de la vacante."""
        innovation_focus = vacancy_data.get('innovation_focus', 0)
        title = vacancy_data.get('title', '').lower()
        
        score = 70.0  # Base
        
        # Ajustar por enfoque en innovación
        score += innovation_focus * 0.2
        
        # Ajustar por tipo de trabajo
        if any(keyword in title for keyword in ['design', 'creative', 'art', 'content']):
            score += 15
        
        return min(100.0, max(0.0, score))
    
    async def _assess_vacancy_intellectual_dimension(self, vacancy_data: Dict[str, Any]) -> float:
        """Evalúa la dimensión intelectual de la vacante."""
        requirements = vacancy_data.get('requirements', {})
        responsibilities = vacancy_data.get('responsibilities', [])
        
        score = 70.0  # Base
        
        # Ajustar por complejidad de requisitos
        if requirements:
            score += 10
        
        # Ajustar por responsabilidades
        score += min(15, len(responsibilities) * 2)
        
        return min(100.0, max(0.0, score))
    
    def _determine_holistic_balance(self, dimensions: Dict[HolisticDimension, float]) -> HolisticBalance:
        """Determina el balance holístico basado en las dimensiones."""
        # Calcular score promedio
        if not dimensions:
            return HolisticBalance.BALANCED
        
        average_score = np.mean(list(dimensions.values()))
        
        # Determinar balance basado en umbrales
        if average_score >= self.balance_thresholds[HolisticBalance.HARMONIOUS]:
            return HolisticBalance.HARMONIOUS
        elif average_score >= self.balance_thresholds[HolisticBalance.BALANCED]:
            return HolisticBalance.BALANCED
        elif average_score >= self.balance_thresholds[HolisticBalance.UNBALANCED]:
            return HolisticBalance.UNBALANCED
        else:
            return HolisticBalance.DISCORDANT
    
    def _calculate_harmony_score(self, dimensions: Dict[HolisticDimension, float]) -> float:
        """Calcula el score de armonía entre dimensiones."""
        if not dimensions:
            return 0.0
        
        # Calcular desviación estándar (menor = mayor armonía)
        scores = list(dimensions.values())
        std_dev = np.std(scores)
        
        # Convertir a score de armonía (menor desviación = mayor armonía)
        harmony_score = max(0.0, 100.0 - (std_dev * 2))
        
        return harmony_score
    
    def _calculate_growth_potential(self, dimensions: Dict[HolisticDimension, float]) -> float:
        """Calcula el potencial de crecimiento holístico."""
        if not dimensions:
            return 0.0
        
        # Factores que contribuyen al crecimiento
        growth_factors = [
            dimensions.get(HolisticDimension.MENTAL, 0),
            dimensions.get(HolisticDimension.INTELLECTUAL, 0),
            dimensions.get(HolisticDimension.PROFESSIONAL, 0),
            dimensions.get(HolisticDimension.CREATIVE, 0)
        ]
        
        return np.mean(growth_factors)
    
    def _calculate_resilience_index(self, dimensions: Dict[HolisticDimension, float]) -> float:
        """Calcula el índice de resiliencia holística."""
        if not dimensions:
            return 0.0
        
        # Factores que contribuyen a la resiliencia
        resilience_factors = [
            dimensions.get(HolisticDimension.PHYSICAL, 0),
            dimensions.get(HolisticDimension.EMOTIONAL, 0),
            dimensions.get(HolisticDimension.SPIRITUAL, 0),
            dimensions.get(HolisticDimension.MENTAL, 0)
        ]
        
        return np.mean(resilience_factors)
    
    def _calculate_adaptability_quotient(self, dimensions: Dict[HolisticDimension, float]) -> float:
        """Calcula el cociente de adaptabilidad holística."""
        if not dimensions:
            return 0.0
        
        # Factores que contribuyen a la adaptabilidad
        adaptability_factors = [
            dimensions.get(HolisticDimension.MENTAL, 0),
            dimensions.get(HolisticDimension.SOCIAL, 0),
            dimensions.get(HolisticDimension.PROFESSIONAL, 0)
        ]
        
        return np.mean(adaptability_factors)
    
    def _calculate_integration_level(self, dimensions: Dict[HolisticDimension, float]) -> float:
        """Calcula el nivel de integración holística."""
        if not dimensions:
            return 0.0
        
        # Calcular correlación entre dimensiones (simplificado)
        scores = list(dimensions.values())
        
        # Usar variabilidad como proxy de integración
        # Menor variabilidad = mayor integración
        variability = np.std(scores)
        integration_score = max(0.0, 100.0 - (variability * 2))
        
        return integration_score
    
    async def _calculate_holistic_compatibility(
        self,
        person_profile: HolisticProfile,
        vacancy_profile: HolisticProfile
    ) -> float:
        """Calcula la compatibilidad holística entre perfiles."""
        try:
            # Compatibilidad por dimensión
            dimension_compatibility = []
            
            for dimension in HolisticDimension:
                person_score = person_profile.dimensions.get(dimension, 0)
                vacancy_score = vacancy_profile.dimensions.get(dimension, 0)
                
                # Calcular compatibilidad de dimensión
                compatibility = 100.0 - abs(person_score - vacancy_score)
                dimension_compatibility.append(compatibility)
            
            # Compatibilidad de balance holístico
            balance_compatibility = self._calculate_balance_compatibility(
                person_profile.overall_balance,
                vacancy_profile.overall_balance
            )
            
            # Compatibilidad de métricas holísticas
            metrics_compatibility = self._calculate_metrics_compatibility(person_profile, vacancy_profile)
            
            # Score final ponderado
            final_score = (
                np.mean(dimension_compatibility) * 0.6 +
                balance_compatibility * 0.2 +
                metrics_compatibility * 0.2
            )
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculando compatibilidad holística: {str(e)}")
            return 0.0
    
    def _calculate_balance_compatibility(
        self,
        person_balance: HolisticBalance,
        vacancy_balance: HolisticBalance
    ) -> float:
        """Calcula la compatibilidad de balance holístico."""
        # Matriz de compatibilidad de balance
        balance_compatibility = {
            HolisticBalance.HARMONIOUS: {
                HolisticBalance.HARMONIOUS: 100.0,
                HolisticBalance.BALANCED: 85.0,
                HolisticBalance.UNBALANCED: 60.0,
                HolisticBalance.DISCORDANT: 40.0
            },
            HolisticBalance.BALANCED: {
                HolisticBalance.HARMONIOUS: 85.0,
                HolisticBalance.BALANCED: 100.0,
                HolisticBalance.UNBALANCED: 75.0,
                HolisticBalance.DISCORDANT: 50.0
            },
            HolisticBalance.UNBALANCED: {
                HolisticBalance.HARMONIOUS: 60.0,
                HolisticBalance.BALANCED: 75.0,
                HolisticBalance.UNBALANCED: 100.0,
                HolisticBalance.DISCORDANT: 70.0
            },
            HolisticBalance.DISCORDANT: {
                HolisticBalance.HARMONIOUS: 40.0,
                HolisticBalance.BALANCED: 50.0,
                HolisticBalance.UNBALANCED: 70.0,
                HolisticBalance.DISCORDANT: 100.0
            }
        }
        
        return balance_compatibility.get(person_balance, {}).get(vacancy_balance, 50.0)
    
    def _calculate_metrics_compatibility(
        self,
        person_profile: HolisticProfile,
        vacancy_profile: HolisticProfile
    ) -> float:
        """Calcula la compatibilidad de métricas holísticas."""
        metrics = [
            ('harmony_score', person_profile.harmony_score, vacancy_profile.harmony_score),
            ('growth_potential', person_profile.growth_potential, vacancy_profile.growth_potential),
            ('resilience_index', person_profile.resilience_index, vacancy_profile.resilience_index),
            ('adaptability_quotient', person_profile.adaptability_quotient, vacancy_profile.adaptability_quotient),
            ('integration_level', person_profile.integration_level, vacancy_profile.integration_level)
        ]
        
        compatibility_scores = []
        for metric_name, person_value, vacancy_value in metrics:
            compatibility = 100.0 - abs(person_value - vacancy_value)
            compatibility_scores.append(compatibility)
        
        return np.mean(compatibility_scores)
    
    async def _adjust_holistic_score(
        self,
        base_score: float,
        business_unit: Optional[BusinessUnit] = None
    ) -> float:
        """Ajusta el score holístico basado en el contexto de negocio."""
        adjusted_score = base_score
        
        # Ajustes específicos por unidad de negocio (si aplica)
        if business_unit:
            # Implementar ajustes específicos por unidad de negocio
            pass
        
        return max(0.0, min(100.0, adjusted_score))
    
    def _get_dimension_description(self, dimension: HolisticDimension, score: float) -> str:
        """Obtiene la descripción de una dimensión basada en el score."""
        descriptions = {
            HolisticDimension.PHYSICAL: {
                'high': 'Excelente bienestar físico y manejo del estrés',
                'medium': 'Buen estado físico con áreas de mejora',
                'low': 'Necesita desarrollo en bienestar físico'
            },
            HolisticDimension.MENTAL: {
                'high': 'Excelente capacidad mental y adaptabilidad',
                'medium': 'Buena capacidad mental con potencial de desarrollo',
                'low': 'Necesita fortalecer capacidades mentales'
            },
            HolisticDimension.EMOTIONAL: {
                'high': 'Excelente inteligencia emocional y resiliencia',
                'medium': 'Buena inteligencia emocional con áreas de mejora',
                'low': 'Necesita desarrollar inteligencia emocional'
            },
            HolisticDimension.SPIRITUAL: {
                'high': 'Excelente conexión con valores y propósito',
                'medium': 'Buena conexión espiritual con potencial de desarrollo',
                'low': 'Necesita explorar dimensión espiritual'
            },
            HolisticDimension.SOCIAL: {
                'high': 'Excelente habilidades sociales y colaboración',
                'medium': 'Buenas habilidades sociales con áreas de mejora',
                'low': 'Necesita desarrollar habilidades sociales'
            },
            HolisticDimension.PROFESSIONAL: {
                'high': 'Excelente desarrollo profesional y experiencia',
                'medium': 'Buen desarrollo profesional con potencial de crecimiento',
                'low': 'Necesita desarrollo profesional'
            },
            HolisticDimension.CREATIVE: {
                'high': 'Excelente creatividad e innovación',
                'medium': 'Buena creatividad con potencial de desarrollo',
                'low': 'Necesita desarrollar creatividad'
            },
            HolisticDimension.INTELLECTUAL: {
                'high': 'Excelente capacidad intelectual y aprendizaje',
                'medium': 'Buena capacidad intelectual con potencial de desarrollo',
                'low': 'Necesita fortalecer capacidades intelectuales'
            }
        }
        
        level = 'high' if score >= 80 else 'medium' if score >= 60 else 'low'
        return descriptions.get(dimension, {}).get(level, 'Descripción no disponible')
    
    def _get_dimension_recommendations(self, dimension: HolisticDimension) -> List[str]:
        """Obtiene recomendaciones para una dimensión específica."""
        recommendations = {
            HolisticDimension.PHYSICAL: [
                'Desarrollar rutina de ejercicio regular',
                'Practicar técnicas de manejo del estrés',
                'Mejorar hábitos de sueño y nutrición'
            ],
            HolisticDimension.MENTAL: [
                'Desarrollar pensamiento crítico',
                'Practicar resolución de problemas',
                'Mantener aprendizaje continuo'
            ],
            HolisticDimension.EMOTIONAL: [
                'Desarrollar autoconciencia emocional',
                'Practicar empatía y compasión',
                'Mejorar regulación emocional'
            ],
            HolisticDimension.SPIRITUAL: [
                'Explorar valores personales',
                'Desarrollar sentido de propósito',
                'Practicar mindfulness o meditación'
            ],
            HolisticDimension.SOCIAL: [
                'Mejorar habilidades de comunicación',
                'Desarrollar trabajo en equipo',
                'Construir red profesional'
            ],
            HolisticDimension.PROFESSIONAL: [
                'Desarrollar habilidades técnicas',
                'Buscar oportunidades de crecimiento',
                'Construir experiencia relevante'
            ],
            HolisticDimension.CREATIVE: [
                'Explorar diferentes formas de expresión',
                'Desarrollar pensamiento divergente',
                'Buscar inspiración en diversas fuentes'
            ],
            HolisticDimension.INTELLECTUAL: [
                'Mantener curiosidad intelectual',
                'Desarrollar pensamiento analítico',
                'Buscar desafíos cognitivos'
            ]
        }
        
        return recommendations.get(dimension, ['Desarrollar esta dimensión'])
    
    async def _generate_holistic_recommendations(
        self,
        holistic_profile: HolisticProfile,
        insights: Dict[str, Any]
    ) -> List[str]:
        """Genera recomendaciones holísticas basadas en el perfil."""
        recommendations = []
        
        # Recomendaciones basadas en balance holístico
        if holistic_profile.overall_balance == HolisticBalance.DISCORDANT:
            recommendations.append("Trabajar en el equilibrio holístico general")
            recommendations.append("Desarrollar dimensiones más débiles")
        
        # Recomendaciones basadas en armonía
        if holistic_profile.harmony_score < 70:
            recommendations.append("Buscar mayor armonía entre dimensiones")
            recommendations.append("Desarrollar integración holística")
        
        # Recomendaciones basadas en potencial de crecimiento
        if holistic_profile.growth_potential > 80:
            recommendations.append("Aprovechar el alto potencial de crecimiento")
            recommendations.append("Buscar oportunidades de desarrollo acelerado")
        
        # Recomendaciones basadas en resiliencia
        if holistic_profile.resilience_index < 70:
            recommendations.append("Desarrollar mayor resiliencia holística")
            recommendations.append("Fortalecer capacidades de recuperación")
        
        return recommendations[:5]  # Limitar a 5 recomendaciones
    
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
    
    def _create_default_holistic_profile(self) -> HolisticProfile:
        """Crea un perfil holístico por defecto."""
        default_dimensions = {
            dimension: 70.0 for dimension in HolisticDimension
        }
        
        return HolisticProfile(
            dimensions=default_dimensions,
            overall_balance=HolisticBalance.BALANCED,
            harmony_score=70.0,
            growth_potential=70.0,
            resilience_index=70.0,
            adaptability_quotient=70.0,
            integration_level=70.0,
            timestamp=datetime.now()
        ) 