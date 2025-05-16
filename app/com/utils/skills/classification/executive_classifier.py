from ..base.base_classifier import BaseSkillClassifier
from ..base.base_models import Skill, Competency, SkillCategory, CompetencyLevel
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ExecutiveSkillClassifier(BaseSkillClassifier):
    """Clasificador de habilidades específico para huntRED® Executive."""

    def __init__(self, business_unit: str):
        super().__init__(business_unit)
        self.executive_rules = self._load_executive_rules()
        
    def _load_executive_rules(self) -> Dict:
        """Carga reglas específicas para roles ejecutivos."""
        return {
            'strategic': {
                'importance': 0.9,
                'evidence_required': True,
                'min_experience': 10
            },
            'leadership': {
                'importance': 0.85,
                'evidence_required': True,
                'min_examples': 3
            },
            'board_relations': {
                'importance': 0.8,
                'evidence_required': True,
                'min_projects': 2
            },
            'vision': {
                'importance': 0.9,
                'evidence_required': True,
                'min_duration': '5Y'
            }
        }
        
    async def classify_skills(self, skills: List[Skill]) -> List[Competency]:
        """Clasifica habilidades para roles ejecutivos."""
        competencies = []
        
        for skill in skills:
            competency = await self._classify_executive_skill(skill)
            if competency:
                competencies.append(competency)
                
        return competencies
        
    async def _classify_executive_skill(self, skill: Skill) -> Optional[Competency]:
        """Clasifica habilidad específica para roles ejecutivos."""
        # Validar requisitos ejecutivos
        if not await self._validate_executive_requirements(skill):
            return None
            
        # Determinar categoría ejecutiva
        category = self._determine_executive_category(skill)
        
        # Determinar nivel ejecutivo
        level = self._determine_executive_level(skill)
        
        # Calcular importancia
        importance = self._calculate_executive_importance(skill)
        
        return Competency(
            name=skill.name,
            category=category,
            level=level,
            importance=importance,
            source='executive_classifier',
            evidence=skill.source.evidence,
            metadata={
                'experience': skill.years_experience,
                'confidence': skill.source.confidence
            }
        )
        
    async def _validate_executive_requirements(self, skill: Skill) -> bool:
        """Valida requisitos específicos para roles ejecutivos."""
        rules = self.executive_rules.get(skill.category, {})
        
        # Validar experiencia mínima
        if rules.get('min_experience') and skill.years_experience:
            if skill.years_experience < rules['min_experience']:
                return False
                
        # Validar evidencia
        if rules.get('evidence_required'):
            if not skill.source.evidence or len(skill.source.evidence) < rules.get('min_examples', 1):
                return False
                
        return True
        
    def _determine_executive_category(self, skill: Skill) -> str:
        """Determina categoría ejecutiva."""
        base_category = self._determine_category(skill)
        
        # Ajustar categoría para roles ejecutivos
        if base_category == SkillCategory.TECHNICAL:
            return 'executive_technical'
        elif base_category == SkillCategory.LEADERSHIP:
            return 'executive_leadership'
        elif base_category == SkillCategory.STRATEGIC:
            return 'executive_strategic'
            
        return base_category.value
        
    def _determine_executive_level(self, skill: Skill) -> CompetencyLevel:
        """Determina nivel ejecutivo."""
        # Ajustar nivel para roles ejecutivos
        if skill.years_experience and skill.years_experience > 10:
            return CompetencyLevel.EXECUTIVE
        elif skill.years_experience and skill.years_experience > 5:
            return CompetencyLevel.LEADERSHIP
            
        return self._determine_level(skill)
        
    def _calculate_executive_importance(self, skill: Skill) -> float:
        """Calcula importancia para roles ejecutivos."""
        base_importance = self.rules.get(skill.category, {}).get('importance', 0.5)
        executive_weight = 0.2 if skill.category in ['strategic', 'leadership'] else 0.1
        
        return min(1.0, base_importance + executive_weight + (skill.source.confidence or 0))
