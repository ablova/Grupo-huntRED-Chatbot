from app.com.utils.skills.base.base_analyzer import BaseSkillAnalyzer
from app.com.utils.skills.base.base_models import Skill, Competency, SkillCategory, CompetencyLevel
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ExecutiveSkillAnalyzer(BaseSkillAnalyzer):
    """Analizador de habilidades y competencias para roles ejecutivos."""

    def __init__(self, business_unit: str):
        super().__init__(business_unit)
        self.executive_weights = self._load_executive_weights()
        self.executive_metrics = self._initialize_executive_metrics()
        
    def _load_executive_weights(self) -> Dict:
        """Carga pesos específicos para roles ejecutivos."""
        return {
            'strategic': 0.35,
            'leadership': 0.3,
            'board_relations': 0.15,
            'vision': 0.1,
            'cultural': 0.1
        }
        
    def _initialize_executive_metrics(self) -> Dict:
        """Inicializa métricas específicas para roles ejecutivos."""
        return {
            'strategic': 0.0,
            'leadership': 0.0,
            'board_relations': 0.0,
            'vision': 0.0,
            'cultural': 0.0,
            'executive': 0.0,
            'total': 0.0
        }
        
    async def analyze_skills(self, skills: List[Skill]) -> Dict:
        """Analiza habilidades para roles ejecutivos."""
        metrics = self._initialize_executive_metrics()
        
        for skill in skills:
            score = self._calculate_executive_skill_score(skill)
            metrics[skill.category] += score
            metrics['total'] += score
            
        return self._generate_analysis_report(metrics)
        
    async def analyze_competencies(self, competencies: List[Competency]) -> Dict:
        """Analiza competencias para roles ejecutivos."""
        metrics = self._initialize_executive_metrics()
        
        for competency in competencies:
            score = self._calculate_executive_competency_score(competency)
            metrics[competency.category] += score
            metrics['total'] += score
            
        return self._generate_analysis_report(metrics)
        
    def _calculate_executive_skill_score(self, skill: Skill) -> float:
        """Calcula puntuación ejecutiva para habilidades."""
        base_score = self.executive_weights.get(skill.category, 0.1)
        experience_score = min(1.0, skill.years_experience / 15) if skill.years_experience else 0
        relevance_score = skill.source.confidence if skill.source.confidence else 0
        
        return (base_score + experience_score + relevance_score) / 3
        
    def _calculate_executive_competency_score(self, competency: Competency) -> float:
        """Calcula puntuación ejecutiva para competencias."""
        base_score = self.executive_weights.get(competency.category, 0.1)
        importance_score = competency.importance if competency.importance else 0
        evidence_score = len(competency.evidence) / 5 if competency.evidence else 0
        
        return (base_score + importance_score + evidence_score) / 3
        
    def _generate_analysis_report(self, metrics: Dict) -> Dict:
        """Genera reporte de análisis ejecutivo."""
        report = super()._generate_analysis_report(metrics)
        
        # Añadir métricas ejecutivas específicas
        report['executive_metrics'] = {
            'strategic_alignment': self._calculate_strategic_alignment(metrics),
            'leadership_potential': self._calculate_leadership_potential(metrics),
            'board_readiness': self._calculate_board_readiness(metrics)
        }
        
        return report
        
    def _calculate_strategic_alignment(self, metrics: Dict) -> float:
        """Calcula alineación estratégica."""
        strategic_score = metrics.get('strategic', 0)
        vision_score = metrics.get('vision', 0)
        
        return (strategic_score + vision_score) / 2
        
    def _calculate_leadership_potential(self, metrics: Dict) -> float:
        """Calcula potencial de liderazgo."""
        leadership_score = metrics.get('leadership', 0)
        cultural_score = metrics.get('cultural', 0)
        
        return (leadership_score + cultural_score) / 2
        
    def _calculate_board_readiness(self, metrics: Dict) -> float:
        """Calcula preparación para directorio."""
        board_score = metrics.get('board_relations', 0)
        executive_score = metrics.get('executive', 0)
        
        return (board_score + executive_score) / 2
