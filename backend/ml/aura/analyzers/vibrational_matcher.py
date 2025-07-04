"""
Vibrational Matcher - Sistema AURA huntRED® v2
Motor de compatibilidad vibracional avanzado para análisis holístico de candidatos.
"""

import logging
import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import json
import math
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from collections import defaultdict

from ...core.base_analyzer import BaseAnalyzer
from ...core.exceptions import AuraAnalysisError, DataValidationError
from ...core.metrics import AuraMetrics


logger = logging.getLogger(__name__)


class VibrationalFrequency(Enum):
    """Frecuencias vibracionales básicas."""
    ALPHA = "alpha"      # 8-13 Hz - Creatividad, relajación
    BETA = "beta"        # 13-30 Hz - Concentración, análisis
    THETA = "theta"      # 4-8 Hz - Intuición, creatividad profunda
    GAMMA = "gamma"      # 30-100 Hz - Procesamiento de alto nivel
    DELTA = "delta"      # 0.5-4 Hz - Regeneración, descanso profundo


class PersonalityArchetype(Enum):
    """Arquetipos de personalidad vibracional."""
    INNOVATOR = "innovator"          # Alta frecuencia, creatividad
    ANALYZER = "analyzer"            # Media-alta frecuencia, lógica
    HARMONIZER = "harmonizer"        # Media frecuencia, equilibrio
    STABILIZER = "stabilizer"        # Media-baja frecuencia, estructura
    TRANSFORMER = "transformer"      # Variable, adaptabilidad


class EnergyPattern(Enum):
    """Patrones energéticos detectables."""
    ASCENDING = "ascending"          # Energía creciente
    DESCENDING = "descending"        # Energía decreciente
    STABLE = "stable"               # Energía constante
    OSCILLATING = "oscillating"     # Energía variable
    RESONANT = "resonant"           # Energía en resonancia


@dataclass
class VibrationalProfile:
    """Perfil vibracional de una persona."""
    person_id: str
    dominant_frequency: VibrationalFrequency
    frequency_distribution: Dict[VibrationalFrequency, float]
    personality_archetype: PersonalityArchetype
    energy_pattern: EnergyPattern
    vibrational_signature: np.ndarray
    harmonic_resonances: List[float]
    chakra_alignment: Dict[str, float]
    aura_colors: List[str]
    compatibility_matrix: Dict[str, float]
    strength_indicators: Dict[str, float]
    growth_potential: Dict[str, float]
    optimal_environments: List[str]
    synergy_factors: Dict[str, float]
    temporal_variations: Dict[str, List[float]]
    confidence_score: float
    analysis_timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompatibilityResult:
    """Resultado de análisis de compatibilidad vibracional."""
    person1_id: str
    person2_id: str
    overall_compatibility: float
    frequency_harmony: float
    archetype_synergy: float
    energy_synchronization: float
    resonance_strength: float
    complementary_score: float
    conflict_potential: float
    growth_potential: float
    optimal_collaboration_modes: List[str]
    recommended_interaction_frequency: str
    potential_challenges: List[str]
    synergy_opportunities: List[str]
    detailed_analysis: Dict[str, Any]
    confidence_level: float
    timestamp: datetime


class VibrationalMatcher(BaseAnalyzer):
    """
    Motor de análisis vibracional avanzado para el sistema AURA.
    
    Analiza patrones energéticos, frecuencias vibracionales y compatibilidades
    entre personas basándose en múltiples dimensiones sutiles.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el matcher vibracional.
        
        Args:
            config: Configuración personalizada del analizador
        """
        super().__init__(config)
        self.model_name = "vibrational_matcher"
        self.version = "3.0.0"
        
        # Configuración por defecto
        self.default_config = {
            'frequency_resolution': 0.1,
            'harmonic_depth': 12,
            'temporal_window_days': 30,
            'compatibility_threshold': 0.7,
            'resonance_sensitivity': 0.05,
            'archetype_weight': 0.25,
            'frequency_weight': 0.25,
            'energy_weight': 0.25,
            'resonance_weight': 0.25,
            'enable_chakra_analysis': True,
            'enable_aura_colors': True,
            'enable_temporal_tracking': True,
            'cache_profiles': True,
            'profile_cache_ttl': 3600,  # 1 hora
            'batch_size': 50,
            'precision_mode': 'high',
            'quantum_corrections': True,
            'lunar_influence': True,
            'seasonal_adjustments': True
        }
        
        self.config = {**self.default_config, **(config or {})}
        self.metrics = AuraMetrics("vibrational_matcher")
        
        # Matrices de frecuencias base
        self._base_frequencies = self._initialize_base_frequencies()
        self._harmonic_series = self._calculate_harmonic_series()
        self._archetype_signatures = self._initialize_archetype_signatures()
        self._chakra_frequencies = self._initialize_chakra_frequencies()
        self._color_frequency_map = self._initialize_color_frequency_map()
        
        # Cache para perfiles
        self._profile_cache = {}
        self._compatibility_cache = {}
        
        logger.info(f"Vibrational Matcher {self.version} initialized")
    
    def _initialize_base_frequencies(self) -> Dict[VibrationalFrequency, Tuple[float, float]]:
        """Inicializa las frecuencias base para cada banda."""
        return {
            VibrationalFrequency.DELTA: (0.5, 4.0),
            VibrationalFrequency.THETA: (4.0, 8.0),
            VibrationalFrequency.ALPHA: (8.0, 13.0),
            VibrationalFrequency.BETA: (13.0, 30.0),
            VibrationalFrequency.GAMMA: (30.0, 100.0)
        }
    
    def _calculate_harmonic_series(self) -> Dict[str, List[float]]:
        """Calcula las series armónicas para cada frecuencia base."""
        harmonics = {}
        for freq_type, (min_freq, max_freq) in self._base_frequencies.items():
            fundamental = (min_freq + max_freq) / 2
            harmonic_series = []
            for n in range(1, self.config['harmonic_depth'] + 1):
                harmonic_series.append(fundamental * n)
            harmonics[freq_type.value] = harmonic_series
        return harmonics
    
    def _initialize_archetype_signatures(self) -> Dict[PersonalityArchetype, np.ndarray]:
        """Inicializa las firmas vibracionales de cada arquetipo."""
        signatures = {}
        
        # Innovator: Alta gamma y beta, creatividad elevada
        signatures[PersonalityArchetype.INNOVATOR] = np.array([
            0.1,  # Delta
            0.2,  # Theta
            0.25, # Alpha
            0.25, # Beta
            0.2   # Gamma
        ])
        
        # Analyzer: Alta beta, procesamiento lógico
        signatures[PersonalityArchetype.ANALYZER] = np.array([
            0.1,  # Delta
            0.15, # Theta
            0.2,  # Alpha
            0.4,  # Beta
            0.15  # Gamma
        ])
        
        # Harmonizer: Distribución equilibrada
        signatures[PersonalityArchetype.HARMONIZER] = np.array([
            0.2,  # Delta
            0.2,  # Theta
            0.2,  # Alpha
            0.2,  # Beta
            0.2   # Gamma
        ])
        
        # Stabilizer: Alta delta y theta, estabilidad
        signatures[PersonalityArchetype.STABILIZER] = np.array([
            0.3,  # Delta
            0.25, # Theta
            0.2,  # Alpha
            0.15, # Beta
            0.1   # Gamma
        ])
        
        # Transformer: Patrón variable
        signatures[PersonalityArchetype.TRANSFORMER] = np.array([
            0.15, # Delta
            0.25, # Theta
            0.3,  # Alpha
            0.2,  # Beta
            0.1   # Gamma
        ])
        
        return signatures
    
    def _initialize_chakra_frequencies(self) -> Dict[str, float]:
        """Inicializa las frecuencias de los chakras."""
        return {
            'root': 256.0,       # Do - Raíz
            'sacral': 288.0,     # Re - Sacro
            'solar': 320.0,      # Mi - Plexo solar
            'heart': 341.3,      # Fa - Corazón
            'throat': 384.0,     # Sol - Garganta
            'third_eye': 426.7,  # La - Tercer ojo
            'crown': 480.0       # Si - Corona
        }
    
    def _initialize_color_frequency_map(self) -> Dict[str, Tuple[float, float]]:
        """Mapea colores del aura a frecuencias."""
        return {
            'red': (430, 480),       # Energía, pasión
            'orange': (480, 510),    # Creatividad, vitalidad
            'yellow': (510, 540),    # Intelectualidad, alegría
            'green': (540, 580),     # Equilibrio, sanación
            'blue': (580, 620),      # Comunicación, calma
            'indigo': (620, 680),    # Intuición, sabiduría
            'violet': (680, 750),    # Espiritualidad, transformación
            'white': (400, 750),     # Pureza, totalidad
            'gold': (570, 590),      # Iluminación, maestría
            'silver': (400, 450)     # Reflexión, feminidad
        }
    
    async def analyze_vibrational_profile(
        self,
        person_data: Dict[str, Any],
        historical_data: Optional[List[Dict]] = None
    ) -> VibrationalProfile:
        """
        Analiza el perfil vibracional completo de una persona.
        
        Args:
            person_data: Datos de la persona
            historical_data: Datos históricos para análisis temporal
            
        Returns:
            Perfil vibracional completo
        """
        try:
            person_id = str(person_data.get('id', ''))
            
            # Verificar cache
            cache_key = f"profile_{person_id}"
            if self.config['cache_profiles'] and cache_key in self._profile_cache:
                cached_profile = self._profile_cache[cache_key]
                if self._is_cache_valid(cached_profile.analysis_timestamp):
                    return cached_profile
            
            start_time = datetime.now()
            
            # Extraer características para análisis
            characteristics = await self._extract_vibrational_characteristics(person_data)
            
            # Calcular frecuencias dominantes
            frequency_distribution = await self._calculate_frequency_distribution(characteristics)
            dominant_frequency = max(frequency_distribution, key=frequency_distribution.get)
            
            # Determinar arquetipo de personalidad
            personality_archetype = await self._determine_personality_archetype(
                frequency_distribution, characteristics
            )
            
            # Analizar patrón energético
            energy_pattern = await self._analyze_energy_pattern(
                characteristics, historical_data
            )
            
            # Generar firma vibracional
            vibrational_signature = await self._generate_vibrational_signature(
                frequency_distribution, characteristics
            )
            
            # Calcular resonancias armónicas
            harmonic_resonances = await self._calculate_harmonic_resonances(
                vibrational_signature
            )
            
            # Analizar alineación de chakras
            chakra_alignment = {}
            if self.config['enable_chakra_analysis']:
                chakra_alignment = await self._analyze_chakra_alignment(
                    frequency_distribution, characteristics
                )
            
            # Determinar colores del aura
            aura_colors = []
            if self.config['enable_aura_colors']:
                aura_colors = await self._determine_aura_colors(
                    frequency_distribution, chakra_alignment
                )
            
            # Calcular matriz de compatibilidad
            compatibility_matrix = await self._calculate_compatibility_matrix(
                vibrational_signature, personality_archetype
            )
            
            # Analizar indicadores de fortaleza
            strength_indicators = await self._analyze_strength_indicators(
                characteristics, frequency_distribution
            )
            
            # Evaluar potencial de crecimiento
            growth_potential = await self._evaluate_growth_potential(
                personality_archetype, energy_pattern, characteristics
            )
            
            # Determinar entornos óptimos
            optimal_environments = await self._determine_optimal_environments(
                personality_archetype, frequency_distribution
            )
            
            # Calcular factores de sinergia
            synergy_factors = await self._calculate_synergy_factors(
                vibrational_signature, personality_archetype
            )
            
            # Análisis temporal
            temporal_variations = {}
            if self.config['enable_temporal_tracking'] and historical_data:
                temporal_variations = await self._analyze_temporal_variations(
                    historical_data
                )
            
            # Calcular puntuación de confianza
            confidence_score = await self._calculate_confidence_score(
                characteristics, len(historical_data) if historical_data else 0
            )
            
            # Crear perfil vibracional
            profile = VibrationalProfile(
                person_id=person_id,
                dominant_frequency=dominant_frequency,
                frequency_distribution=frequency_distribution,
                personality_archetype=personality_archetype,
                energy_pattern=energy_pattern,
                vibrational_signature=vibrational_signature,
                harmonic_resonances=harmonic_resonances,
                chakra_alignment=chakra_alignment,
                aura_colors=aura_colors,
                compatibility_matrix=compatibility_matrix,
                strength_indicators=strength_indicators,
                growth_potential=growth_potential,
                optimal_environments=optimal_environments,
                synergy_factors=synergy_factors,
                temporal_variations=temporal_variations,
                confidence_score=confidence_score,
                analysis_timestamp=datetime.now(),
                metadata={
                    'analysis_version': self.version,
                    'data_quality': await self._assess_data_quality(person_data),
                    'processing_time': (datetime.now() - start_time).total_seconds()
                }
            )
            
            # Guardar en cache
            if self.config['cache_profiles']:
                self._profile_cache[cache_key] = profile
            
            # Registrar métricas
            await self.metrics.record_analysis(
                'vibrational_profile',
                (datetime.now() - start_time).total_seconds(),
                {'confidence': confidence_score, 'archetype': personality_archetype.value}
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Error analyzing vibrational profile: {e}")
            await self.metrics.record_error('vibrational_profile', str(e))
            raise AuraAnalysisError(f"Vibrational profile analysis failed: {e}")
    
    async def calculate_compatibility(
        self,
        profile1: VibrationalProfile,
        profile2: VibrationalProfile,
        context: Optional[str] = None
    ) -> CompatibilityResult:
        """
        Calcula la compatibilidad vibracional entre dos perfiles.
        
        Args:
            profile1: Primer perfil vibracional
            profile2: Segundo perfil vibracional
            context: Contexto de la interacción (trabajo, romántico, etc.)
            
        Returns:
            Resultado de compatibilidad vibracional
        """
        try:
            # Verificar cache
            cache_key = f"compat_{profile1.person_id}_{profile2.person_id}_{context or 'general'}"
            if cache_key in self._compatibility_cache:
                cached_result = self._compatibility_cache[cache_key]
                if self._is_cache_valid(cached_result.timestamp):
                    return cached_result
            
            start_time = datetime.now()
            
            # Análisis de armonía de frecuencias
            frequency_harmony = await self._calculate_frequency_harmony(
                profile1.frequency_distribution,
                profile2.frequency_distribution
            )
            
            # Análisis de sinergia de arquetipos
            archetype_synergy = await self._calculate_archetype_synergy(
                profile1.personality_archetype,
                profile2.personality_archetype,
                context
            )
            
            # Análisis de sincronización energética
            energy_synchronization = await self._calculate_energy_synchronization(
                profile1.energy_pattern,
                profile2.energy_pattern,
                profile1.vibrational_signature,
                profile2.vibrational_signature
            )
            
            # Análisis de fuerza de resonancia
            resonance_strength = await self._calculate_resonance_strength(
                profile1.harmonic_resonances,
                profile2.harmonic_resonances
            )
            
            # Puntuación complementaria
            complementary_score = await self._calculate_complementary_score(
                profile1, profile2
            )
            
            # Potencial de conflicto
            conflict_potential = await self._assess_conflict_potential(
                profile1, profile2, context
            )
            
            # Potencial de crecimiento conjunto
            growth_potential = await self._assess_mutual_growth_potential(
                profile1, profile2
            )
            
            # Modos óptimos de colaboración
            optimal_collaboration_modes = await self._determine_collaboration_modes(
                profile1, profile2, context
            )
            
            # Frecuencia de interacción recomendada
            interaction_frequency = await self._recommend_interaction_frequency(
                profile1, profile2, context
            )
            
            # Identificar desafíos potenciales
            potential_challenges = await self._identify_potential_challenges(
                profile1, profile2, context
            )
            
            # Oportunidades de sinergia
            synergy_opportunities = await self._identify_synergy_opportunities(
                profile1, profile2, context
            )
            
            # Compatibilidad general ponderada
            overall_compatibility = await self._calculate_overall_compatibility([
                (frequency_harmony, self.config['frequency_weight']),
                (archetype_synergy, self.config['archetype_weight']),
                (energy_synchronization, self.config['energy_weight']),
                (resonance_strength, self.config['resonance_weight'])
            ])
            
            # Análisis detallado
            detailed_analysis = await self._generate_detailed_analysis(
                profile1, profile2, {
                    'frequency_harmony': frequency_harmony,
                    'archetype_synergy': archetype_synergy,
                    'energy_synchronization': energy_synchronization,
                    'resonance_strength': resonance_strength
                }
            )
            
            # Nivel de confianza
            confidence_level = min(profile1.confidence_score, profile2.confidence_score)
            
            # Crear resultado
            result = CompatibilityResult(
                person1_id=profile1.person_id,
                person2_id=profile2.person_id,
                overall_compatibility=overall_compatibility,
                frequency_harmony=frequency_harmony,
                archetype_synergy=archetype_synergy,
                energy_synchronization=energy_synchronization,
                resonance_strength=resonance_strength,
                complementary_score=complementary_score,
                conflict_potential=conflict_potential,
                growth_potential=growth_potential,
                optimal_collaboration_modes=optimal_collaboration_modes,
                recommended_interaction_frequency=interaction_frequency,
                potential_challenges=potential_challenges,
                synergy_opportunities=synergy_opportunities,
                detailed_analysis=detailed_analysis,
                confidence_level=confidence_level,
                timestamp=datetime.now()
            )
            
            # Guardar en cache
            self._compatibility_cache[cache_key] = result
            
            # Registrar métricas
            await self.metrics.record_analysis(
                'compatibility_calculation',
                (datetime.now() - start_time).total_seconds(),
                {
                    'overall_compatibility': overall_compatibility,
                    'confidence': confidence_level,
                    'context': context or 'general'
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating compatibility: {e}")
            await self.metrics.record_error('compatibility_calculation', str(e))
            raise AuraAnalysisError(f"Compatibility calculation failed: {e}")
    
    async def _extract_vibrational_characteristics(
        self,
        person_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extrae características relevantes para análisis vibracional."""
        
        characteristics = {}
        
        # Características básicas
        characteristics['age'] = person_data.get('age', 30)
        characteristics['gender'] = person_data.get('gender', 'unknown')
        
        # Personalidad (Big Five)
        characteristics['openness'] = person_data.get('openness', 50) / 100
        characteristics['conscientiousness'] = person_data.get('conscientiousness', 50) / 100
        characteristics['extraversion'] = person_data.get('extraversion', 50) / 100
        characteristics['agreeableness'] = person_data.get('agreeableness', 50) / 100
        characteristics['neuroticism'] = person_data.get('neuroticism', 50) / 100
        
        # Características profesionales
        characteristics['experience_years'] = person_data.get('experience_years', 0)
        characteristics['skills'] = person_data.get('skills', [])
        characteristics['leadership_score'] = person_data.get('leadership_score', 0)
        
        # Datos de interacción
        characteristics['communication_style'] = person_data.get('communication_style', 'balanced')
        characteristics['work_style'] = person_data.get('work_style', 'collaborative')
        characteristics['stress_tolerance'] = person_data.get('stress_tolerance', 50) / 100
        
        # Valores y motivaciones
        characteristics['values'] = person_data.get('values', {})
        characteristics['motivations'] = person_data.get('motivations', [])
        
        # Contexto temporal
        characteristics['current_mood'] = person_data.get('current_mood', 'neutral')
        characteristics['energy_level'] = person_data.get('energy_level', 50) / 100
        
        return characteristics
    
    async def _calculate_frequency_distribution(
        self,
        characteristics: Dict[str, Any]
    ) -> Dict[VibrationalFrequency, float]:
        """Calcula la distribución de frecuencias vibracionales."""
        
        distribution = {}
        
        # Delta: Estabilidad, estructura
        delta_score = (
            characteristics['conscientiousness'] * 0.4 +
            characteristics['agreeableness'] * 0.3 +
            (1 - characteristics['neuroticism']) * 0.3
        )
        distribution[VibrationalFrequency.DELTA] = delta_score
        
        # Theta: Creatividad, intuición
        theta_score = (
            characteristics['openness'] * 0.5 +
            (1 - characteristics['conscientiousness']) * 0.2 +
            characteristics['extraversion'] * 0.3
        )
        distribution[VibrationalFrequency.THETA] = theta_score
        
        # Alpha: Equilibrio, armonía
        alpha_score = (
            characteristics['agreeableness'] * 0.4 +
            (1 - characteristics['neuroticism']) * 0.4 +
            characteristics['stress_tolerance'] * 0.2
        )
        distribution[VibrationalFrequency.ALPHA] = alpha_score
        
        # Beta: Análisis, concentración
        beta_score = (
            characteristics['conscientiousness'] * 0.4 +
            (1 - characteristics['openness']) * 0.3 +
            characteristics['leadership_score'] / 100 * 0.3
        )
        distribution[VibrationalFrequency.BETA] = beta_score
        
        # Gamma: Procesamiento superior, insights
        gamma_score = (
            characteristics['openness'] * 0.5 +
            characteristics['experience_years'] / 20 * 0.3 +
            characteristics['leadership_score'] / 100 * 0.2
        )
        distribution[VibrationalFrequency.GAMMA] = gamma_score
        
        # Normalizar distribución
        total = sum(distribution.values())
        if total > 0:
            distribution = {k: v / total for k, v in distribution.items()}
        
        return distribution
    
    async def _determine_personality_archetype(
        self,
        frequency_distribution: Dict[VibrationalFrequency, float],
        characteristics: Dict[str, Any]
    ) -> PersonalityArchetype:
        """Determina el arquetipo de personalidad basado en frecuencias."""
        
        scores = {}
        
        for archetype in PersonalityArchetype:
            signature = self._archetype_signatures[archetype]
            freq_vector = np.array([
                frequency_distribution[VibrationalFrequency.DELTA],
                frequency_distribution[VibrationalFrequency.THETA],
                frequency_distribution[VibrationalFrequency.ALPHA],
                frequency_distribution[VibrationalFrequency.BETA],
                frequency_distribution[VibrationalFrequency.GAMMA]
            ])
            
            # Calcular similitud coseno
            similarity = np.dot(signature, freq_vector) / (
                np.linalg.norm(signature) * np.linalg.norm(freq_vector)
            )
            
            # Ajustar por características específicas
            if archetype == PersonalityArchetype.INNOVATOR:
                similarity *= (1 + characteristics['openness'] * 0.5)
            elif archetype == PersonalityArchetype.ANALYZER:
                similarity *= (1 + characteristics['conscientiousness'] * 0.5)
            elif archetype == PersonalityArchetype.HARMONIZER:
                similarity *= (1 + characteristics['agreeableness'] * 0.5)
            elif archetype == PersonalityArchetype.STABILIZER:
                similarity *= (1 + (1 - characteristics['neuroticism']) * 0.5)
            elif archetype == PersonalityArchetype.TRANSFORMER:
                similarity *= (1 + characteristics['extraversion'] * 0.5)
            
            scores[archetype] = similarity
        
        return max(scores, key=scores.get)
    
    async def _analyze_energy_pattern(
        self,
        characteristics: Dict[str, Any],
        historical_data: Optional[List[Dict]]
    ) -> EnergyPattern:
        """Analiza el patrón energético de la persona."""
        
        if not historical_data or len(historical_data) < 3:
            # Sin datos históricos, inferir del estado actual
            energy_level = characteristics.get('energy_level', 0.5)
            
            if energy_level > 0.8:
                return EnergyPattern.ASCENDING
            elif energy_level < 0.3:
                return EnergyPattern.DESCENDING
            else:
                return EnergyPattern.STABLE
        
        # Analizar tendencia histórica
        energy_levels = [data.get('energy_level', 0.5) for data in historical_data[-10:]]
        
        # Calcular tendencia
        x = np.arange(len(energy_levels))
        z = np.polyfit(x, energy_levels, 1)
        slope = z[0]
        
        # Calcular variabilidad
        std_dev = np.std(energy_levels)
        
        if std_dev > 0.2:
            return EnergyPattern.OSCILLATING
        elif abs(slope) < 0.01:
            return EnergyPattern.STABLE
        elif slope > 0.05:
            return EnergyPattern.ASCENDING
        elif slope < -0.05:
            return EnergyPattern.DESCENDING
        else:
            # Verificar resonancia (patrones cíclicos)
            if self._detect_resonance_pattern(energy_levels):
                return EnergyPattern.RESONANT
            else:
                return EnergyPattern.STABLE
    
    def _detect_resonance_pattern(self, energy_levels: List[float]) -> bool:
        """Detecta patrones de resonancia en los niveles de energía."""
        if len(energy_levels) < 6:
            return False
        
        # Usar FFT para detectar periodicidades
        fft = np.fft.fft(energy_levels)
        freqs = np.fft.fftfreq(len(energy_levels))
        
        # Buscar picos significativos
        magnitude = np.abs(fft)
        peak_threshold = np.mean(magnitude) + 2 * np.std(magnitude)
        
        peaks = magnitude > peak_threshold
        return np.sum(peaks) > 1
    
    async def _generate_vibrational_signature(
        self,
        frequency_distribution: Dict[VibrationalFrequency, float],
        characteristics: Dict[str, Any]
    ) -> np.ndarray:
        """Genera la firma vibracional única de la persona."""
        
        # Vector base de frecuencias
        base_vector = np.array([
            frequency_distribution[VibrationalFrequency.DELTA],
            frequency_distribution[VibrationalFrequency.THETA],
            frequency_distribution[VibrationalFrequency.ALPHA],
            frequency_distribution[VibrationalFrequency.BETA],
            frequency_distribution[VibrationalFrequency.GAMMA]
        ])
        
        # Aplicar modulaciones basadas en características
        modulations = np.array([
            characteristics['agreeableness'],
            characteristics['openness'],
            characteristics['stress_tolerance'],
            characteristics['conscientiousness'],
            characteristics['extraversion']
        ])
        
        # Combinar base con modulaciones
        signature = base_vector * (0.7 + 0.3 * modulations)
        
        # Añadir armónicos
        harmonics = []
        for i, freq_amplitude in enumerate(signature):
            for harmonic in range(2, 6):  # 2nd to 5th harmonics
                harmonic_amplitude = freq_amplitude / (harmonic ** 1.5)
                harmonics.append(harmonic_amplitude)
        
        # Combinar fundamental con armónicos
        full_signature = np.concatenate([signature, harmonics])
        
        # Normalizar
        return full_signature / np.linalg.norm(full_signature)
    
    async def _calculate_harmonic_resonances(
        self,
        vibrational_signature: np.ndarray
    ) -> List[float]:
        """Calcula las resonancias armónicas de la firma vibracional."""
        
        resonances = []
        
        # Usar las primeras 5 componentes como fundamentales
        fundamentals = vibrational_signature[:5]
        
        for i, amplitude in enumerate(fundamentals):
            if amplitude > 0.1:  # Solo considerar frecuencias significativas
                base_freq = list(self._base_frequencies.values())[i]
                center_freq = (base_freq[0] + base_freq[1]) / 2
                
                # Calcular resonancias armónicas
                for harmonic in range(1, 8):
                    resonant_freq = center_freq * harmonic
                    resonant_amplitude = amplitude / (harmonic ** 0.5)
                    
                    if resonant_amplitude > 0.05:
                        resonances.append(resonant_freq)
        
        return sorted(set(resonances))  # Remover duplicados y ordenar
    
    async def _analyze_chakra_alignment(
        self,
        frequency_distribution: Dict[VibrationalFrequency, float],
        characteristics: Dict[str, Any]
    ) -> Dict[str, float]:
        """Analiza la alineación de los chakras."""
        
        alignment = {}
        
        # Root Chakra - Estabilidad, seguridad
        alignment['root'] = (
            frequency_distribution[VibrationalFrequency.DELTA] * 0.6 +
            (1 - characteristics['neuroticism']) * 0.4
        )
        
        # Sacral Chakra - Creatividad, sexualidad
        alignment['sacral'] = (
            frequency_distribution[VibrationalFrequency.THETA] * 0.5 +
            characteristics['openness'] * 0.3 +
            characteristics['extraversion'] * 0.2
        )
        
        # Solar Plexus - Poder personal, confianza
        alignment['solar'] = (
            frequency_distribution[VibrationalFrequency.BETA] * 0.4 +
            characteristics['conscientiousness'] * 0.3 +
            characteristics['leadership_score'] / 100 * 0.3
        )
        
        # Heart Chakra - Amor, compasión
        alignment['heart'] = (
            frequency_distribution[VibrationalFrequency.ALPHA] * 0.5 +
            characteristics['agreeableness'] * 0.5
        )
        
        # Throat Chakra - Comunicación, expresión
        alignment['throat'] = (
            frequency_distribution[VibrationalFrequency.BETA] * 0.4 +
            characteristics['extraversion'] * 0.6
        )
        
        # Third Eye - Intuición, sabiduría
        alignment['third_eye'] = (
            frequency_distribution[VibrationalFrequency.GAMMA] * 0.6 +
            characteristics['openness'] * 0.4
        )
        
        # Crown Chakra - Espiritualidad, conexión
        alignment['crown'] = (
            frequency_distribution[VibrationalFrequency.GAMMA] * 0.5 +
            characteristics['openness'] * 0.3 +
            (1 - characteristics['neuroticism']) * 0.2
        )
        
        return alignment
    
    async def _determine_aura_colors(
        self,
        frequency_distribution: Dict[VibrationalFrequency, float],
        chakra_alignment: Dict[str, float]
    ) -> List[str]:
        """Determina los colores del aura basados en frecuencias y chakras."""
        
        color_scores = {}
        
        # Mapear frecuencias a colores
        if frequency_distribution[VibrationalFrequency.DELTA] > 0.25:
            color_scores['red'] = frequency_distribution[VibrationalFrequency.DELTA]
        
        if frequency_distribution[VibrationalFrequency.THETA] > 0.25:
            color_scores['orange'] = frequency_distribution[VibrationalFrequency.THETA]
        
        if frequency_distribution[VibrationalFrequency.ALPHA] > 0.25:
            color_scores['green'] = frequency_distribution[VibrationalFrequency.ALPHA]
        
        if frequency_distribution[VibrationalFrequency.BETA] > 0.25:
            color_scores['blue'] = frequency_distribution[VibrationalFrequency.BETA]
        
        if frequency_distribution[VibrationalFrequency.GAMMA] > 0.25:
            color_scores['violet'] = frequency_distribution[VibrationalFrequency.GAMMA]
        
        # Considerar alineación de chakras
        if chakra_alignment.get('heart', 0) > 0.8:
            color_scores['green'] = color_scores.get('green', 0) + 0.2
        
        if chakra_alignment.get('crown', 0) > 0.8:
            color_scores['white'] = 0.9
        
        if chakra_alignment.get('third_eye', 0) > 0.8:
            color_scores['indigo'] = 0.8
        
        # Seleccionar colores predominantes
        sorted_colors = sorted(color_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Retornar los 3 colores más fuertes
        return [color for color, score in sorted_colors[:3] if score > 0.3]
    
    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Verifica si el cache sigue siendo válido."""
        return (datetime.now() - timestamp).total_seconds() < self.config['profile_cache_ttl']