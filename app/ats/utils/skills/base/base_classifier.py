from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from app.ats.utils.skills.base.base_models import Skill, Competency, SkillCategory, CompetencyLevel
import logging

logger = logging.getLogger(__name__)

class BaseSkillClassifier(ABC):
    """Clase base abstracta para clasificadores de habilidades."""
    
    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self.business_unit = None
        self.ontology = None
        self.rules = None
    
    @abstractmethod
    def classify_skill(self, skill: Skill) -> Competency:
        """
        Clasifica una habilidad en términos de competencia.
        
        Args:
            skill: Habilidad a clasificar
            
        Returns:
            Competencia clasificada
        """
        pass
    
    @abstractmethod
    def classify_skills(self, skills: List[Skill]) -> List[Competency]:
        """
        Clasifica múltiples habilidades.
        
        Args:
            skills: Lista de habilidades a clasificar
            
        Returns:
            Lista de competencias clasificadas
        """
        pass
        
    def _load_ontology(self, business_unit: str) -> Dict:
        """Carga la ontología específica por BU."""
        self.business_unit = business_unit
        try:
            from app.ats.utils.ontologies import load_ontology
            self.ontology = load_ontology(business_unit)
            return self.ontology
        except ImportError:
            logger.warning(f"Ontología no encontrada para {business_unit}")
            return {}
            
    def _load_rules(self, business_unit: str) -> Dict:
        """Carga reglas de clasificación específicas por BU."""
        self.business_unit = business_unit
        try:
            from app.ats.utils.classification_rules import load_rules
            self.rules = load_rules(business_unit)
            return self.rules
        except ImportError:
            logger.warning(f"Reglas no encontradas para {business_unit}")
            return {}
            
    def _determine_category(self, skill: Skill) -> SkillCategory:
        """Determina la categoría de la habilidad."""
        category = self.ontology.get(skill.name, {}).get('category')
        if category:
            return SkillCategory.from_string(category)
        return SkillCategory.TECHNICAL
        
    def _determine_level(self, skill: Skill) -> CompetencyLevel:
        """Determina el nivel de la competencia."""
        if skill.years_experience and skill.years_experience > 5:
            return CompetencyLevel.EXPERT
        return CompetencyLevel.from_string(skill.level or 'basic')
        
    def _calculate_importance(self, skill: Skill) -> float:
        """Calcula la importancia de la competencia."""
        base_importance = self.rules.get(skill.category, {}).get('importance', 0.5)
        return min(1.0, max(0.1, base_importance + (skill.relevance or 0)))
        
    def _validate_classification(self, competency: Competency) -> bool:
        """Valida la clasificación."""
        if not competency.name:
            return False
            
        if not competency.category:
            return False
            
        return True
