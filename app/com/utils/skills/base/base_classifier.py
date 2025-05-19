from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from app.com.utils.skills.base.base_models import Skill, Competency, SkillCategory, CompetencyLevel
import logging

logger = logging.getLogger(__name__)

class BaseSkillClassifier(ABC):
    """Clase base para clasificadores de habilidades."""

    def __init__(self, business_unit: str):
        """
        Inicializa el clasificador de habilidades.
        
        Args:
            business_unit: Unidad de negocio
        """
        self.business_unit = business_unit
        self.ontology = self._load_ontology()
        self.rules = self._load_rules()
        
    @abstractmethod
    async def classify_skills(self, skills: List[Skill]) -> List[Competency]:
        """Clasifica habilidades en competencias."""
        pass
        
    def _load_ontology(self) -> Dict:
        """Carga la ontología específica por BU."""
        try:
            from app.com.utils.ontologies import load_ontology
            return load_ontology(self.business_unit)
        except ImportError:
            logger.warning(f"Ontología no encontrada para {self.business_unit}")
            return {}
            
    def _load_rules(self) -> Dict:
        """Carga reglas de clasificación específicas por BU."""
        try:
            from app.com.utils.classification_rules import load_rules
            return load_rules(self.business_unit)
        except ImportError:
            logger.warning(f"Reglas no encontradas para {self.business_unit}")
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
