"""
Analizador de Energía del Sistema Aura

Este módulo implementa el análisis de patrones energéticos y compatibilidad
energética entre candidatos y entornos de trabajo.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime

from app.models import Person, Vacante

logger = logging.getLogger(__name__)

class EnergyType(Enum):
    """Tipos de energía identificados en el análisis."""
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    SOCIAL = "social"
    LEADERSHIP = "leadership"
    TECHNICAL = "technical"
    EMOTIONAL = "emotional"
    PHYSICAL = "physical"
    MENTAL = "mental"
    SPIRITUAL = "spiritual"
    PRACTICAL = "practical"

class EnergyLevel(Enum):
    """Niveles de energía."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VARIABLE = "variable"

@dataclass
class EnergyProfile:
    """Perfil energético de una persona o entorno."""
    primary_energy: EnergyType
    secondary_energy: EnergyType
    energy_level: EnergyLevel
    energy_patterns: Dict[str, float]
    compatibility_factors: Dict[str, float]
    timestamp: datetime

class EnergyAnalyzer:
    """
    Analizador de patrones energéticos y compatibilidad.
    
    Evalúa los patrones de energía de personas y entornos de trabajo,
    proporcionando análisis de compatibilidad energética.
    """
    
    def __init__(self):
        """Inicializa el analizador de energía."""
        self.energy_weights = {
            'personality': 0.30,
            'work_style': 0.25,
            'communication': 0.20,
            'motivation': 0.15,
            'stress_response': 0.10
        }
        
        # Patrones energéticos por tipo de trabajo
        self.work_energy_patterns = {
            'creative': {
                'primary': EnergyType.CREATIVE,
                'secondary': EnergyType.EMOTIONAL,
                'level': EnergyLevel.HIGH,
                'characteristics': ['innovación', 'expresividad', 'flexibilidad']
            },
            'technical': {
                'primary': EnergyType.TECHNICAL,
                'secondary': EnergyType.ANALYTICAL,
                'level': EnergyLevel.MEDIUM,
                'characteristics': ['precisión', 'lógica', 'concentración']
            },
            'leadership': {
                'primary': EnergyType.LEADERSHIP,
                'secondary': EnergyType.SOCIAL,
                'level': EnergyLevel.HIGH,
                'characteristics': ['inspiración', 'comunicación', 'estrategia']
            },
            'collaborative': {
                'primary': EnergyType.SOCIAL,
                'secondary': EnergyType.PRACTICAL,
                'level': EnergyLevel.MEDIUM,
                'characteristics': ['cooperación', 'empatía', 'organización']
            },
            'analytical': {
                'primary': EnergyType.ANALYTICAL,
                'secondary': EnergyType.MENTAL,
                'level': EnergyLevel.MEDIUM,
                'characteristics': ['análisis', 'investigación', 'pensamiento crítico']
            }
        }
        
        logger.info("Analizador de energía inicializado")
    
    async def analyze_energy_compatibility(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> float:
        """
        Analiza la compatibilidad energética entre persona y vacante.
        
        Args:
            person_data: Datos de la persona
            vacancy_data: Datos de la vacante
            
        Returns:
            Score de compatibilidad energética (0-100)
        """
        try:
            # Extraer perfiles energéticos
            person_energy = await self.extract_energy_patterns(person_data)
            vacancy_energy = await self.extract_vacancy_energy_patterns(vacancy_data)
            
            # Calcular compatibilidad
            compatibility_score = await self._calculate_energy_compatibility(
                person_energy, vacancy_energy
            )
            
            # Ajustar por factores contextuales
            adjusted_score = await self._adjust_energy_score(
                compatibility_score, person_data, vacancy_data
            )
            
            return adjusted_score
            
        except Exception as e:
            logger.error(f"Error en análisis de compatibilidad energética: {str(e)}")
            return 0.0
    
    async def extract_energy_patterns(self, person_data: Dict[str, Any]) -> EnergyProfile:
        """
        Extrae patrones energéticos de una persona.
        
        Args:
            person_data: Datos de la persona
            
        Returns:
            Perfil energético de la persona
        """
        try:
            # Analizar diferentes aspectos energéticos
            personality_energy = await self._analyze_personality_energy(person_data)
            work_style_energy = await self._analyze_work_style_energy(person_data)
            communication_energy = await self._analyze_communication_energy(person_data)
            motivation_energy = await self._analyze_motivation_energy(person_data)
            stress_energy = await self._analyze_stress_energy(person_data)
            
            # Combinar patrones energéticos
            combined_patterns = {
                'personality': personality_energy,
                'work_style': work_style_energy,
                'communication': communication_energy,
                'motivation': motivation_energy,
                'stress_response': stress_energy
            }
            
            # Determinar energía primaria y secundaria
            primary_energy = self._determine_primary_energy(combined_patterns)
            secondary_energy = self._determine_secondary_energy(combined_patterns, primary_energy)
            
            # Determinar nivel de energía
            energy_level = self._determine_energy_level(combined_patterns)
            
            # Calcular factores de compatibilidad
            compatibility_factors = await self._calculate_compatibility_factors(combined_patterns)
            
            return EnergyProfile(
                primary_energy=primary_energy,
                secondary_energy=secondary_energy,
                energy_level=energy_level,
                energy_patterns=combined_patterns,
                compatibility_factors=compatibility_factors,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error extrayendo patrones energéticos: {str(e)}")
            return self._create_default_energy_profile()
    
    async def extract_vacancy_energy_patterns(self, vacancy_data: Dict[str, Any]) -> EnergyProfile:
        """
        Extrae patrones energéticos de una vacante.
        
        Args:
            vacancy_data: Datos de la vacante
            
        Returns:
            Perfil energético de la vacante
        """
        try:
            # Determinar tipo de trabajo
            work_type = self._determine_work_type(vacancy_data)
            
            # Obtener patrón energético del tipo de trabajo
            if work_type in self.work_energy_patterns:
                pattern = self.work_energy_patterns[work_type]
                
                # Crear patrones energéticos específicos
                energy_patterns = {
                    'work_environment': pattern['characteristics'],
                    'energy_requirements': {
                        'primary': pattern['primary'].value,
                        'secondary': pattern['secondary'].value,
                        'level': pattern['level'].value
                    },
                    'team_dynamics': self._analyze_team_energy_requirements(vacancy_data),
                    'stress_factors': self._analyze_stress_factors(vacancy_data),
                    'growth_energy': self._analyze_growth_energy_requirements(vacancy_data)
                }
                
                compatibility_factors = {
                    'environment_fit': 0.8,
                    'team_synergy': 0.7,
                    'stress_compatibility': 0.6,
                    'growth_alignment': 0.7
                }
                
                return EnergyProfile(
                    primary_energy=pattern['primary'],
                    secondary_energy=pattern['secondary'],
                    energy_level=pattern['level'],
                    energy_patterns=energy_patterns,
                    compatibility_factors=compatibility_factors,
                    timestamp=datetime.now()
                )
            else:
                return self._create_default_energy_profile()
                
        except Exception as e:
            logger.error(f"Error extrayendo patrones energéticos de vacante: {str(e)}")
            return self._create_default_energy_profile()
    
    async def analyze_energy_stability(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza la estabilidad energética de una persona.
        
        Args:
            person_data: Datos de la persona
            
        Returns:
            Análisis de estabilidad energética
        """
        try:
            # Extraer patrones energéticos
            energy_profile = await self.extract_energy_patterns(person_data)
            
            # Analizar estabilidad
            stability_analysis = {
                'overall_stability': self._calculate_energy_stability(energy_profile),
                'stress_resilience': self._analyze_stress_resilience(person_data),
                'energy_consistency': self._analyze_energy_consistency(energy_profile),
                'recovery_patterns': self._analyze_recovery_patterns(person_data),
                'adaptability': self._analyze_energy_adaptability(person_data)
            }
            
            return stability_analysis
            
        except Exception as e:
            logger.error(f"Error analizando estabilidad energética: {str(e)}")
            return {'error': str(e)}
    
    async def generate_energy_recommendations(
        self,
        person_data: Dict[str, Any],
        energy_analysis: Dict[str, Any]
    ) -> List[str]:
        """
        Genera recomendaciones basadas en el análisis energético.
        
        Args:
            person_data: Datos de la persona
            energy_analysis: Análisis energético
            
        Returns:
            Lista de recomendaciones energéticas
        """
        try:
            recommendations = []
            
            # Recomendaciones basadas en estabilidad
            stability = energy_analysis.get('overall_stability', 0)
            if stability < 60:
                recommendations.append("Desarrollar técnicas de gestión energética")
                recommendations.append("Establecer rutinas de descanso y recuperación")
            
            # Recomendaciones basadas en resiliencia al estrés
            stress_resilience = energy_analysis.get('stress_resilience', 0)
            if stress_resilience < 70:
                recommendations.append("Practicar técnicas de manejo del estrés")
                recommendations.append("Desarrollar estrategias de recuperación energética")
            
            # Recomendaciones basadas en adaptabilidad
            adaptability = energy_analysis.get('adaptability', 0)
            if adaptability < 65:
                recommendations.append("Desarrollar flexibilidad energética")
                recommendations.append("Practicar adaptación a diferentes entornos")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones energéticas: {str(e)}")
            return ["Completar evaluación energética para recomendaciones más precisas"]
    
    async def _analyze_personality_energy(self, person_data: Dict[str, Any]) -> Dict[str, float]:
        """Analiza la energía de personalidad."""
        personality_traits = person_data.get('personality_traits', {})
        
        energy_scores = {
            'creative': 0.0,
            'analytical': 0.0,
            'social': 0.0,
            'leadership': 0.0,
            'emotional': 0.0,
            'practical': 0.0
        }
        
        # Mapear rasgos de personalidad a energías
        if personality_traits.get('openness', 0) > 70:
            energy_scores['creative'] += 0.3
            energy_scores['analytical'] += 0.2
        
        if personality_traits.get('extraversion', 0) > 70:
            energy_scores['social'] += 0.4
            energy_scores['leadership'] += 0.2
        
        if personality_traits.get('conscientiousness', 0) > 70:
            energy_scores['practical'] += 0.3
            energy_scores['analytical'] += 0.2
        
        if personality_traits.get('agreeableness', 0) > 70:
            energy_scores['social'] += 0.2
            energy_scores['emotional'] += 0.2
        
        return energy_scores
    
    async def _analyze_work_style_energy(self, person_data: Dict[str, Any]) -> Dict[str, float]:
        """Analiza la energía del estilo de trabajo."""
        work_style = person_data.get('work_style', '')
        
        energy_scores = {
            'creative': 0.0,
            'analytical': 0.0,
            'social': 0.0,
            'leadership': 0.0,
            'technical': 0.0,
            'practical': 0.0
        }
        
        # Mapear estilos de trabajo a energías
        if 'collaborative' in work_style.lower():
            energy_scores['social'] += 0.4
            energy_scores['leadership'] += 0.2
        
        if 'independent' in work_style.lower():
            energy_scores['analytical'] += 0.3
            energy_scores['technical'] += 0.2
        
        if 'creative' in work_style.lower():
            energy_scores['creative'] += 0.4
            energy_scores['emotional'] += 0.2
        
        if 'structured' in work_style.lower():
            energy_scores['practical'] += 0.3
            energy_scores['analytical'] += 0.2
        
        return energy_scores
    
    async def _analyze_communication_energy(self, person_data: Dict[str, Any]) -> Dict[str, float]:
        """Analiza la energía de comunicación."""
        communication_style = person_data.get('communication_style', '')
        
        energy_scores = {
            'social': 0.0,
            'leadership': 0.0,
            'analytical': 0.0,
            'emotional': 0.0,
            'practical': 0.0
        }
        
        # Mapear estilos de comunicación a energías
        if 'direct' in communication_style.lower():
            energy_scores['practical'] += 0.3
            energy_scores['leadership'] += 0.2
        
        if 'empathetic' in communication_style.lower():
            energy_scores['emotional'] += 0.4
            energy_scores['social'] += 0.2
        
        if 'analytical' in communication_style.lower():
            energy_scores['analytical'] += 0.4
            energy_scores['technical'] += 0.2
        
        if 'inspirational' in communication_style.lower():
            energy_scores['leadership'] += 0.4
            energy_scores['creative'] += 0.2
        
        return energy_scores
    
    async def _analyze_motivation_energy(self, person_data: Dict[str, Any]) -> Dict[str, float]:
        """Analiza la energía de motivación."""
        motivations = person_data.get('motivations', [])
        
        energy_scores = {
            'creative': 0.0,
            'leadership': 0.0,
            'social': 0.0,
            'practical': 0.0,
            'emotional': 0.0
        }
        
        # Mapear motivaciones a energías
        for motivation in motivations:
            if 'innovation' in motivation.lower():
                energy_scores['creative'] += 0.3
            elif 'leadership' in motivation.lower():
                energy_scores['leadership'] += 0.3
            elif 'collaboration' in motivation.lower():
                energy_scores['social'] += 0.3
            elif 'results' in motivation.lower():
                energy_scores['practical'] += 0.3
            elif 'impact' in motivation.lower():
                energy_scores['emotional'] += 0.3
        
        return energy_scores
    
    async def _analyze_stress_energy(self, person_data: Dict[str, Any]) -> Dict[str, float]:
        """Analiza la energía de respuesta al estrés."""
        stress_management = person_data.get('stress_management', '')
        resilience = person_data.get('resilience', 0)
        
        energy_scores = {
            'emotional': 0.0,
            'practical': 0.0,
            'analytical': 0.0,
            'social': 0.0
        }
        
        # Mapear manejo del estrés a energías
        if 'mindfulness' in stress_management.lower():
            energy_scores['emotional'] += 0.3
        elif 'exercise' in stress_management.lower():
            energy_scores['practical'] += 0.3
        elif 'analysis' in stress_management.lower():
            energy_scores['analytical'] += 0.3
        elif 'social' in stress_management.lower():
            energy_scores['social'] += 0.3
        
        # Ajustar por nivel de resiliencia
        if resilience > 80:
            for key in energy_scores:
                energy_scores[key] += 0.1
        
        return energy_scores
    
    def _determine_primary_energy(self, energy_patterns: Dict[str, Dict[str, float]]) -> EnergyType:
        """Determina la energía primaria basada en los patrones."""
        # Combinar todos los patrones energéticos
        combined_energy = {}
        
        for pattern_type, pattern_scores in energy_patterns.items():
            for energy_type, score in pattern_scores.items():
                if energy_type not in combined_energy:
                    combined_energy[energy_type] = 0.0
                combined_energy[energy_type] += score * self.energy_weights.get(pattern_type, 0.1)
        
        # Encontrar la energía con mayor score
        if combined_energy:
            primary_energy_name = max(combined_energy, key=combined_energy.get)
            return EnergyType(primary_energy_name)
        else:
            return EnergyType.PRACTICAL
    
    def _determine_secondary_energy(
        self,
        energy_patterns: Dict[str, Dict[str, float]],
        primary_energy: EnergyType
    ) -> EnergyType:
        """Determina la energía secundaria."""
        # Combinar patrones energéticos excluyendo la primaria
        combined_energy = {}
        
        for pattern_type, pattern_scores in energy_patterns.items():
            for energy_type, score in pattern_scores.items():
                if energy_type != primary_energy.value:
                    if energy_type not in combined_energy:
                        combined_energy[energy_type] = 0.0
                    combined_energy[energy_type] += score * self.energy_weights.get(pattern_type, 0.1)
        
        # Encontrar la energía secundaria con mayor score
        if combined_energy:
            secondary_energy_name = max(combined_energy, key=combined_energy.get)
            return EnergyType(secondary_energy_name)
        else:
            return EnergyType.SOCIAL
    
    def _determine_energy_level(self, energy_patterns: Dict[str, Dict[str, float]]) -> EnergyLevel:
        """Determina el nivel de energía."""
        # Calcular nivel promedio de energía
        total_energy = 0.0
        count = 0
        
        for pattern_scores in energy_patterns.values():
            for score in pattern_scores.values():
                total_energy += score
                count += 1
        
        if count > 0:
            average_energy = total_energy / count
            
            if average_energy > 0.7:
                return EnergyLevel.HIGH
            elif average_energy > 0.4:
                return EnergyLevel.MEDIUM
            else:
                return EnergyLevel.LOW
        else:
            return EnergyLevel.MEDIUM
    
    async def _calculate_compatibility_factors(
        self,
        energy_patterns: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Calcula factores de compatibilidad energética."""
        return {
            'stability': 0.7,
            'adaptability': 0.6,
            'resilience': 0.8,
            'growth_potential': 0.7,
            'team_synergy': 0.6
        }
    
    async def _calculate_energy_compatibility(
        self,
        person_energy: EnergyProfile,
        vacancy_energy: EnergyProfile
    ) -> float:
        """Calcula la compatibilidad energética entre persona y vacante."""
        try:
            # Compatibilidad de energía primaria
            primary_compatibility = self._calculate_energy_type_compatibility(
                person_energy.primary_energy,
                vacancy_energy.primary_energy
            )
            
            # Compatibilidad de energía secundaria
            secondary_compatibility = self._calculate_energy_type_compatibility(
                person_energy.secondary_energy,
                vacancy_energy.secondary_energy
            )
            
            # Compatibilidad de nivel de energía
            level_compatibility = self._calculate_energy_level_compatibility(
                person_energy.energy_level,
                vacancy_energy.energy_level
            )
            
            # Calcular score final ponderado
            final_score = (
                primary_compatibility * 0.4 +
                secondary_compatibility * 0.3 +
                level_compatibility * 0.3
            )
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculando compatibilidad energética: {str(e)}")
            return 0.0
    
    def _calculate_energy_type_compatibility(
        self,
        person_energy: EnergyType,
        vacancy_energy: EnergyType
    ) -> float:
        """Calcula compatibilidad entre tipos de energía."""
        # Matriz de compatibilidad energética
        compatibility_matrix = {
            EnergyType.CREATIVE: {
                EnergyType.CREATIVE: 1.0,
                EnergyType.ANALYTICAL: 0.6,
                EnergyType.SOCIAL: 0.8,
                EnergyType.LEADERSHIP: 0.7,
                EnergyType.TECHNICAL: 0.5,
                EnergyType.EMOTIONAL: 0.9,
                EnergyType.PHYSICAL: 0.4,
                EnergyType.MENTAL: 0.7,
                EnergyType.SPIRITUAL: 0.8,
                EnergyType.PRACTICAL: 0.6
            },
            EnergyType.ANALYTICAL: {
                EnergyType.CREATIVE: 0.6,
                EnergyType.ANALYTICAL: 1.0,
                EnergyType.SOCIAL: 0.5,
                EnergyType.LEADERSHIP: 0.6,
                EnergyType.TECHNICAL: 0.9,
                EnergyType.EMOTIONAL: 0.4,
                EnergyType.PHYSICAL: 0.3,
                EnergyType.MENTAL: 0.9,
                EnergyType.SPIRITUAL: 0.5,
                EnergyType.PRACTICAL: 0.8
            },
            EnergyType.SOCIAL: {
                EnergyType.CREATIVE: 0.8,
                EnergyType.ANALYTICAL: 0.5,
                EnergyType.SOCIAL: 1.0,
                EnergyType.LEADERSHIP: 0.9,
                EnergyType.TECHNICAL: 0.4,
                EnergyType.EMOTIONAL: 0.8,
                EnergyType.PHYSICAL: 0.6,
                EnergyType.MENTAL: 0.5,
                EnergyType.SPIRITUAL: 0.7,
                EnergyType.PRACTICAL: 0.6
            },
            EnergyType.LEADERSHIP: {
                EnergyType.CREATIVE: 0.7,
                EnergyType.ANALYTICAL: 0.6,
                EnergyType.SOCIAL: 0.9,
                EnergyType.LEADERSHIP: 1.0,
                EnergyType.TECHNICAL: 0.5,
                EnergyType.EMOTIONAL: 0.7,
                EnergyType.PHYSICAL: 0.6,
                EnergyType.MENTAL: 0.7,
                EnergyType.SPIRITUAL: 0.8,
                EnergyType.PRACTICAL: 0.7
            },
            EnergyType.TECHNICAL: {
                EnergyType.CREATIVE: 0.5,
                EnergyType.ANALYTICAL: 0.9,
                EnergyType.SOCIAL: 0.4,
                EnergyType.LEADERSHIP: 0.5,
                EnergyType.TECHNICAL: 1.0,
                EnergyType.EMOTIONAL: 0.3,
                EnergyType.PHYSICAL: 0.4,
                EnergyType.MENTAL: 0.8,
                EnergyType.SPIRITUAL: 0.4,
                EnergyType.PRACTICAL: 0.9
            }
        }
        
        # Obtener compatibilidad de la matriz
        if person_energy in compatibility_matrix and vacancy_energy in compatibility_matrix[person_energy]:
            return compatibility_matrix[person_energy][vacancy_energy]
        else:
            return 0.5  # Compatibilidad neutral por defecto
    
    def _calculate_energy_level_compatibility(
        self,
        person_level: EnergyLevel,
        vacancy_level: EnergyLevel
    ) -> float:
        """Calcula compatibilidad de niveles de energía."""
        # Matriz de compatibilidad de niveles
        level_compatibility = {
            EnergyLevel.LOW: {
                EnergyLevel.LOW: 1.0,
                EnergyLevel.MEDIUM: 0.7,
                EnergyLevel.HIGH: 0.4,
                EnergyLevel.VARIABLE: 0.6
            },
            EnergyLevel.MEDIUM: {
                EnergyLevel.LOW: 0.7,
                EnergyLevel.MEDIUM: 1.0,
                EnergyLevel.HIGH: 0.8,
                EnergyLevel.VARIABLE: 0.9
            },
            EnergyLevel.HIGH: {
                EnergyLevel.LOW: 0.4,
                EnergyLevel.MEDIUM: 0.8,
                EnergyLevel.HIGH: 1.0,
                EnergyLevel.VARIABLE: 0.8
            },
            EnergyLevel.VARIABLE: {
                EnergyLevel.LOW: 0.6,
                EnergyLevel.MEDIUM: 0.9,
                EnergyLevel.HIGH: 0.8,
                EnergyLevel.VARIABLE: 1.0
            }
        }
        
        return level_compatibility.get(person_level, {}).get(vacancy_level, 0.5)
    
    async def _adjust_energy_score(
        self,
        base_score: float,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> float:
        """Ajusta el score energético basado en factores contextuales."""
        adjusted_score = base_score
        
        # Ajustar por adaptabilidad
        adaptability = person_data.get('adaptability', 0)
        if adaptability > 80:
            adjusted_score += 5
        elif adaptability < 40:
            adjusted_score -= 5
        
        # Ajustar por estrés del trabajo
        stress_level = vacancy_data.get('stress_level', 0)
        stress_management = person_data.get('stress_management', '')
        
        if stress_level > 70 and 'mindfulness' in stress_management.lower():
            adjusted_score += 3
        elif stress_level > 70 and not stress_management:
            adjusted_score -= 5
        
        # Ajustar por trabajo remoto
        remote_work = vacancy_data.get('remote_work', False)
        work_style = person_data.get('work_style', '')
        
        if remote_work and 'independent' in work_style.lower():
            adjusted_score += 3
        elif not remote_work and 'collaborative' in work_style.lower():
            adjusted_score += 3
        
        return max(0.0, min(100.0, adjusted_score))
    
    def _determine_work_type(self, vacancy_data: Dict[str, Any]) -> str:
        """Determina el tipo de trabajo de la vacante."""
        title = vacancy_data.get('title', '').lower()
        description = vacancy_data.get('description', '').lower()
        
        # Palabras clave para cada tipo
        creative_keywords = ['design', 'creative', 'art', 'content', 'brand', 'marketing']
        technical_keywords = ['developer', 'engineer', 'technical', 'software', 'data', 'analyst']
        leadership_keywords = ['manager', 'director', 'lead', 'head', 'chief', 'supervisor']
        collaborative_keywords = ['coordinator', 'facilitator', 'team', 'collaboration']
        analytical_keywords = ['analyst', 'researcher', 'scientist', 'consultant']
        
        if any(keyword in title or keyword in description for keyword in creative_keywords):
            return 'creative'
        elif any(keyword in title or keyword in description for keyword in technical_keywords):
            return 'technical'
        elif any(keyword in title or keyword in description for keyword in leadership_keywords):
            return 'leadership'
        elif any(keyword in title or keyword in description for keyword in collaborative_keywords):
            return 'collaborative'
        elif any(keyword in title or keyword in description for keyword in analytical_keywords):
            return 'analytical'
        else:
            return 'general'
    
    def _analyze_team_energy_requirements(self, vacancy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza los requisitos energéticos del equipo."""
        team_size = vacancy_data.get('team_size', 0)
        
        if team_size > 10:
            return {'energy_type': 'collaborative', 'intensity': 'high'}
        elif team_size > 5:
            return {'energy_type': 'collaborative', 'intensity': 'medium'}
        else:
            return {'energy_type': 'flexible', 'intensity': 'variable'}
    
    def _analyze_stress_factors(self, vacancy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza los factores de estrés de la vacante."""
        stress_level = vacancy_data.get('stress_level', 0)
        travel_requirements = vacancy_data.get('travel_requirements', 0)
        
        return {
            'overall_stress': stress_level,
            'travel_stress': travel_requirements,
            'work_life_balance': vacancy_data.get('work_life_balance', 'moderate')
        }
    
    def _analyze_growth_energy_requirements(self, vacancy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza los requisitos energéticos de crecimiento."""
        growth_opportunities = vacancy_data.get('growth_opportunities', [])
        mentoring_available = vacancy_data.get('mentoring_available', False)
        
        return {
            'growth_energy': 'high' if growth_opportunities else 'low',
            'mentoring_energy': 'high' if mentoring_available else 'low',
            'learning_energy': 'medium'
        }
    
    def _calculate_energy_stability(self, energy_profile: EnergyProfile) -> float:
        """Calcula la estabilidad energética."""
        # Implementación básica
        return 75.0
    
    def _analyze_stress_resilience(self, person_data: Dict[str, Any]) -> float:
        """Analiza la resiliencia al estrés."""
        resilience = person_data.get('resilience', 0)
        stress_management = person_data.get('stress_management', '')
        
        base_resilience = resilience
        
        # Ajustar por técnicas de manejo del estrés
        if stress_management:
            base_resilience += 10
        
        return min(100.0, base_resilience)
    
    def _analyze_energy_consistency(self, energy_profile: EnergyProfile) -> float:
        """Analiza la consistencia energética."""
        # Implementación básica
        return 80.0
    
    def _analyze_recovery_patterns(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza los patrones de recuperación energética."""
        return {
            'recovery_speed': 'medium',
            'recovery_methods': ['rest', 'exercise', 'social'],
            'recovery_efficiency': 0.7
        }
    
    def _analyze_energy_adaptability(self, person_data: Dict[str, Any]) -> float:
        """Analiza la adaptabilidad energética."""
        adaptability = person_data.get('adaptability', 0)
        work_style = person_data.get('work_style', '')
        
        base_adaptability = adaptability
        
        # Ajustar por estilo de trabajo
        if 'flexible' in work_style.lower():
            base_adaptability += 10
        elif 'rigid' in work_style.lower():
            base_adaptability -= 10
        
        return max(0.0, min(100.0, base_adaptability))
    
    def _create_default_energy_profile(self) -> EnergyProfile:
        """Crea un perfil energético por defecto."""
        return EnergyProfile(
            primary_energy=EnergyType.PRACTICAL,
            secondary_energy=EnergyType.SOCIAL,
            energy_level=EnergyLevel.MEDIUM,
            energy_patterns={},
            compatibility_factors={},
            timestamp=datetime.now()
        ) 