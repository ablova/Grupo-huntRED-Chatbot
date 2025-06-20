"""
Matcher Vibracional del Sistema Aura

Este módulo implementa el análisis de alineación vibracional y resonancia
entre candidatos y entornos de trabajo.
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

class VibrationalFrequency(Enum):
    """Frecuencias vibracionales identificadas."""
    ALPHA = "alpha"  # 8-13 Hz - Relajación, creatividad
    BETA = "beta"    # 13-30 Hz - Concentración, alerta
    THETA = "theta"  # 4-8 Hz - Meditación, intuición
    DELTA = "delta"  # 0.5-4 Hz - Sueño profundo, regeneración
    GAMMA = "gamma"  # 30-100 Hz - Procesamiento cognitivo superior

class ResonanceType(Enum):
    """Tipos de resonancia vibracional."""
    HARMONIC = "harmonic"      # Resonancia perfecta
    COMPLEMENTARY = "complementary"  # Resonancia complementaria
    NEUTRAL = "neutral"        # Sin resonancia específica
    DISSONANT = "dissonant"    # Resonancia conflictiva

@dataclass
class VibrationalProfile:
    """Perfil vibracional de una persona o entorno."""
    primary_frequency: VibrationalFrequency
    secondary_frequency: VibrationalFrequency
    resonance_patterns: Dict[str, float]
    stability_index: float
    adaptability_score: float
    harmonic_balance: float
    timestamp: datetime

class VibrationalMatcher:
    """
    Matcher de alineación vibracional y resonancia.
    
    Analiza las frecuencias vibracionales de personas y entornos,
    determinando la calidad de la resonancia y alineación.
    """
    
    def __init__(self):
        """Inicializa el matcher vibracional."""
        self.frequency_characteristics = {
            VibrationalFrequency.ALPHA: {
                'description': 'Relajación y creatividad',
                'work_style': 'creativo',
                'stress_level': 'bajo',
                'collaboration': 'alta',
                'innovation': 'alta'
            },
            VibrationalFrequency.BETA: {
                'description': 'Concentración y alerta',
                'work_style': 'analítico',
                'stress_level': 'medio',
                'collaboration': 'media',
                'innovation': 'media'
            },
            VibrationalFrequency.THETA: {
                'description': 'Meditación e intuición',
                'work_style': 'intuitivo',
                'stress_level': 'muy bajo',
                'collaboration': 'variable',
                'innovation': 'alta'
            },
            VibrationalFrequency.DELTA: {
                'description': 'Regeneración profunda',
                'work_style': 'contemplativo',
                'stress_level': 'mínimo',
                'collaboration': 'baja',
                'innovation': 'variable'
            },
            VibrationalFrequency.GAMMA: {
                'description': 'Procesamiento cognitivo superior',
                'work_style': 'estratégico',
                'stress_level': 'alto',
                'collaboration': 'alta',
                'innovation': 'muy alta'
            }
        }
        
        # Matriz de resonancia entre frecuencias
        self.resonance_matrix = {
            VibrationalFrequency.ALPHA: {
                VibrationalFrequency.ALPHA: 1.0,
                VibrationalFrequency.BETA: 0.7,
                VibrationalFrequency.THETA: 0.9,
                VibrationalFrequency.DELTA: 0.6,
                VibrationalFrequency.GAMMA: 0.5
            },
            VibrationalFrequency.BETA: {
                VibrationalFrequency.ALPHA: 0.7,
                VibrationalFrequency.BETA: 1.0,
                VibrationalFrequency.THETA: 0.6,
                VibrationalFrequency.DELTA: 0.4,
                VibrationalFrequency.GAMMA: 0.8
            },
            VibrationalFrequency.THETA: {
                VibrationalFrequency.ALPHA: 0.9,
                VibrationalFrequency.BETA: 0.6,
                VibrationalFrequency.THETA: 1.0,
                VibrationalFrequency.DELTA: 0.8,
                VibrationalFrequency.GAMMA: 0.4
            },
            VibrationalFrequency.DELTA: {
                VibrationalFrequency.ALPHA: 0.6,
                VibrationalFrequency.BETA: 0.4,
                VibrationalFrequency.THETA: 0.8,
                VibrationalFrequency.DELTA: 1.0,
                VibrationalFrequency.GAMMA: 0.3
            },
            VibrationalFrequency.GAMMA: {
                VibrationalFrequency.ALPHA: 0.5,
                VibrationalFrequency.BETA: 0.8,
                VibrationalFrequency.THETA: 0.4,
                VibrationalFrequency.DELTA: 0.3,
                VibrationalFrequency.GAMMA: 1.0
            }
        }
        
        logger.info("Matcher vibracional inicializado")
    
    async def analyze_vibrational_alignment(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> float:
        """
        Analiza la alineación vibracional entre persona y vacante.
        
        Args:
            person_data: Datos de la persona
            vacancy_data: Datos de la vacante
            
        Returns:
            Score de alineación vibracional (0-100)
        """
        try:
            # Extraer perfiles vibracionales
            person_vibration = await self.extract_vibrational_signature(person_data)
            vacancy_vibration = await self.extract_vacancy_vibrational_signature(vacancy_data)
            
            # Calcular alineación
            alignment_score = await self._calculate_vibrational_alignment(
                person_vibration, vacancy_vibration
            )
            
            # Ajustar por factores contextuales
            adjusted_score = await self._adjust_vibrational_score(
                alignment_score, person_data, vacancy_data
            )
            
            return adjusted_score
            
        except Exception as e:
            logger.error(f"Error en análisis de alineación vibracional: {str(e)}")
            return 0.0
    
    async def extract_vibrational_signature(self, person_data: Dict[str, Any]) -> VibrationalProfile:
        """
        Extrae la firma vibracional de una persona.
        
        Args:
            person_data: Datos de la persona
            
        Returns:
            Perfil vibracional de la persona
        """
        try:
            # Analizar diferentes aspectos vibracionales
            personality_vibration = await self._analyze_personality_vibration(person_data)
            work_style_vibration = await self._analyze_work_style_vibration(person_data)
            stress_vibration = await self._analyze_stress_vibration(person_data)
            creativity_vibration = await self._analyze_creativity_vibration(person_data)
            social_vibration = await self._analyze_social_vibration(person_data)
            
            # Combinar patrones vibracionales
            combined_patterns = {
                'personality': personality_vibration,
                'work_style': work_style_vibration,
                'stress_response': stress_vibration,
                'creativity': creativity_vibration,
                'social': social_vibration
            }
            
            # Determinar frecuencias primaria y secundaria
            primary_frequency = self._determine_primary_frequency(combined_patterns)
            secondary_frequency = self._determine_secondary_frequency(combined_patterns, primary_frequency)
            
            # Calcular índices vibracionales
            stability_index = self._calculate_vibrational_stability(combined_patterns)
            adaptability_score = self._calculate_vibrational_adaptability(person_data)
            harmonic_balance = self._calculate_harmonic_balance(combined_patterns)
            
            return VibrationalProfile(
                primary_frequency=primary_frequency,
                secondary_frequency=secondary_frequency,
                resonance_patterns=combined_patterns,
                stability_index=stability_index,
                adaptability_score=adaptability_score,
                harmonic_balance=harmonic_balance,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error extrayendo firma vibracional: {str(e)}")
            return self._create_default_vibrational_profile()
    
    async def extract_vacancy_vibrational_signature(self, vacancy_data: Dict[str, Any]) -> VibrationalProfile:
        """
        Extrae la firma vibracional de una vacante.
        
        Args:
            vacancy_data: Datos de la vacante
            
        Returns:
            Perfil vibracional de la vacante
        """
        try:
            # Determinar tipo de trabajo
            work_type = self._determine_vacancy_work_type(vacancy_data)
            
            # Mapear tipo de trabajo a frecuencia vibracional
            frequency_mapping = {
                'creative': VibrationalFrequency.ALPHA,
                'analytical': VibrationalFrequency.BETA,
                'intuitive': VibrationalFrequency.THETA,
                'strategic': VibrationalFrequency.GAMMA,
                'collaborative': VibrationalFrequency.ALPHA,
                'technical': VibrationalFrequency.BETA,
                'leadership': VibrationalFrequency.GAMMA,
                'research': VibrationalFrequency.THETA
            }
            
            primary_frequency = frequency_mapping.get(work_type, VibrationalFrequency.BETA)
            secondary_frequency = self._determine_vacancy_secondary_frequency(vacancy_data, primary_frequency)
            
            # Analizar patrones vibracionales del entorno
            environment_patterns = {
                'work_environment': self._analyze_work_environment_vibration(vacancy_data),
                'team_dynamics': self._analyze_team_vibration(vacancy_data),
                'stress_level': self._analyze_stress_vibration_environment(vacancy_data),
                'innovation_focus': self._analyze_innovation_vibration(vacancy_data)
            }
            
            # Calcular índices vibracionales del entorno
            stability_index = self._calculate_environment_stability(vacancy_data)
            adaptability_score = self._calculate_environment_adaptability(vacancy_data)
            harmonic_balance = self._calculate_environment_harmonic_balance(environment_patterns)
            
            return VibrationalProfile(
                primary_frequency=primary_frequency,
                secondary_frequency=secondary_frequency,
                resonance_patterns=environment_patterns,
                stability_index=stability_index,
                adaptability_score=adaptability_score,
                harmonic_balance=harmonic_balance,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error extrayendo firma vibracional de vacante: {str(e)}")
            return self._create_default_vibrational_profile()
    
    async def analyze_vibrational_resonance(
        self,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analiza la resonancia vibracional entre persona y vacante.
        
        Args:
            person_data: Datos de la persona
            vacancy_data: Datos de la vacante
            
        Returns:
            Análisis detallado de resonancia vibracional
        """
        try:
            person_vibration = await self.extract_vibrational_signature(person_data)
            vacancy_vibration = await self.extract_vacancy_vibrational_signature(vacancy_data)
            
            # Calcular resonancia
            resonance_score = self._calculate_resonance_score(person_vibration, vacancy_vibration)
            resonance_type = self._determine_resonance_type(resonance_score)
            
            # Análisis detallado
            resonance_analysis = {
                'overall_resonance': resonance_score,
                'resonance_type': resonance_type.value,
                'primary_frequency_match': self._calculate_frequency_match(
                    person_vibration.primary_frequency,
                    vacancy_vibration.primary_frequency
                ),
                'secondary_frequency_match': self._calculate_frequency_match(
                    person_vibration.secondary_frequency,
                    vacancy_vibration.secondary_frequency
                ),
                'stability_compatibility': self._calculate_stability_compatibility(
                    person_vibration.stability_index,
                    vacancy_vibration.stability_index
                ),
                'adaptability_synergy': self._calculate_adaptability_synergy(
                    person_vibration.adaptability_score,
                    vacancy_vibration.adaptability_score
                ),
                'harmonic_alignment': self._calculate_harmonic_alignment(
                    person_vibration.harmonic_balance,
                    vacancy_vibration.harmonic_balance
                ),
                'resonance_insights': self._generate_resonance_insights(
                    person_vibration, vacancy_vibration, resonance_score
                ),
                'recommendations': self._generate_resonance_recommendations(
                    person_vibration, vacancy_vibration, resonance_score
                )
            }
            
            return resonance_analysis
            
        except Exception as e:
            logger.error(f"Error analizando resonancia vibracional: {str(e)}")
            return {'error': str(e)}
    
    async def _analyze_personality_vibration(self, person_data: Dict[str, Any]) -> Dict[str, float]:
        """Analiza la vibración de personalidad."""
        personality_traits = person_data.get('personality_traits', {})
        
        vibration_scores = {
            'alpha': 0.0,
            'beta': 0.0,
            'theta': 0.0,
            'delta': 0.0,
            'gamma': 0.0
        }
        
        # Mapear rasgos de personalidad a frecuencias
        if personality_traits.get('openness', 0) > 70:
            vibration_scores['alpha'] += 0.3
            vibration_scores['theta'] += 0.2
        
        if personality_traits.get('conscientiousness', 0) > 70:
            vibration_scores['beta'] += 0.3
            vibration_scores['gamma'] += 0.2
        
        if personality_traits.get('extraversion', 0) > 70:
            vibration_scores['alpha'] += 0.2
            vibration_scores['gamma'] += 0.3
        
        if personality_traits.get('neuroticism', 0) > 70:
            vibration_scores['beta'] += 0.2
            vibration_scores['delta'] += 0.3
        
        if personality_traits.get('agreeableness', 0) > 70:
            vibration_scores['alpha'] += 0.2
            vibration_scores['theta'] += 0.2
        
        return vibration_scores
    
    async def _analyze_work_style_vibration(self, person_data: Dict[str, Any]) -> Dict[str, float]:
        """Analiza la vibración del estilo de trabajo."""
        work_style = person_data.get('work_style', '')
        
        vibration_scores = {
            'alpha': 0.0,
            'beta': 0.0,
            'theta': 0.0,
            'delta': 0.0,
            'gamma': 0.0
        }
        
        # Mapear estilos de trabajo a frecuencias
        if 'creative' in work_style.lower():
            vibration_scores['alpha'] += 0.4
            vibration_scores['theta'] += 0.2
        
        if 'analytical' in work_style.lower():
            vibration_scores['beta'] += 0.4
            vibration_scores['gamma'] += 0.2
        
        if 'collaborative' in work_style.lower():
            vibration_scores['alpha'] += 0.3
            vibration_scores['gamma'] += 0.2
        
        if 'independent' in work_style.lower():
            vibration_scores['theta'] += 0.3
            vibration_scores['delta'] += 0.2
        
        if 'structured' in work_style.lower():
            vibration_scores['beta'] += 0.3
            vibration_scores['gamma'] += 0.2
        
        return vibration_scores
    
    async def _analyze_stress_vibration(self, person_data: Dict[str, Any]) -> Dict[str, float]:
        """Analiza la vibración de respuesta al estrés."""
        stress_management = person_data.get('stress_management', '')
        resilience = person_data.get('resilience', 0)
        
        vibration_scores = {
            'alpha': 0.0,
            'beta': 0.0,
            'theta': 0.0,
            'delta': 0.0,
            'gamma': 0.0
        }
        
        # Mapear manejo del estrés a frecuencias
        if 'mindfulness' in stress_management.lower():
            vibration_scores['theta'] += 0.4
            vibration_scores['alpha'] += 0.2
        
        if 'exercise' in stress_management.lower():
            vibration_scores['beta'] += 0.3
            vibration_scores['gamma'] += 0.2
        
        if 'meditation' in stress_management.lower():
            vibration_scores['theta'] += 0.4
            vibration_scores['delta'] += 0.2
        
        # Ajustar por resiliencia
        if resilience > 80:
            vibration_scores['alpha'] += 0.2
            vibration_scores['gamma'] += 0.2
        
        return vibration_scores
    
    async def _analyze_creativity_vibration(self, person_data: Dict[str, Any]) -> Dict[str, float]:
        """Analiza la vibración de creatividad."""
        creativity = person_data.get('creativity', 0)
        innovation_capacity = person_data.get('innovation_capacity', 0)
        
        vibration_scores = {
            'alpha': 0.0,
            'beta': 0.0,
            'theta': 0.0,
            'delta': 0.0,
            'gamma': 0.0
        }
        
        # Mapear creatividad a frecuencias
        if creativity > 70:
            vibration_scores['alpha'] += 0.3
            vibration_scores['theta'] += 0.3
        
        if innovation_capacity > 70:
            vibration_scores['gamma'] += 0.4
            vibration_scores['alpha'] += 0.2
        
        return vibration_scores
    
    async def _analyze_social_vibration(self, person_data: Dict[str, Any]) -> Dict[str, float]:
        """Analiza la vibración social."""
        communication_style = person_data.get('communication_style', '')
        collaboration = person_data.get('collaboration', 0)
        
        vibration_scores = {
            'alpha': 0.0,
            'beta': 0.0,
            'theta': 0.0,
            'delta': 0.0,
            'gamma': 0.0
        }
        
        # Mapear aspectos sociales a frecuencias
        if collaboration > 70:
            vibration_scores['alpha'] += 0.3
            vibration_scores['gamma'] += 0.2
        
        if 'empathetic' in communication_style.lower():
            vibration_scores['alpha'] += 0.3
            vibration_scores['theta'] += 0.2
        
        if 'inspirational' in communication_style.lower():
            vibration_scores['gamma'] += 0.4
            vibration_scores['alpha'] += 0.2
        
        return vibration_scores
    
    def _determine_primary_frequency(self, vibration_patterns: Dict[str, Dict[str, float]]) -> VibrationalFrequency:
        """Determina la frecuencia primaria basada en los patrones."""
        # Combinar todos los patrones vibracionales
        combined_vibration = {}
        
        for pattern_type, pattern_scores in vibration_patterns.items():
            for frequency_name, score in pattern_scores.items():
                if frequency_name not in combined_vibration:
                    combined_vibration[frequency_name] = 0.0
                combined_vibration[frequency_name] += score
        
        # Encontrar la frecuencia con mayor score
        if combined_vibration:
            primary_frequency_name = max(combined_vibration, key=combined_vibration.get)
            return VibrationalFrequency(primary_frequency_name)
        else:
            return VibrationalFrequency.BETA
    
    def _determine_secondary_frequency(
        self,
        vibration_patterns: Dict[str, Dict[str, float]],
        primary_frequency: VibrationalFrequency
    ) -> VibrationalFrequency:
        """Determina la frecuencia secundaria."""
        # Combinar patrones vibracionales excluyendo la primaria
        combined_vibration = {}
        
        for pattern_type, pattern_scores in vibration_patterns.items():
            for frequency_name, score in pattern_scores.items():
                if frequency_name != primary_frequency.value:
                    if frequency_name not in combined_vibration:
                        combined_vibration[frequency_name] = 0.0
                    combined_vibration[frequency_name] += score
        
        # Encontrar la frecuencia secundaria con mayor score
        if combined_vibration:
            secondary_frequency_name = max(combined_vibration, key=combined_vibration.get)
            return VibrationalFrequency(secondary_frequency_name)
        else:
            return VibrationalFrequency.ALPHA
    
    def _calculate_vibrational_stability(self, vibration_patterns: Dict[str, Dict[str, float]]) -> float:
        """Calcula la estabilidad vibracional."""
        # Implementación básica
        return 75.0
    
    def _calculate_vibrational_adaptability(self, person_data: Dict[str, Any]) -> float:
        """Calcula la adaptabilidad vibracional."""
        adaptability = person_data.get('adaptability', 0)
        work_style = person_data.get('work_style', '')
        
        base_adaptability = adaptability
        
        # Ajustar por estilo de trabajo
        if 'flexible' in work_style.lower():
            base_adaptability += 10
        elif 'rigid' in work_style.lower():
            base_adaptability -= 10
        
        return max(0.0, min(100.0, base_adaptability))
    
    def _calculate_harmonic_balance(self, vibration_patterns: Dict[str, Dict[str, float]]) -> float:
        """Calcula el balance armónico vibracional."""
        # Implementación básica
        return 80.0
    
    async def _calculate_vibrational_alignment(
        self,
        person_vibration: VibrationalProfile,
        vacancy_vibration: VibrationalProfile
    ) -> float:
        """Calcula la alineación vibracional entre persona y vacante."""
        try:
            # Alineación de frecuencia primaria
            primary_alignment = self._calculate_frequency_alignment(
                person_vibration.primary_frequency,
                vacancy_vibration.primary_frequency
            )
            
            # Alineación de frecuencia secundaria
            secondary_alignment = self._calculate_frequency_alignment(
                person_vibration.secondary_frequency,
                vacancy_vibration.secondary_frequency
            )
            
            # Alineación de estabilidad
            stability_alignment = self._calculate_stability_alignment(
                person_vibration.stability_index,
                vacancy_vibration.stability_index
            )
            
            # Alineación de adaptabilidad
            adaptability_alignment = self._calculate_adaptability_alignment(
                person_vibration.adaptability_score,
                vacancy_vibration.adaptability_score
            )
            
            # Calcular score final ponderado
            final_score = (
                primary_alignment * 0.4 +
                secondary_alignment * 0.3 +
                stability_alignment * 0.2 +
                adaptability_alignment * 0.1
            )
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculando alineación vibracional: {str(e)}")
            return 0.0
    
    def _calculate_frequency_alignment(
        self,
        person_frequency: VibrationalFrequency,
        vacancy_frequency: VibrationalFrequency
    ) -> float:
        """Calcula la alineación entre frecuencias."""
        # Obtener resonancia de la matriz
        if person_frequency in self.resonance_matrix and vacancy_frequency in self.resonance_matrix[person_frequency]:
            resonance = self.resonance_matrix[person_frequency][vacancy_frequency]
            return resonance * 100  # Convertir a escala 0-100
        else:
            return 50.0  # Alineación neutral por defecto
    
    def _calculate_stability_alignment(self, person_stability: float, vacancy_stability: float) -> float:
        """Calcula la alineación de estabilidad."""
        # Calcular diferencia de estabilidad
        stability_diff = abs(person_stability - vacancy_stability)
        
        # Menor diferencia = mayor alineación
        if stability_diff < 10:
            return 90.0
        elif stability_diff < 20:
            return 75.0
        elif stability_diff < 30:
            return 60.0
        else:
            return 40.0
    
    def _calculate_adaptability_alignment(self, person_adaptability: float, vacancy_adaptability: float) -> float:
        """Calcula la alineación de adaptabilidad."""
        # Ambos altos = buena alineación
        if person_adaptability > 80 and vacancy_adaptability > 80:
            return 90.0
        # Ambos bajos = alineación moderada
        elif person_adaptability < 40 and vacancy_adaptability < 40:
            return 70.0
        # Uno alto, uno bajo = alineación variable
        else:
            return 60.0
    
    async def _adjust_vibrational_score(
        self,
        base_score: float,
        person_data: Dict[str, Any],
        vacancy_data: Dict[str, Any]
    ) -> float:
        """Ajusta el score vibracional basado en factores contextuales."""
        adjusted_score = base_score
        
        # Ajustar por compatibilidad de trabajo remoto
        remote_work = vacancy_data.get('remote_work', False)
        work_style = person_data.get('work_style', '')
        
        if remote_work and 'independent' in work_style.lower():
            adjusted_score += 5
        elif not remote_work and 'collaborative' in work_style.lower():
            adjusted_score += 5
        
        # Ajustar por nivel de estrés
        stress_level = vacancy_data.get('stress_level', 0)
        stress_management = person_data.get('stress_management', '')
        
        if stress_level > 70 and stress_management:
            adjusted_score += 3
        elif stress_level > 70 and not stress_management:
            adjusted_score -= 5
        
        return max(0.0, min(100.0, adjusted_score))
    
    def _determine_vacancy_work_type(self, vacancy_data: Dict[str, Any]) -> str:
        """Determina el tipo de trabajo de la vacante."""
        title = vacancy_data.get('title', '').lower()
        description = vacancy_data.get('description', '').lower()
        
        # Palabras clave para cada tipo
        creative_keywords = ['design', 'creative', 'art', 'content', 'brand', 'marketing']
        analytical_keywords = ['analyst', 'researcher', 'scientist', 'consultant']
        strategic_keywords = ['strategist', 'planner', 'director', 'manager']
        collaborative_keywords = ['coordinator', 'facilitator', 'team', 'collaboration']
        technical_keywords = ['developer', 'engineer', 'technical', 'software']
        leadership_keywords = ['leader', 'head', 'chief', 'supervisor']
        research_keywords = ['research', 'investigation', 'study', 'analysis']
        
        if any(keyword in title or keyword in description for keyword in creative_keywords):
            return 'creative'
        elif any(keyword in title or keyword in description for keyword in analytical_keywords):
            return 'analytical'
        elif any(keyword in title or keyword in description for keyword in strategic_keywords):
            return 'strategic'
        elif any(keyword in title or keyword in description for keyword in collaborative_keywords):
            return 'collaborative'
        elif any(keyword in title or keyword in description for keyword in technical_keywords):
            return 'technical'
        elif any(keyword in title or keyword in description for keyword in leadership_keywords):
            return 'leadership'
        elif any(keyword in title or keyword in description for keyword in research_keywords):
            return 'research'
        else:
            return 'general'
    
    def _determine_vacancy_secondary_frequency(
        self,
        vacancy_data: Dict[str, Any],
        primary_frequency: VibrationalFrequency
    ) -> VibrationalFrequency:
        """Determina la frecuencia secundaria de la vacante."""
        # Lógica básica para determinar frecuencia secundaria
        if primary_frequency == VibrationalFrequency.ALPHA:
            return VibrationalFrequency.THETA
        elif primary_frequency == VibrationalFrequency.BETA:
            return VibrationalFrequency.GAMMA
        elif primary_frequency == VibrationalFrequency.THETA:
            return VibrationalFrequency.ALPHA
        elif primary_frequency == VibrationalFrequency.DELTA:
            return VibrationalFrequency.THETA
        elif primary_frequency == VibrationalFrequency.GAMMA:
            return VibrationalFrequency.BETA
        else:
            return VibrationalFrequency.ALPHA
    
    def _analyze_work_environment_vibration(self, vacancy_data: Dict[str, Any]) -> Dict[str, float]:
        """Analiza la vibración del entorno de trabajo."""
        work_environment = vacancy_data.get('work_environment', '')
        
        vibration_scores = {
            'alpha': 0.0,
            'beta': 0.0,
            'theta': 0.0,
            'delta': 0.0,
            'gamma': 0.0
        }
        
        # Mapear entorno de trabajo a frecuencias
        if 'creative' in work_environment.lower():
            vibration_scores['alpha'] += 0.4
            vibration_scores['theta'] += 0.2
        
        if 'structured' in work_environment.lower():
            vibration_scores['beta'] += 0.4
            vibration_scores['gamma'] += 0.2
        
        if 'collaborative' in work_environment.lower():
            vibration_scores['alpha'] += 0.3
            vibration_scores['gamma'] += 0.2
        
        return vibration_scores
    
    def _analyze_team_vibration(self, vacancy_data: Dict[str, Any]) -> Dict[str, float]:
        """Analiza la vibración del equipo."""
        team_size = vacancy_data.get('team_size', 0)
        
        vibration_scores = {
            'alpha': 0.0,
            'beta': 0.0,
            'theta': 0.0,
            'delta': 0.0,
            'gamma': 0.0
        }
        
        if team_size > 10:
            vibration_scores['gamma'] += 0.4
            vibration_scores['alpha'] += 0.2
        elif team_size > 5:
            vibration_scores['alpha'] += 0.3
            vibration_scores['beta'] += 0.2
        else:
            vibration_scores['theta'] += 0.3
            vibration_scores['beta'] += 0.2
        
        return vibration_scores
    
    def _analyze_stress_vibration_environment(self, vacancy_data: Dict[str, Any]) -> Dict[str, float]:
        """Analiza la vibración del estrés en el entorno."""
        stress_level = vacancy_data.get('stress_level', 0)
        
        vibration_scores = {
            'alpha': 0.0,
            'beta': 0.0,
            'theta': 0.0,
            'delta': 0.0,
            'gamma': 0.0
        }
        
        if stress_level > 70:
            vibration_scores['beta'] += 0.4
            vibration_scores['gamma'] += 0.3
        elif stress_level > 40:
            vibration_scores['beta'] += 0.3
            vibration_scores['alpha'] += 0.2
        else:
            vibration_scores['alpha'] += 0.3
            vibration_scores['theta'] += 0.2
        
        return vibration_scores
    
    def _analyze_innovation_vibration(self, vacancy_data: Dict[str, Any]) -> Dict[str, float]:
        """Analiza la vibración de innovación."""
        innovation_focus = vacancy_data.get('innovation_focus', 0)
        
        vibration_scores = {
            'alpha': 0.0,
            'beta': 0.0,
            'theta': 0.0,
            'delta': 0.0,
            'gamma': 0.0
        }
        
        if innovation_focus > 70:
            vibration_scores['gamma'] += 0.4
            vibration_scores['alpha'] += 0.3
        elif innovation_focus > 40:
            vibration_scores['alpha'] += 0.3
            vibration_scores['theta'] += 0.2
        else:
            vibration_scores['beta'] += 0.3
            vibration_scores['delta'] += 0.2
        
        return vibration_scores
    
    def _calculate_environment_stability(self, vacancy_data: Dict[str, Any]) -> float:
        """Calcula la estabilidad del entorno."""
        # Implementación básica
        return 70.0
    
    def _calculate_environment_adaptability(self, vacancy_data: Dict[str, Any]) -> float:
        """Calcula la adaptabilidad del entorno."""
        # Implementación básica
        return 65.0
    
    def _calculate_environment_harmonic_balance(self, environment_patterns: Dict[str, Dict[str, float]]) -> float:
        """Calcula el balance armónico del entorno."""
        # Implementación básica
        return 75.0
    
    def _calculate_resonance_score(
        self,
        person_vibration: VibrationalProfile,
        vacancy_vibration: VibrationalProfile
    ) -> float:
        """Calcula el score de resonancia entre perfiles vibracionales."""
        # Resonancia de frecuencias primarias
        primary_resonance = self.resonance_matrix.get(
            person_vibration.primary_frequency, {}
        ).get(vacancy_vibration.primary_frequency, 0.5)
        
        # Resonancia de frecuencias secundarias
        secondary_resonance = self.resonance_matrix.get(
            person_vibration.secondary_frequency, {}
        ).get(vacancy_vibration.secondary_frequency, 0.5)
        
        # Resonancia de estabilidad
        stability_resonance = 1.0 - abs(
            person_vibration.stability_index - vacancy_vibration.stability_index
        ) / 100.0
        
        # Score final ponderado
        final_score = (
            primary_resonance * 0.4 +
            secondary_resonance * 0.3 +
            stability_resonance * 0.3
        ) * 100
        
        return final_score
    
    def _determine_resonance_type(self, resonance_score: float) -> ResonanceType:
        """Determina el tipo de resonancia basado en el score."""
        if resonance_score >= 85:
            return ResonanceType.HARMONIC
        elif resonance_score >= 70:
            return ResonanceType.COMPLEMENTARY
        elif resonance_score >= 50:
            return ResonanceType.NEUTRAL
        else:
            return ResonanceType.DISSONANT
    
    def _calculate_frequency_match(
        self,
        person_frequency: VibrationalFrequency,
        vacancy_frequency: VibrationalFrequency
    ) -> float:
        """Calcula el match de frecuencias."""
        return self.resonance_matrix.get(person_frequency, {}).get(vacancy_frequency, 0.5) * 100
    
    def _calculate_stability_compatibility(self, person_stability: float, vacancy_stability: float) -> float:
        """Calcula la compatibilidad de estabilidad."""
        stability_diff = abs(person_stability - vacancy_stability)
        return max(0.0, 100.0 - stability_diff)
    
    def _calculate_adaptability_synergy(self, person_adaptability: float, vacancy_adaptability: float) -> float:
        """Calcula la sinergia de adaptabilidad."""
        # Ambos altos = sinergia positiva
        if person_adaptability > 80 and vacancy_adaptability > 80:
            return 90.0
        # Ambos bajos = sinergia moderada
        elif person_adaptability < 40 and vacancy_adaptability < 40:
            return 70.0
        # Uno alto, uno bajo = sinergia variable
        else:
            return 60.0
    
    def _calculate_harmonic_alignment(self, person_harmonic: float, vacancy_harmonic: float) -> float:
        """Calcula la alineación armónica."""
        harmonic_diff = abs(person_harmonic - vacancy_harmonic)
        return max(0.0, 100.0 - harmonic_diff)
    
    def _generate_resonance_insights(
        self,
        person_vibration: VibrationalProfile,
        vacancy_vibration: VibrationalProfile,
        resonance_score: float
    ) -> Dict[str, Any]:
        """Genera insights sobre la resonancia vibracional."""
        return {
            'resonance_quality': 'excellent' if resonance_score >= 85 else 'good' if resonance_score >= 70 else 'moderate',
            'primary_frequency_description': self.frequency_characteristics[person_vibration.primary_frequency]['description'],
            'vacancy_frequency_description': self.frequency_characteristics[vacancy_vibration.primary_frequency]['description'],
            'synergy_potential': 'high' if resonance_score >= 80 else 'medium' if resonance_score >= 60 else 'low',
            'growth_compatibility': 'excellent' if resonance_score >= 85 else 'good' if resonance_score >= 70 else 'moderate'
        }
    
    def _generate_resonance_recommendations(
        self,
        person_vibration: VibrationalProfile,
        vacancy_vibration: VibrationalProfile,
        resonance_score: float
    ) -> List[str]:
        """Genera recomendaciones basadas en la resonancia vibracional."""
        recommendations = []
        
        if resonance_score >= 85:
            recommendations.append("Excelente resonancia vibracional - aprovechar la sinergia natural")
            recommendations.append("Mantener el equilibrio energético actual")
        elif resonance_score >= 70:
            recommendations.append("Buena resonancia vibracional - desarrollar complementariedad")
            recommendations.append("Trabajar en la alineación de frecuencias secundarias")
        elif resonance_score >= 50:
            recommendations.append("Resonancia vibracional moderada - buscar puntos de conexión")
            recommendations.append("Desarrollar técnicas de adaptación vibracional")
        else:
            recommendations.append("Resonancia vibracional baja - considerar desarrollo energético")
            recommendations.append("Evaluar compatibilidad a largo plazo")
        
        return recommendations
    
    def _create_default_vibrational_profile(self) -> VibrationalProfile:
        """Crea un perfil vibracional por defecto."""
        return VibrationalProfile(
            primary_frequency=VibrationalFrequency.BETA,
            secondary_frequency=VibrationalFrequency.ALPHA,
            resonance_patterns={},
            stability_index=70.0,
            adaptability_score=65.0,
            harmonic_balance=75.0,
            timestamp=datetime.now()
        ) 