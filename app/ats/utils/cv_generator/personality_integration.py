"""
Módulo de integración de personalidad con el CV Generator.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from app.ats.chatbot.workflow.assessments.professional_dna.personality_analysis import (
    PersonalityDimension,
    DerailerDimension,
    ValueDimension,
    PersonalityInsight,
    DerailerInsight,
    ValueInsight
)

logger = logging.getLogger(__name__)

@dataclass
class CVOptimization:
    """Resultado de la optimización del CV basada en personalidad."""
    strengths: List[str]
    keywords: List[str]
    style: Dict[str, Any]
    sections: Dict[str, List[str]]
    recommendations: List[str]

class PersonalityCVIntegrator:
    """Integra insights de personalidad con la generación de CV."""
    
    def __init__(self):
        self.strength_mapping = {
            PersonalityDimension.ADJUSTMENT: [
                'Resiliencia',
                'Manejo del estrés',
                'Adaptabilidad'
            ],
            PersonalityDimension.AMBITION: [
                'Orientación a resultados',
                'Liderazgo',
                'Visión estratégica'
            ],
            PersonalityDimension.SOCIABILITY: [
                'Trabajo en equipo',
                'Comunicación efectiva',
                'Relaciones interpersonales'
            ],
            PersonalityDimension.INTERPERSONAL_SENSITIVITY: [
                'Inteligencia emocional',
                'Empatía',
                'Gestión de conflictos'
            ],
            PersonalityDimension.PRUDENCE: [
                'Pensamiento analítico',
                'Toma de decisiones',
                'Gestión de riesgos'
            ],
            PersonalityDimension.INQUISITIVE: [
                'Innovación',
                'Aprendizaje continuo',
                'Pensamiento crítico'
            ],
            PersonalityDimension.LEARNING_APPROACH: [
                'Desarrollo profesional',
                'Adaptabilidad',
                'Mejora continua'
            ]
        }
        
        self.style_mapping = {
            'adjustment': {
                'high': {
                    'tone': 'confident',
                    'emphasis': 'achievements',
                    'format': 'dynamic'
                },
                'medium': {
                    'tone': 'balanced',
                    'emphasis': 'experience',
                    'format': 'standard'
                },
                'low': {
                    'tone': 'professional',
                    'emphasis': 'skills',
                    'format': 'structured'
                }
            },
            'ambition': {
                'high': {
                    'tone': 'assertive',
                    'emphasis': 'goals',
                    'format': 'impact'
                },
                'medium': {
                    'tone': 'motivated',
                    'emphasis': 'growth',
                    'format': 'progressive'
                },
                'low': {
                    'tone': 'steady',
                    'emphasis': 'stability',
                    'format': 'traditional'
                }
            }
        }
        
        self.section_optimization = {
            'summary': {
                'adjustment': {
                    'high': 'Enfocado en logros y manejo de desafíos',
                    'medium': 'Balance entre experiencia y adaptabilidad',
                    'low': 'Énfasis en habilidades técnicas y estabilidad'
                },
                'ambition': {
                    'high': 'Orientado a resultados y crecimiento',
                    'medium': 'Balance entre desarrollo y contribución',
                    'low': 'Énfasis en experiencia y confiabilidad'
                }
            },
            'experience': {
                'adjustment': {
                    'high': 'Enfocado en logros en situaciones desafiantes',
                    'medium': 'Balance entre responsabilidades y resultados',
                    'low': 'Énfasis en consistencia y cumplimiento'
                }
            },
            'skills': {
                'adjustment': {
                    'high': 'Destacar habilidades de adaptación y resiliencia',
                    'medium': 'Balance entre habilidades técnicas y blandas',
                    'low': 'Énfasis en habilidades técnicas específicas'
                }
            }
        }
    
    def optimize_cv(
        self,
        cv_data: Dict,
        personality_insights: List[PersonalityInsight],
        derailer_insights: List[DerailerInsight],
        value_insights: List[ValueInsight]
    ) -> CVOptimization:
        """
        Optimiza el CV basado en los insights de personalidad.
        
        Args:
            cv_data: Datos del CV
            personality_insights: Insights de personalidad
            derailer_insights: Insights de derailers
            value_insights: Insights de valores
            
        Returns:
            CVOptimization con las optimizaciones sugeridas
        """
        try:
            # 1. Analizar fortalezas
            strengths = self._analyze_strengths(
                personality_insights,
                derailer_insights,
                value_insights
            )
            
            # 2. Generar keywords
            keywords = self._generate_keywords(
                personality_insights,
                derailer_insights,
                value_insights
            )
            
            # 3. Determinar estilo
            style = self._determine_style(
                personality_insights,
                derailer_insights,
                value_insights
            )
            
            # 4. Optimizar secciones
            sections = self._optimize_sections(
                cv_data,
                personality_insights,
                derailer_insights,
                value_insights
            )
            
            # 5. Generar recomendaciones
            recommendations = self._generate_recommendations(
                cv_data,
                personality_insights,
                derailer_insights,
                value_insights
            )
            
            return CVOptimization(
                strengths=strengths,
                keywords=keywords,
                style=style,
                sections=sections,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error optimizando CV: {str(e)}", exc_info=True)
            return CVOptimization(
                strengths=[],
                keywords=[],
                style={},
                sections={},
                recommendations=[]
            )
    
    def _analyze_strengths(
        self,
        personality_insights: List[PersonalityInsight],
        derailer_insights: List[DerailerInsight],
        value_insights: List[ValueInsight]
    ) -> List[str]:
        """Analiza y extrae fortalezas relevantes."""
        strengths = []
        
        # Fortalezas de personalidad
        for insight in personality_insights:
            if insight.score >= 0.7:
                strengths.extend(self.strength_mapping.get(insight.dimension, []))
        
        # Fortalezas de valores
        for insight in value_insights:
            if insight.score >= 0.7:
                strengths.extend(insight.implications)
        
        # Mitigar derailers como fortalezas
        for insight in derailer_insights:
            if insight.risk_level == 'low':
                strengths.extend(insight.mitigation_strategies)
        
        return list(set(strengths))  # Eliminar duplicados
    
    def _generate_keywords(
        self,
        personality_insights: List[PersonalityInsight],
        derailer_insights: List[DerailerInsight],
        value_insights: List[ValueInsight]
    ) -> List[str]:
        """Genera keywords relevantes para el CV."""
        keywords = []
        
        # Keywords de personalidad
        for insight in personality_insights:
            if insight.score >= 0.7:
                keywords.extend(insight.strengths)
        
        # Keywords de valores
        for insight in value_insights:
            if insight.score >= 0.7:
                keywords.extend([
                    f"{dimension.value}_oriented"
                    for dimension, score in insight.alignment.items()
                    if score >= 0.7
                ])
        
        return list(set(keywords))  # Eliminar duplicados
    
    def _determine_style(
        self,
        personality_insights: List[PersonalityInsight],
        derailer_insights: List[DerailerInsight],
        value_insights: List[ValueInsight]
    ) -> Dict[str, Any]:
        """Determina el estilo óptimo para el CV."""
        style = {
            'tone': 'professional',
            'emphasis': 'experience',
            'format': 'standard'
        }
        
        # Ajustar estilo basado en personalidad
        for insight in personality_insights:
            if insight.score >= 0.7:
                dimension_style = self.style_mapping.get(insight.dimension.value, {})
                if dimension_style:
                    style.update(dimension_style.get('high', {}))
        
        # Ajustar estilo basado en valores
        for insight in value_insights:
            if insight.score >= 0.7:
                if insight.dimension == ValueDimension.RECOGNITION:
                    style['tone'] = 'achievement-focused'
                elif insight.dimension == ValueDimension.POWER:
                    style['format'] = 'impact'
        
        return style
    
    def _optimize_sections(
        self,
        cv_data: Dict,
        personality_insights: List[PersonalityInsight],
        derailer_insights: List[DerailerInsight],
        value_insights: List[ValueInsight]
    ) -> Dict[str, List[str]]:
        """Optimiza las secciones del CV."""
        optimized_sections = {}
        
        # Optimizar cada sección
        for section, content in cv_data.items():
            if section in self.section_optimization:
                section_style = self._get_section_style(
                    section,
                    personality_insights,
                    derailer_insights,
                    value_insights
                )
                
                optimized_sections[section] = self._apply_section_optimization(
                    content,
                    section_style
                )
        
        return optimized_sections
    
    def _get_section_style(
        self,
        section: str,
        personality_insights: List[PersonalityInsight],
        derailer_insights: List[DerailerInsight],
        value_insights: List[ValueInsight]
    ) -> Dict[str, str]:
        """Obtiene el estilo óptimo para una sección."""
        style = {}
        
        # Estilo basado en personalidad
        for insight in personality_insights:
            if insight.score >= 0.7:
                section_style = self.section_optimization.get(section, {}).get(
                    insight.dimension.value, {}
                )
                if section_style:
                    style.update(section_style.get('high', {}))
        
        return style
    
    def _apply_section_optimization(
        self,
        content: List[str],
        style: Dict[str, str]
    ) -> List[str]:
        """Aplica optimizaciones a una sección del CV."""
        optimized_content = []
        
        for item in content:
            # Aplicar estilo
            if 'tone' in style:
                item = self._apply_tone(item, style['tone'])
            
            # Aplicar énfasis
            if 'emphasis' in style:
                item = self._apply_emphasis(item, style['emphasis'])
            
            optimized_content.append(item)
        
        return optimized_content
    
    def _apply_tone(self, content: str, tone: str) -> str:
        """Aplica un tono específico al contenido."""
        tone_mapping = {
            'confident': lambda x: x.replace('managed', 'led').replace('helped', 'drove'),
            'assertive': lambda x: x.replace('participated', 'spearheaded').replace('assisted', 'directed'),
            'professional': lambda x: x.replace('did', 'executed').replace('made', 'developed')
        }
        
        return tone_mapping.get(tone, lambda x: x)(content)
    
    def _apply_emphasis(self, content: str, emphasis: str) -> str:
        """Aplica énfasis específico al contenido."""
        emphasis_mapping = {
            'achievements': lambda x: f"Achieved: {x}",
            'goals': lambda x: f"Goal-oriented: {x}",
            'skills': lambda x: f"Demonstrated skills in: {x}"
        }
        
        return emphasis_mapping.get(emphasis, lambda x: x)(content)
    
    def _generate_recommendations(
        self,
        cv_data: Dict,
        personality_insights: List[PersonalityInsight],
        derailer_insights: List[DerailerInsight],
        value_insights: List[ValueInsight]
    ) -> List[str]:
        """Genera recomendaciones para mejorar el CV."""
        recommendations = []
        
        # Recomendaciones basadas en personalidad
        for insight in personality_insights:
            if insight.score < 0.7:
                recommendations.extend(insight.recommendations)
        
        # Recomendaciones para mitigar derailers
        for insight in derailer_insights:
            if insight.risk_level in ['high', 'medium']:
                recommendations.extend(insight.mitigation_strategies)
        
        # Recomendaciones basadas en valores
        for insight in value_insights:
            if insight.score < 0.7:
                recommendations.extend(insight.implications)
        
        return list(set(recommendations))  # Eliminar duplicados 