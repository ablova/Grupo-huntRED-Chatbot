"""
Módulo de análisis de personalidad avanzado.
Integra componentes de análisis de personalidad, derailers y valores.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PersonalityDimension(Enum):
    ADJUSTMENT = "adjustment"
    AMBITION = "ambition"
    SOCIABILITY = "sociability"
    INTERPERSONAL_SENSITIVITY = "interpersonal_sensitivity"
    PRUDENCE = "prudence"
    INQUISITIVE = "inquisitive"
    LEARNING_APPROACH = "learning_approach"

class DerailerDimension(Enum):
    EXCITABLE = "excitable"
    SKEPTICAL = "skeptical"
    CAUTIOUS = "cautious"
    RESERVED = "reserved"
    LEISURELY = "leisurely"
    BOLD = "bold"
    MISCHIEVOUS = "mischievous"
    COLORFUL = "colorful"
    IMAGINATIVE = "imaginative"
    DILIGENT = "diligent"
    DUTIFUL = "dutiful"

class ValueDimension(Enum):
    RECOGNITION = "recognition"
    POWER = "power"
    HEDONISM = "hedonism"
    ALTRUISM = "altruism"
    AFFILIATION = "affiliation"
    TRADITION = "tradition"
    SECURITY = "security"
    COMMERCE = "commerce"
    AESTHETICS = "aesthetics"
    SCIENCE = "science"

@dataclass
class PersonalityInsight:
    dimension: PersonalityDimension
    score: float
    description: str
    strengths: List[str]
    development_areas: List[str]
    recommendations: List[str]

@dataclass
class DerailerInsight:
    dimension: DerailerDimension
    score: float
    description: str
    risk_level: str
    mitigation_strategies: List[str]

@dataclass
class ValueInsight:
    dimension: ValueDimension
    score: float
    description: str
    alignment: Dict[str, float]
    implications: List[str]

class AdvancedPersonalityAnalysis:
    """Análisis avanzado de personalidad que integra HPI, HDS y MVPI."""
    
    def __init__(self):
        self.personality_weights = {
            PersonalityDimension.ADJUSTMENT: 1.2,
            PersonalityDimension.AMBITION: 1.1,
            PersonalityDimension.SOCIABILITY: 1.0,
            PersonalityDimension.INTERPERSONAL_SENSITIVITY: 1.0,
            PersonalityDimension.PRUDENCE: 1.1,
            PersonalityDimension.INQUISITIVE: 1.0,
            PersonalityDimension.LEARNING_APPROACH: 1.2
        }
        
        self.derailer_thresholds = {
            DerailerDimension.EXCITABLE: 0.7,
            DerailerDimension.SKEPTICAL: 0.7,
            DerailerDimension.CAUTIOUS: 0.7,
            DerailerDimension.RESERVED: 0.7,
            DerailerDimension.LEISURELY: 0.7,
            DerailerDimension.BOLD: 0.7,
            DerailerDimension.MISCHIEVOUS: 0.7,
            DerailerDimension.COLORFUL: 0.7,
            DerailerDimension.IMAGINATIVE: 0.7,
            DerailerDimension.DILIGENT: 0.7,
            DerailerDimension.DUTIFUL: 0.7
        }
        
        self.value_weights = {
            ValueDimension.RECOGNITION: 1.1,
            ValueDimension.POWER: 1.0,
            ValueDimension.HEDONISM: 0.9,
            ValueDimension.ALTRUISM: 1.1,
            ValueDimension.AFFILIATION: 1.0,
            ValueDimension.TRADITION: 0.9,
            ValueDimension.SECURITY: 1.0,
            ValueDimension.COMMERCE: 1.1,
            ValueDimension.AESTHETICS: 0.9,
            ValueDimension.SCIENCE: 1.0
        }
    
    def analyze(self, responses: Dict) -> Dict:
        """
        Analiza las respuestas y genera insights completos.
        
        Args:
            responses: Diccionario con las respuestas del candidato
            
        Returns:
            Dict con los resultados del análisis
        """
        try:
            # Análisis de personalidad (HPI)
            personality_insights = self._analyze_personality(
                responses.get('personality', {})
            )
            
            # Análisis de derailers (HDS)
            derailer_insights = self._analyze_derailers(
                responses.get('derailers', {})
            )
            
            # Análisis de valores (MVPI)
            value_insights = self._analyze_values(
                responses.get('values', {})
            )
            
            # Generar recomendaciones integradas
            recommendations = self._generate_integrated_recommendations(
                personality_insights,
                derailer_insights,
                value_insights
            )
            
            return {
                'personality': personality_insights,
                'derailers': derailer_insights,
                'values': value_insights,
                'recommendations': recommendations,
                'overall_score': self._calculate_overall_score(
                    personality_insights,
                    derailer_insights,
                    value_insights
                )
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de personalidad: {str(e)}", exc_info=True)
            return {
                'error': f"Error en análisis: {str(e)}",
                'personality': [],
                'derailers': [],
                'values': [],
                'recommendations': []
            }
    
    def _analyze_personality(self, responses: Dict) -> List[PersonalityInsight]:
        """Analiza las dimensiones de personalidad."""
        insights = []
        
        for dimension in PersonalityDimension:
            if dimension.value in responses:
                score = self._calculate_dimension_score(
                    responses[dimension.value],
                    self.personality_weights[dimension]
                )
                
                insight = PersonalityInsight(
                    dimension=dimension,
                    score=score,
                    description=self._get_personality_description(dimension, score),
                    strengths=self._identify_personality_strengths(dimension, score),
                    development_areas=self._identify_development_areas(dimension, score),
                    recommendations=self._generate_personality_recommendations(dimension, score)
                )
                
                insights.append(insight)
        
        return insights
    
    def _analyze_derailers(self, responses: Dict) -> List[DerailerInsight]:
        """Analiza los derailers potenciales."""
        insights = []
        
        for dimension in DerailerDimension:
            if dimension.value in responses:
                score = self._calculate_derailer_score(
                    responses[dimension.value],
                    self.derailer_thresholds[dimension]
                )
                
                insight = DerailerInsight(
                    dimension=dimension,
                    score=score,
                    description=self._get_derailer_description(dimension, score),
                    risk_level=self._calculate_risk_level(score),
                    mitigation_strategies=self._generate_mitigation_strategies(dimension, score)
                )
                
                insights.append(insight)
        
        return insights
    
    def _analyze_values(self, responses: Dict) -> List[ValueInsight]:
        """Analiza los valores y motivaciones."""
        insights = []
        
        for dimension in ValueDimension:
            if dimension.value in responses:
                score = self._calculate_value_score(
                    responses[dimension.value],
                    self.value_weights[dimension]
                )
                
                insight = ValueInsight(
                    dimension=dimension,
                    score=score,
                    description=self._get_value_description(dimension, score),
                    alignment=self._calculate_value_alignment(dimension, score),
                    implications=self._generate_value_implications(dimension, score)
                )
                
                insights.append(insight)
        
        return insights
    
    def _generate_integrated_recommendations(
        self,
        personality_insights: List[PersonalityInsight],
        derailer_insights: List[DerailerInsight],
        value_insights: List[ValueInsight]
    ) -> List[str]:
        """Genera recomendaciones integradas basadas en todos los análisis."""
        recommendations = []
        
        # Recomendaciones basadas en personalidad
        for insight in personality_insights:
            recommendations.extend(insight.recommendations)
        
        # Recomendaciones para mitigar derailers
        for insight in derailer_insights:
            if insight.risk_level in ['high', 'medium']:
                recommendations.extend(insight.mitigation_strategies)
        
        # Recomendaciones basadas en valores
        for insight in value_insights:
            recommendations.extend(insight.implications)
        
        return list(set(recommendations))  # Eliminar duplicados
    
    def _calculate_overall_score(
        self,
        personality_insights: List[PersonalityInsight],
        derailer_insights: List[DerailerInsight],
        value_insights: List[ValueInsight]
    ) -> float:
        """Calcula el puntaje general integrado."""
        personality_score = sum(insight.score for insight in personality_insights) / len(personality_insights)
        derailer_score = sum(insight.score for insight in derailer_insights) / len(derailer_insights)
        value_score = sum(insight.score for insight in value_insights) / len(value_insights)
        
        return (personality_score * 0.5 + derailer_score * 0.3 + value_score * 0.2)
    
    # Métodos auxiliares para descripciones y recomendaciones
    def _get_personality_description(self, dimension: PersonalityDimension, score: float) -> str:
        """Genera descripción para una dimensión de personalidad."""
        descriptions = {
            PersonalityDimension.ADJUSTMENT: {
                'high': 'Maneja bien el estrés y la presión',
                'medium': 'Manejo moderado del estrés',
                'low': 'Puede tener dificultades con el estrés'
            },
            # Añadir descripciones para otras dimensiones...
        }
        
        if score >= 0.8:
            return descriptions[dimension]['high']
        elif score >= 0.5:
            return descriptions[dimension]['medium']
        else:
            return descriptions[dimension]['low']
    
    def _get_derailer_description(self, dimension: DerailerDimension, score: float) -> str:
        """Genera descripción para un derailer."""
        descriptions = {
            DerailerDimension.EXCITABLE: {
                'high': 'Puede ser muy reactivo emocionalmente',
                'medium': 'Moderadamente reactivo',
                'low': 'Manejo emocional estable'
            },
            # Añadir descripciones para otros derailers...
        }
        
        if score >= 0.7:
            return descriptions[dimension]['high']
        elif score >= 0.4:
            return descriptions[dimension]['medium']
        else:
            return descriptions[dimension]['low']
    
    def _get_value_description(self, dimension: ValueDimension, score: float) -> str:
        """Genera descripción para un valor."""
        descriptions = {
            ValueDimension.RECOGNITION: {
                'high': 'Busca activamente reconocimiento',
                'medium': 'Valora el reconocimiento moderadamente',
                'low': 'Menos motivado por el reconocimiento'
            },
            # Añadir descripciones para otros valores...
        }
        
        if score >= 0.8:
            return descriptions[dimension]['high']
        elif score >= 0.5:
            return descriptions[dimension]['medium']
        else:
            return descriptions[dimension]['low']
    
    def _identify_personality_strengths(self, dimension: PersonalityDimension, score: float) -> List[str]:
        """Identifica fortalezas basadas en la puntuación."""
        strengths = {
            PersonalityDimension.ADJUSTMENT: [
                'Resiliencia emocional',
                'Manejo del estrés',
                'Estabilidad bajo presión'
            ],
            # Añadir fortalezas para otras dimensiones...
        }
        
        return strengths.get(dimension, []) if score >= 0.7 else []
    
    def _identify_development_areas(self, dimension: PersonalityDimension, score: float) -> List[str]:
        """Identifica áreas de desarrollo basadas en la puntuación."""
        areas = {
            PersonalityDimension.ADJUSTMENT: [
                'Gestión del estrés',
                'Resiliencia emocional',
                'Adaptabilidad'
            ],
            # Añadir áreas para otras dimensiones...
        }
        
        return areas.get(dimension, []) if score < 0.7 else []
    
    def _generate_personality_recommendations(self, dimension: PersonalityDimension, score: float) -> List[str]:
        """Genera recomendaciones basadas en la puntuación de personalidad."""
        recommendations = {
            PersonalityDimension.ADJUSTMENT: [
                'Practicar técnicas de mindfulness',
                'Desarrollar estrategias de afrontamiento',
                'Buscar feedback sobre manejo del estrés'
            ],
            # Añadir recomendaciones para otras dimensiones...
        }
        
        return recommendations.get(dimension, []) if score < 0.7 else []
    
    def _calculate_risk_level(self, score: float) -> str:
        """Calcula el nivel de riesgo basado en la puntuación."""
        if score >= 0.7:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _generate_mitigation_strategies(self, dimension: DerailerDimension, score: float) -> List[str]:
        """Genera estrategias de mitigación para derailers."""
        strategies = {
            DerailerDimension.EXCITABLE: [
                'Desarrollar técnicas de regulación emocional',
                'Practicar la pausa reflexiva',
                'Buscar feedback sobre reacciones emocionales'
            ],
            # Añadir estrategias para otros derailers...
        }
        
        return strategies.get(dimension, []) if score >= 0.7 else []
    
    def _calculate_value_alignment(self, dimension: ValueDimension, score: float) -> Dict[str, float]:
        """Calcula la alineación de valores con diferentes contextos."""
        alignments = {
            ValueDimension.RECOGNITION: {
                'startup': 0.8,
                'corporate': 0.6,
                'non_profit': 0.4
            },
            # Añadir alineaciones para otros valores...
        }
        
        return alignments.get(dimension, {})
    
    def _generate_value_implications(self, dimension: ValueDimension, score: float) -> List[str]:
        """Genera implicaciones basadas en los valores."""
        implications = {
            ValueDimension.RECOGNITION: [
                'Buscar roles con visibilidad',
                'Desarrollar habilidades de presentación',
                'Construir marca personal'
            ],
            # Añadir implicaciones para otros valores...
        }
        
        return implications.get(dimension, []) if score >= 0.7 else [] 