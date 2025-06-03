from app.ats.utils.skills.base.base_extractor import BaseSkillExtractor
from app.ats.utils.skills.base.base_models import Skill, SkillSource, SkillContext
from app.ats.utils.tabiya import TabiyaNLPAdapter
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class TabiyaSkillExtractor(BaseSkillExtractor):
    """Extractor de habilidades usando Tabiya."""

    def __init__(self, business_unit: str, language: str = 'es'):
        super().__init__(business_unit, language)
        self.tabiya = TabiyaNLPAdapter(business_unit)
        
    async def extract_skills(self, text: str) -> List[Skill]:
        """Extrae habilidades usando Tabiya."""
        cache_key = f"tabiya_skills_{hash(text)}"
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
            
        try:
            # Usar Tabiya para análisis profundo
            analysis = await self.tabiya.analyze(text)
            skills = []
            
            # Procesar habilidades técnicas
            tech_skills = await self._process_technical_skills(analysis)
            skills.extend(tech_skills)
            
            # Procesar habilidades blandas
            soft_skills = await self._process_soft_skills(analysis)
            skills.extend(soft_skills)
            
            # Procesar competencias
            competencies = await self._process_competencies(analysis)
            skills.extend(competencies)
            
            # Validar y enriquecer habilidades
            valid_skills = []
            for skill in skills:
                if await self._validate_skill(skill):
                    enriched_skill = await self._enrich_skill(skill)
                    valid_skills.append(enriched_skill)
                    
            # Almacenar en cache
            await self._cache_result(cache_key, valid_skills)
            return valid_skills
            
        except Exception as e:
            logger.error(f"Error en Tabiya: {str(e)}")
            return []
            
    async def _process_technical_skills(self, analysis: Dict) -> List[Skill]:
        """Procesa habilidades técnicas de análisis."""
        skills = []
        for skill in analysis.get('technical_skills', []):
            skill_obj = Skill(
                name=skill['name'],
                category=SkillCategory.TECHNICAL.value,
                level=skill.get('level'),
                years_experience=skill.get('experience'),
                source=SkillSource(
                    type='tabiya',
                    confidence=skill.get('confidence', 0.9),
                    timestamp=datetime.now().isoformat(),
                    evidence=skill.get('evidence')
                )
            )
            skills.append(skill_obj)
        return skills
        
    async def _process_soft_skills(self, analysis: Dict) -> List[Skill]:
        """Procesa habilidades blandas de análisis."""
        skills = []
        for skill in analysis.get('soft_skills', []):
            skill_obj = Skill(
                name=skill['name'],
                category=SkillCategory.SOFT.value,
                level=skill.get('level'),
                source=SkillSource(
                    type='tabiya',
                    confidence=skill.get('confidence', 0.8),
                    timestamp=datetime.now().isoformat(),
                    evidence=skill.get('evidence')
                )
            )
            skills.append(skill_obj)
        return skills
        
    async def _process_competencies(self, analysis: Dict) -> List[Skill]:
        """Procesa competencias de análisis."""
        skills = []
        for competency in analysis.get('competencies', []):
            skill_obj = Skill(
                name=competency['name'],
                category=competency['category'],
                level=competency.get('level'),
                source=SkillSource(
                    type='tabiya',
                    confidence=competency.get('confidence', 0.9),
                    timestamp=datetime.now().isoformat(),
                    evidence=competency.get('evidence')
                )
            )
            skills.append(skill_obj)
        return skills
