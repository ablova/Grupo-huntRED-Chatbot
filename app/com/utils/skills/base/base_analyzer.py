from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from app.com.utils.skills.base_models.base_models import Skill, Competency, SkillCategory, CompetencyLevel
import logging

logger = logging.getLogger(__name__)

class BaseSkillAnalyzer(ABC):
    """Clase base para analizadores de habilidades y competencias."""

    def __init__(self, business_unit: str):
        """
        Inicializa el analizador.
        
        Args:
            business_unit: Unidad de negocio
        """
        self.business_unit = business_unit
        self.metrics = self._initialize_metrics()
        self.weights = self._load_weights()
        
    @abstractmethod
    async def analyze_skills(self, skills: List[Skill]) -> Dict:
        """Analiza habilidades y genera métricas."""
        pass
        
    @abstractmethod
    async def analyze_competencies(self, competencies: List[Competency]) -> Dict:
        """Analiza competencias y genera métricas."""
        pass
        
    def _initialize_metrics(self) -> Dict:
        """Inicializa métricas de análisis."""
        return {
            'technical': 0.0,
            'soft': 0.0,
            'leadership': 0.0,
            'behavioral': 0.0,
            'cultural': 0.0,
            'strategic': 0.0,
            'executive': 0.0,
            'total': 0.0
        }
        
    def _load_weights(self) -> Dict:
        """Carga pesos específicos por BU."""
        try:
            from app.com.utils.analysis_weights import load_weights
            return load_weights(self.business_unit)
        except ImportError:
            logger.warning(f"Pesos no encontrados para {self.business_unit}")
            return {
                'technical': 0.3,
                'soft': 0.3,
                'leadership': 0.2,
                'behavioral': 0.1,
                'cultural': 0.1
            }
            
    def _calculate_skill_score(self, skill: Skill) -> float:
        """Calcula la puntuación de una habilidad."""
        base_score = self.weights.get(skill.category, 0.1)
        experience_score = min(1.0, skill.years_experience / 10) if skill.years_experience else 0
        relevance_score = skill.relevance or 0
        
        return (base_score + experience_score + relevance_score) / 3
        
    def _calculate_competency_score(self, competency: Competency) -> float:
        """Calcula la puntuación de una competencia."""
        base_score = self.weights.get(competency.category, 0.1)
        importance_score = competency.importance or 0
        
        return (base_score + importance_score) / 2
        
    def _generate_analysis_report(self, metrics: Dict) -> Dict:
        """Genera un reporte de análisis."""
        return {
            'scores': metrics,
            'strengths': self._identify_strengths(metrics),
            'weaknesses': self._identify_weaknesses(metrics),
            'recommendations': self._generate_recommendations(metrics)
        }
        
    def _identify_strengths(self, metrics: Dict) -> List[str]:
        """Identifica fortalezas basadas en métricas."""
        threshold = 0.8
        return [k for k, v in metrics.items() if v >= threshold]
        
    def _identify_weaknesses(self, metrics: Dict) -> List[str]:
        """Identifica debilidades basadas en métricas."""
        threshold = 0.4
        return [k for k, v in metrics.items() if v <= threshold]
        
    def _generate_recommendations(self, metrics: Dict) -> List[str]:
        """Genera recomendaciones basadas en análisis."""
        recommendations = []
        for weakness in self._identify_weaknesses(metrics):
            recommendations.append(f"Desarrollar habilidades en {weakness}")
        return recommendations
