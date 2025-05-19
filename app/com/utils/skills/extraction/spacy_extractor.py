from app.com.utils.skills.base.base_extractor.base.base_extractor import BaseSkillExtractor
from app.com.utils.skills.base.base_extractor.base.base_models import Skill, SkillSource, SkillContext
import spacy
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class SpacySkillExtractor(BaseSkillExtractor):
    """Extractor de habilidades usando Spacy."""

    def __init__(self, business_unit: str, language: str = 'es'):
        super().__init__(business_unit, language)
        self.nlp = self._load_spacy_model()
        
    def _load_spacy_model(self):
        """Carga el modelo de Spacy."""
        try:
            return spacy.load(f"{self.language}_core_news_md")
        except OSError:
            logger.warning(f"Modelo Spacy no encontrado para {self.language}")
            return spacy.load("es_core_news_md")
            
    async def extract_skills(self, text: str) -> List[Skill]:
        """Extrae habilidades usando Spacy."""
        cache_key = f"spacy_skills_{hash(text)}"
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached
            
        doc = self.nlp(text)
        skills = []
        
        # Extraer habilidades técnicas
        tech_skills = await self._extract_technical_skills(doc)
        skills.extend(tech_skills)
        
        # Extraer habilidades blandas
        soft_skills = await self._extract_soft_skills(doc)
        skills.extend(soft_skills)
        
        # Validar y enriquecer habilidades
        valid_skills = []
        for skill in skills:
            if await self._validate_skill(skill):
                enriched_skill = await self._enrich_skill(skill)
                valid_skills.append(enriched_skill)
                
        # Almacenar en cache
        await self._cache_result(cache_key, valid_skills)
        return valid_skills
        
    async def _extract_technical_skills(self, doc) -> List[Skill]:
        """Extrae habilidades técnicas."""
        skills = []
        for token in doc:
            if token.pos_ in ['NOUN', 'ADJ'] and token.text.lower() in self.patterns['technical']:
                skill = Skill(
                    name=token.text,
                    category=SkillCategory.TECHNICAL.value,
                    source=SkillSource(
                        type='spacy',
                        confidence=0.8,
                        timestamp=datetime.now().isoformat()
                    )
                )
                skills.append(skill)
        return skills
        
    async def _extract_soft_skills(self, doc) -> List[Skill]:
        """Extrae habilidades blandas."""
        skills = []
        for token in doc:
            if token.pos_ in ['NOUN', 'ADJ'] and token.text.lower() in self.patterns['soft']:
                skill = Skill(
                    name=token.text,
                    category=SkillCategory.SOFT.value,
                    source=SkillSource(
                        type='spacy',
                        confidence=0.7,
                        timestamp=datetime.now().isoformat()
                    )
                )
                skills.append(skill)
        return skills
