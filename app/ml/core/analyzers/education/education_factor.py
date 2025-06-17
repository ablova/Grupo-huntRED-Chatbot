"""
Factor que usa el analyzer de educación.
"""
from typing import Dict, List, Optional, Any, Union
import numpy as np
from ...models.matchmaking.factors.analyzer_factors import AnalyzerBasedFactor
from .education_analyzer import EducationAnalyzer

class EducationFactor(AnalyzerBasedFactor):
    """Factor que usa el analyzer de educación."""
    
    def __init__(self,
                 analyzer: EducationAnalyzer,
                 product_type: str = 'huntred',
                 weights: Optional[Dict[str, float]] = None):
        """
        Inicializa el factor de educación.
        
        Args:
            analyzer: Analyzer de educación
            product_type: Tipo de producto
            weights: Pesos personalizados
        """
        super().__init__(
            name='education',
            analyzer_type='education',
            product_type=product_type,
            weights=weights
        )
        self.analyzer: EducationAnalyzer = analyzer
        
        # Pesos por defecto según producto
        self.default_weights: Dict[str, Dict[str, float]] = {
            'huntred': {
                'university_score': 0.4,
                'program_score': 0.3,
                'experience_match': 0.2,
                'skills_match': 0.1
            },
            'executive': {
                'university_score': 0.5,
                'program_score': 0.3,
                'experience_match': 0.15,
                'skills_match': 0.05
            },
            'huntu': {
                'university_score': 0.3,
                'program_score': 0.3,
                'experience_match': 0.2,
                'skills_match': 0.2
            }
        }
        
        # Usar pesos personalizados o los por defecto
        self.weights: Dict[str, float] = weights or self.default_weights.get(product_type, self.default_weights['huntred'])
        
    def get_analyzer_metrics(self,
                           candidate_data: Dict[str, Any],
                           job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene métricas del analyzer.
        
        Args:
            candidate_data: Datos del candidato
            job_data: Datos del trabajo
            
        Returns:
            Métricas del analyzer
        """
        return self.analyzer.analyze(candidate_data, job_data)
        
    def _calculate_weighted_score(self,
                                metrics: Dict[str, Any]) -> float:
        """
        Calcula el score ponderado.
        
        Args:
            metrics: Métricas del analyzer
            
        Returns:
            Score ponderado (0-1)
        """
        return (
            metrics['university']['score'] * self.weights['university_score'] +
            metrics['program']['score'] * self.weights['program_score'] +
            metrics['experience']['score'] * self.weights['experience_match'] +
            metrics['skills']['score'] * self.weights['skills_match']
        )
        
    def _generate_recommendations(self,
                                metrics: Dict[str, Any]) -> List[str]:
        """
        Genera recomendaciones basadas en las métricas.
        
        Args:
            metrics: Métricas del analyzer
            
        Returns:
            Lista de recomendaciones
        """
        recommendations: List[str] = []
        
        # Umbrales según producto
        thresholds: Dict[str, Dict[str, float]] = {
            'huntred': {
                'university': 0.7,
                'program': 0.7,
                'experience': 0.8,
                'skills': 0.8
            },
            'executive': {
                'university': 0.8,
                'program': 0.8,
                'experience': 0.9,
                'skills': 0.9
            },
            'huntu': {
                'university': 0.6,
                'program': 0.6,
                'experience': 0.7,
                'skills': 0.7
            }
        }
        
        threshold: Dict[str, float] = thresholds.get(self.product_type, thresholds['huntred'])
        
        # Verificar score de universidad
        if metrics['university']['score'] < threshold['university']:
            if self.product_type == 'executive':
                recommendations.append(
                    "Considerar candidatos de universidades top-tier"
                )
            elif self.product_type == 'huntu':
                recommendations.append(
                    "Considerar candidatos de universidades acreditadas"
                )
            else:
                recommendations.append(
                    "Considerar candidatos de universidades mejor rankeadas"
                )
                
        # Verificar score de programa
        if metrics['program']['score'] < threshold['program']:
            if self.product_type == 'executive':
                recommendations.append(
                    "Considerar candidatos con programas de élite"
                )
            elif self.product_type == 'huntu':
                recommendations.append(
                    "Considerar candidatos con programas relevantes"
                )
            else:
                recommendations.append(
                    "Considerar candidatos con programas más alineados"
                )
                
        # Verificar experiencia
        if metrics['experience']['score'] < threshold['experience']:
            if self.product_type == 'executive':
                recommendations.append(
                    "Considerar candidatos con experiencia ejecutiva"
                )
            elif self.product_type == 'huntu':
                recommendations.append(
                    "Considerar candidatos con experiencia básica"
                )
            else:
                recommendations.append(
                    "Considerar candidatos con más experiencia"
                )
                
        # Verificar habilidades
        if metrics['skills']['score'] < threshold['skills']:
            missing_skills: List[str] = metrics['skills']['missing']
            if missing_skills:
                if self.product_type == 'executive':
                    recommendations.append(
                        f"Considerar candidatos con habilidades ejecutivas en: {', '.join(missing_skills)}"
                    )
                else:
                    recommendations.append(
                        f"Considerar candidatos con habilidades en: {', '.join(missing_skills)}"
                    )
                    
        return recommendations 