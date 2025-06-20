# app/ml/aura/compatibility_engine.py
"""
Motor de Compatibilidad del Sistema Aura

Este módulo implementa el análisis de compatibilidad holística entre
candidatos y vacantes, considerando múltiples dimensiones de alineación.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

from app.models import BusinessUnit

logger = logging.getLogger(__name__)

class CompatibilityDimension(Enum):
    """Dimensiones de compatibilidad analizadas."""
    SKILLS = "skills"
    EXPERIENCE = "experience"
    PERSONALITY = "personality"
    CULTURE = "culture"
    VALUES = "values"
    GOALS = "goals"
    WORK_STYLE = "work_style"
    LEADERSHIP = "leadership"
    INNOVATION = "innovation"
    COLLABORATION = "collaboration"
    ADAPTABILITY = "adaptability"
    GROWTH = "growth"

@dataclass
class CompatibilityScore:
    """Score de compatibilidad para una dimensión específica."""
    dimension: CompatibilityDimension
    score: float  # 0-100
    confidence: float  # 0-1
    weight: float  # 0-1
    insights: Dict[str, Any]
    recommendations: List[str]

class CompatibilityEngine:
    """
    Motor de análisis de compatibilidad holística.
    
    Evalúa la compatibilidad entre candidatos y vacantes considerando
    múltiples dimensiones y proporcionando análisis detallado.
    """
    
    def __init__(self):
        """Inicializa el motor de compatibilidad."""
        self.dimension_weights = {
            CompatibilityDimension.SKILLS: 0.20,
            CompatibilityDimension.EXPERIENCE: 0.15,
            CompatibilityDimension.PERSONALITY: 0.15,
            CompatibilityDimension.CULTURE: 0.12,
            CompatibilityDimension.VALUES: 0.10,
            CompatibilityDimension.GOALS: 0.08,
            CompatibilityDimension.WORK_STYLE: 0.08,
            CompatibilityDimension.LEADERSHIP: 0.05,
            CompatibilityDimension.INNOVATION: 0.03,
            CompatibilityDimension.COLLABORATION: 0.02,
            CompatibilityDimension.ADAPTABILITY: 0.01,
            CompatibilityDimension.GROWTH: 0.01
        }
        
        # Configurar pesos dinámicos basados en contexto
        self.context_weights = {
            'technical_role': {
                CompatibilityDimension.SKILLS: 0.30,
                CompatibilityDimension.EXPERIENCE: 0.25,
                CompatibilityDimension.INNOVATION: 0.15,
                CompatibilityDimension.PERSONALITY: 0.10,
                CompatibilityDimension.CULTURE: 0.10,
                CompatibilityDimension.VALUES: 0.10
            },
            'leadership_role': {
                CompatibilityDimension.LEADERSHIP: 0.25,
                CompatibilityDimension.PERSONALITY: 0.20,
                CompatibilityDimension.VALUES: 0.15,
                CompatibilityDimension.CULTURE: 0.15,
                CompatibilityDimension.GOALS: 0.10,
                CompatibilityDimension.COLLABORATION: 0.10,
                CompatibilityDimension.SKILLS: 0.05
            },
            'creative_role': {
                CompatibilityDimension.INNOVATION: 0.25,
                CompatibilityDimension.PERSONALITY: 0.20,
                CompatibilityDimension.CREATIVITY: 0.20,
                CompatibilityDimension.CULTURE: 0.15,
                CompatibilityDimension.WORK_STYLE: 0.10,
                CompatibilityDimension.SKILLS: 0.10
            },
            'collaborative_role': {
                CompatibilityDimension.COLLABORATION: 0.25,
                CompatibilityDimension.PERSONALITY: 0.20,
                CompatibilityDimension.CULTURE: 0.20,
                CompatibilityDimension.WORK_STYLE: 0.15,
                CompatibilityDimension.VALUES: 0.10,
                CompatibilityDimension.SKILLS: 0.10
            }
        }
        
        logger.info("Motor de compatibilidad inicializado")
    
    async def analyze_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any],
        business_unit: Optional[BusinessUnit] = None
    ) -> float:
        """
        Analiza la compatibilidad entre persona y vacante.
        
        Args:
            person_data: Datos de la persona
            vacancy_data: Datos de la vacante
            business_unit: Unidad de negocio para contexto
            
        Returns:
            Score de compatibilidad (0-100)
        """
        try:
            # Determinar contexto de la vacante
            context = self._determine_vacancy_context(vacancy_data)
            
            # Obtener pesos para el contexto
            weights = self._get_context_weights(context)
            
            # Analizar cada dimensión
            dimension_scores = []
            total_weight = 0
            
            for dimension in CompatibilityDimension:
                if dimension in weights:
                    score = await self._analyze_dimension(dimension, person_data, vacancy_data)
                    dimension_scores.append(CompatibilityScore(
                        dimension=dimension,
                        score=score['score'],
                        confidence=score['confidence'],
                        weight=weights[dimension],
                        insights=score['insights'],
                        recommendations=score['recommendations']
                    ))
                    total_weight += weights[dimension]
            
            # Calcular score final ponderado
            if total_weight > 0:
                final_score = sum(
                    ds.score * ds.weight for ds in dimension_scores
                ) / total_weight
            else:
                final_score = 0.0
            
            # Registrar análisis
            await self._log_compatibility_analysis(
                person_data['id'], 
                vacancy_data['id'], 
                final_score, 
                dimension_scores
            )
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error en análisis de compatibilidad: {str(e)}")
            return 0.0
    
    async def analyze_multi_vacancy_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancies_data: List[Dict[str, Any]],
        business_unit: Optional[BusinessUnit] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Analiza compatibilidad con múltiples vacantes.
        
        Args:
            person_data: Datos de la persona
            vacancies_data: Lista de datos de vacantes
            business_unit: Unidad de negocio para contexto
            
        Returns:
            Lista de tuplas (vacancy_data, compatibility_score)
        """
        try:
            results = []
            
            # Analizar cada vacante en paralelo
            tasks = []
            for vacancy_data in vacancies_data:
                task = self.analyze_compatibility(person_data, vacancy_data, business_unit)
                tasks.append((vacancy_data, task))
            
            # Esperar resultados
            for vacancy_data, task in tasks:
                try:
                    score = await task
                    results.append((vacancy_data, score))
                except Exception as e:
                    logger.error(f"Error analizando vacante {vacancy_data.get('id')}: {str(e)}")
                    results.append((vacancy_data, 0.0))
            
            # Ordenar por score de compatibilidad
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error en análisis multi-vacante: {str(e)}")
            return []
    
    async def get_compatibility_breakdown(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any],
        business_unit: Optional[BusinessUnit] = None
    ) -> Dict[str, Any]:
        """
        Obtiene el desglose detallado de compatibilidad.
        
        Args:
            person_data: Datos de la persona
            vacancy_data: Datos de la vacante
            business_unit: Unidad de negocio para contexto
            
        Returns:
            Diccionario con desglose detallado
        """
        try:
            context = self._determine_vacancy_context(vacancy_data)
            weights = self._get_context_weights(context)
            
            breakdown = {
                'overall_score': 0.0,
                'context': context,
                'dimensions': {},
                'strengths': [],
                'weaknesses': [],
                'recommendations': [],
                'confidence': 0.0
            }
            
            dimension_scores = []
            total_weight = 0
            
            for dimension in CompatibilityDimension:
                if dimension in weights:
                    score_data = await self._analyze_dimension(dimension, person_data, vacancy_data)
                    
                    dimension_scores.append(score_data['score'])
                    total_weight += weights[dimension]
                    
                    breakdown['dimensions'][dimension.value] = {
                        'score': score_data['score'],
                        'confidence': score_data['confidence'],
                        'weight': weights[dimension],
                        'insights': score_data['insights'],
                        'recommendations': score_data['recommendations']
                    }
                    
                    # Clasificar como fortaleza o debilidad
                    if score_data['score'] >= 80:
                        breakdown['strengths'].append({
                            'dimension': dimension.value,
                            'score': score_data['score'],
                            'description': score_data['insights'].get('description', '')
                        })
                    elif score_data['score'] < 60:
                        breakdown['weaknesses'].append({
                            'dimension': dimension.value,
                            'score': score_data['score'],
                            'description': score_data['insights'].get('description', ''),
                            'recommendations': score_data['recommendations']
                        })
            
            # Calcular score general
            if total_weight > 0:
                breakdown['overall_score'] = sum(
                    breakdown['dimensions'][dim.value]['score'] * breakdown['dimensions'][dim.value]['weight']
                    for dim in weights.keys()
                ) / total_weight
            
            # Calcular confianza general
            if dimension_scores:
                breakdown['confidence'] = np.mean([
                    breakdown['dimensions'][dim.value]['confidence']
                    for dim in weights.keys()
                ])
            
            # Generar recomendaciones generales
            breakdown['recommendations'] = self._generate_overall_recommendations(breakdown)
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Error obteniendo desglose de compatibilidad: {str(e)}")
            return {'error': str(e)}
    
    def _determine_vacancy_context(self, vacancy_data: Dict[str, Any]) -> str:
        """Determina el contexto de la vacante."""
        title = vacancy_data.get('title', '').lower()
        description = vacancy_data.get('description', '').lower()
        
        # Palabras clave para cada contexto
        technical_keywords = ['developer', 'engineer', 'programmer', 'technical', 'software', 'data', 'analyst']
        leadership_keywords = ['manager', 'director', 'lead', 'head', 'chief', 'supervisor', 'coordinator']
        creative_keywords = ['designer', 'creative', 'artist', 'content', 'marketing', 'brand']
        collaborative_keywords = ['coordinator', 'facilitator', 'team', 'collaboration', 'support']
        
        # Determinar contexto
        if any(keyword in title or keyword in description for keyword in technical_keywords):
            return 'technical_role'
        elif any(keyword in title or keyword in description for keyword in leadership_keywords):
            return 'leadership_role'
        elif any(keyword in title or keyword in description for keyword in creative_keywords):
            return 'creative_role'
        elif any(keyword in title or keyword in description for keyword in collaborative_keywords):
            return 'collaborative_role'
        else:
            return 'general'
    
    def _get_context_weights(self, context: str) -> Dict[CompatibilityDimension, float]:
        """Obtiene los pesos para un contexto específico."""
        if context in self.context_weights:
            return self.context_weights[context]
        else:
            return self.dimension_weights
    
    async def _analyze_dimension(
        self,
        dimension: CompatibilityDimension,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza una dimensión específica de compatibilidad."""
        try:
            if dimension == CompatibilityDimension.SKILLS:
                return await self._analyze_skills_compatibility(person_data, vacancy_data)
            elif dimension == CompatibilityDimension.EXPERIENCE:
                return await self._analyze_experience_compatibility(person_data, vacancy_data)
            elif dimension == CompatibilityDimension.PERSONALITY:
                return await self._analyze_personality_compatibility(person_data, vacancy_data)
            elif dimension == CompatibilityDimension.CULTURE:
                return await self._analyze_culture_compatibility(person_data, vacancy_data)
            elif dimension == CompatibilityDimension.VALUES:
                return await self._analyze_values_compatibility(person_data, vacancy_data)
            elif dimension == CompatibilityDimension.GOALS:
                return await self._analyze_goals_compatibility(person_data, vacancy_data)
            elif dimension == CompatibilityDimension.WORK_STYLE:
                return await self._analyze_work_style_compatibility(person_data, vacancy_data)
            elif dimension == CompatibilityDimension.LEADERSHIP:
                return await self._analyze_leadership_compatibility(person_data, vacancy_data)
            elif dimension == CompatibilityDimension.INNOVATION:
                return await self._analyze_innovation_compatibility(person_data, vacancy_data)
            elif dimension == CompatibilityDimension.COLLABORATION:
                return await self._analyze_collaboration_compatibility(person_data, vacancy_data)
            elif dimension == CompatibilityDimension.ADAPTABILITY:
                return await self._analyze_adaptability_compatibility(person_data, vacancy_data)
            elif dimension == CompatibilityDimension.GROWTH:
                return await self._analyze_growth_compatibility(person_data, vacancy_data)
            else:
                return self._default_dimension_analysis(dimension)
                
        except Exception as e:
            logger.error(f"Error analizando dimensión {dimension}: {str(e)}")
            return self._default_dimension_analysis(dimension)
    
    async def _analyze_skills_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza compatibilidad de habilidades."""
        person_skills = set(person_data.get('skills', []))
        required_skills = set(vacancy_data.get('requirements', {}).get('skills', []))
        
        if not required_skills:
            return {
                'score': 75.0,
                'confidence': 0.6,
                'insights': {'description': 'No se especificaron habilidades requeridas'},
                'recommendations': ['Verificar requisitos de habilidades']
            }
        
        # Calcular match de habilidades
        matching_skills = person_skills.intersection(required_skills)
        missing_skills = required_skills - person_skills
        
        skill_match_ratio = len(matching_skills) / len(required_skills) if required_skills else 0
        
        # Calcular score
        score = min(100.0, skill_match_ratio * 100 + 20)  # Bonus por habilidades adicionales
        
        # Ajustar score basado en habilidades adicionales
        additional_skills = person_skills - required_skills
        if additional_skills:
            score = min(100.0, score + len(additional_skills) * 2)
        
        confidence = 0.8 if person_skills else 0.4
        
        insights = {
            'description': f"Match de {len(matching_skills)}/{len(required_skills)} habilidades requeridas",
            'matching_skills': list(matching_skills),
            'missing_skills': list(missing_skills),
            'additional_skills': list(additional_skills)
        }
        
        recommendations = []
        if missing_skills:
            recommendations.append(f"Desarrollar habilidades: {', '.join(list(missing_skills)[:3])}")
        if additional_skills:
            recommendations.append("Destacar habilidades adicionales en el CV")
        
        return {
            'score': score,
            'confidence': confidence,
            'insights': insights,
            'recommendations': recommendations
        }
    
    async def _analyze_experience_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza compatibilidad de experiencia."""
        person_experience = person_data.get('experience_years', 0)
        required_experience = vacancy_data.get('requirements', {}).get('experience_years', 0)
        
        if required_experience == 0:
            return {
                'score': 80.0,
                'confidence': 0.7,
                'insights': {'description': 'No se especificó experiencia requerida'},
                'recommendations': ['Verificar requisitos de experiencia']
            }
        
        # Calcular score basado en diferencia de experiencia
        experience_diff = person_experience - required_experience
        
        if experience_diff >= 0:
            # Experiencia suficiente o superior
            score = min(100.0, 80 + (experience_diff * 2))
        else:
            # Experiencia insuficiente
            score = max(0.0, 60 + (experience_diff * 5))
        
        confidence = 0.9
        
        insights = {
            'description': f"{person_experience} años vs {required_experience} requeridos",
            'experience_gap': experience_diff,
            'experience_level': 'superior' if experience_diff > 2 else 'adecuada' if experience_diff >= 0 else 'insuficiente'
        }
        
        recommendations = []
        if experience_diff < 0:
            recommendations.append(f"Ganar {abs(experience_diff)} años más de experiencia")
        elif experience_diff > 5:
            recommendations.append("Considerar roles más senior")
        
        return {
            'score': score,
            'confidence': confidence,
            'insights': insights,
            'recommendations': recommendations
        }
    
    async def _analyze_personality_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza compatibilidad de personalidad."""
        person_traits = person_data.get('personality_traits', {})
        work_environment = vacancy_data.get('work_environment', '')
        
        # Análisis básico de personalidad
        score = 75.0
        confidence = 0.6
        
        insights = {
            'description': 'Análisis de personalidad básico',
            'personality_type': person_traits.get('type', 'No especificado'),
            'work_environment': work_environment
        }
        
        recommendations = ['Completar evaluación de personalidad para análisis más preciso']
        
        return {
            'score': score,
            'confidence': confidence,
            'insights': insights,
            'recommendations': recommendations
        }
    
    async def _analyze_culture_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza compatibilidad cultural."""
        person_culture = person_data.get('cultural_preferences', {})
        company_culture = vacancy_data.get('company_culture', {})
        
        # Análisis básico de cultura
        score = 70.0
        confidence = 0.5
        
        insights = {
            'description': 'Análisis cultural básico',
            'person_culture': person_culture,
            'company_culture': company_culture
        }
        
        recommendations = ['Investigar cultura de la empresa', 'Evaluar valores compartidos']
        
        return {
            'score': score,
            'confidence': confidence,
            'insights': insights,
            'recommendations': recommendations
        }
    
    async def _analyze_values_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza compatibilidad de valores."""
        person_values = person_data.get('values', {})
        
        score = 75.0
        confidence = 0.6
        
        insights = {
            'description': 'Análisis de valores básico',
            'person_values': person_values
        }
        
        recommendations = ['Clarificar valores personales', 'Investigar valores de la empresa']
        
        return {
            'score': score,
            'confidence': confidence,
            'insights': insights,
            'recommendations': recommendations
        }
    
    async def _analyze_goals_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza compatibilidad de objetivos."""
        person_goals = person_data.get('career_goals', [])
        growth_opportunities = vacancy_data.get('growth_opportunities', [])
        
        score = 70.0
        confidence = 0.5
        
        insights = {
            'description': 'Análisis de objetivos básico',
            'person_goals': person_goals,
            'growth_opportunities': growth_opportunities
        }
        
        recommendations = ['Clarificar objetivos de carrera', 'Evaluar oportunidades de crecimiento']
        
        return {
            'score': score,
            'confidence': confidence,
            'insights': insights,
            'recommendations': recommendations
        }
    
    async def _analyze_work_style_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza compatibilidad de estilo de trabajo."""
        person_style = person_data.get('work_style', '')
        remote_work = vacancy_data.get('remote_work', False)
        
        score = 75.0
        confidence = 0.6
        
        insights = {
            'description': 'Análisis de estilo de trabajo básico',
            'person_style': person_style,
            'remote_work': remote_work
        }
        
        recommendations = ['Evaluar preferencias de trabajo remoto', 'Considerar flexibilidad laboral']
        
        return {
            'score': score,
            'confidence': confidence,
            'insights': insights,
            'recommendations': recommendations
        }
    
    async def _analyze_leadership_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza compatibilidad de liderazgo."""
        leadership_style = person_data.get('leadership_style', '')
        leadership_requirements = vacancy_data.get('leadership_requirements', [])
        
        score = 70.0
        confidence = 0.5
        
        insights = {
            'description': 'Análisis de liderazgo básico',
            'leadership_style': leadership_style,
            'leadership_requirements': leadership_requirements
        }
        
        recommendations = ['Desarrollar habilidades de liderazgo', 'Evaluar estilo de liderazgo']
        
        return {
            'score': score,
            'confidence': confidence,
            'insights': insights,
            'recommendations': recommendations
        }
    
    async def _analyze_innovation_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza compatibilidad de innovación."""
        innovation_capacity = person_data.get('innovation_capacity', 0)
        innovation_focus = vacancy_data.get('innovation_focus', 0)
        
        score = 75.0
        confidence = 0.6
        
        insights = {
            'description': 'Análisis de innovación básico',
            'innovation_capacity': innovation_capacity,
            'innovation_focus': innovation_focus
        }
        
        recommendations = ['Desarrollar capacidad de innovación', 'Buscar roles innovadores']
        
        return {
            'score': score,
            'confidence': confidence,
            'insights': insights,
            'recommendations': recommendations
        }
    
    async def _analyze_collaboration_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza compatibilidad de colaboración."""
        collaboration = person_data.get('collaboration', 0)
        collaboration_emphasis = vacancy_data.get('collaboration_emphasis', 0)
        
        score = 75.0
        confidence = 0.6
        
        insights = {
            'description': 'Análisis de colaboración básico',
            'collaboration_level': collaboration,
            'collaboration_emphasis': collaboration_emphasis
        }
        
        recommendations = ['Desarrollar habilidades de colaboración', 'Buscar entornos colaborativos']
        
        return {
            'score': score,
            'confidence': confidence,
            'insights': insights,
            'recommendations': recommendations
        }
    
    async def _analyze_adaptability_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza compatibilidad de adaptabilidad."""
        adaptability = person_data.get('adaptability', 0)
        
        score = 75.0
        confidence = 0.6
        
        insights = {
            'description': 'Análisis de adaptabilidad básico',
            'adaptability_level': adaptability
        }
        
        recommendations = ['Desarrollar capacidad de adaptación', 'Buscar entornos dinámicos']
        
        return {
            'score': score,
            'confidence': confidence,
            'insights': insights,
            'recommendations': recommendations
        }
    
    async def _analyze_growth_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza compatibilidad de crecimiento."""
        growth_opportunities = vacancy_data.get('growth_opportunities', [])
        mentoring_available = vacancy_data.get('mentoring_available', False)
        training_provided = vacancy_data.get('training_provided', False)
        
        score = 70.0
        confidence = 0.5
        
        insights = {
            'description': 'Análisis de crecimiento básico',
            'growth_opportunities': growth_opportunities,
            'mentoring_available': mentoring_available,
            'training_provided': training_provided
        }
        
        recommendations = ['Evaluar oportunidades de desarrollo', 'Buscar programas de mentoría']
        
        return {
            'score': score,
            'confidence': confidence,
            'insights': insights,
            'recommendations': recommendations
        }
    
    def _default_dimension_analysis(self, dimension: CompatibilityDimension) -> Dict[str, Any]:
        """Análisis por defecto para una dimensión."""
        return {
            'score': 70.0,
            'confidence': 0.5,
            'insights': {'description': f'Análisis básico de {dimension.value}'},
            'recommendations': [f'Completar evaluación de {dimension.value}']
        }
    
    def _generate_overall_recommendations(self, breakdown: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones generales basadas en el desglose."""
        recommendations = []
        
        # Recomendaciones basadas en fortalezas
        if breakdown['strengths']:
            top_strength = breakdown['strengths'][0]
            recommendations.append(f"Destacar {top_strength['dimension']} en el CV")
        
        # Recomendaciones basadas en debilidades
        if breakdown['weaknesses']:
            top_weakness = breakdown['weaknesses'][0]
            recommendations.extend(top_weakness['recommendations'])
        
        # Recomendaciones generales
        if breakdown['overall_score'] < 60:
            recommendations.append("Considerar desarrollo adicional antes de aplicar")
        elif breakdown['overall_score'] > 85:
            recommendations.append("Excelente candidato para el rol")
        
        return recommendations[:5]  # Limitar a 5 recomendaciones
    
    async def _log_compatibility_analysis(
        self,
        person_id: int,
        vacancy_id: int,
        score: float,
        dimension_scores: List[CompatibilityScore]
    ) -> None:
        """Registra el análisis de compatibilidad."""
        try:
            logger.info(
                f"Análisis de compatibilidad: Persona {person_id} - Vacante {vacancy_id} = {score:.2f}"
            )
            
            # Aquí se podría guardar en base de datos para análisis histórico
            # await self._save_compatibility_analysis(person_id, vacancy_id, score, dimension_scores)
            
        except Exception as e:
            logger.error(f"Error registrando análisis de compatibilidad: {str(e)}") 