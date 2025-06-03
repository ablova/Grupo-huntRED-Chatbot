# /home/pablo/app/com/utils/skills/base/base_extractor.py
"""
Clase base para extractores de habilidades.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from app.ats.utils.skills.base.base_models import Skill, SkillSource, SkillContext
import logging

logger = logging.getLogger(__name__)

class BaseSkillExtractor(ABC):
    """Clase base abstracta para extractores de habilidades."""
    
    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
    
    @abstractmethod
    def extract_skills(self, text: str, source: Optional[SkillSource] = None) -> List[Skill]:
        """
        Extrae habilidades de un texto.
        
        Args:
            text: Texto del que extraer habilidades
            source: Fuente opcional de las habilidades
            
        Returns:
            Lista de habilidades extraídas
        """
        pass
    
    def create_skill_context(self, text: str, source: SkillSource) -> SkillContext:
        """
        Crea un contexto de habilidad.
        
        Args:
            text: Texto del contexto
            source: Fuente del contexto
            
        Returns:
            Contexto de habilidad creado
        """
        return SkillContext(text=text, source=source)

    def _initialize_cache(self):
        """Inicializa el sistema de cache."""
        try:
            from app.ats.utils.redis_cache import RedisCache
            return RedisCache()
        except ImportError:
            logger.warning("RedisCache no disponible, usando cache en memoria")
            return {}
            
    def _load_patterns(self) -> Dict:
        """Carga patrones específicos por BU."""
        try:
            from app.ats.utils.patterns import load_patterns
            return load_patterns(self.business_unit)
        except ImportError:
            logger.warning(f"Patrones no encontrados para {self.business_unit}")
            return {}
            
    async def _validate_skill(self, skill: Skill) -> bool:
        """Valida la habilidad extraída."""
        if not skill.name:
            return False
            
        if len(skill.name) < 2:
            return False
            
        return True
            
    async def _enrich_skill(self, skill: Skill) -> Skill:
        """Enriquece la habilidad con contexto y metadatos."""
        skill.context = SkillContext(
            business_unit=self.business_unit
        )
        return skill
        
    async def _cache_result(self, key: str, value: List[Skill], ttl: int = 3600):
        """Almacena resultado en cache."""
        if isinstance(self.cache, dict):
            self.cache[key] = value
        else:
            await self.cache.set(key, value, ttl)
            
    async def _get_cached_result(self, key: str) -> Optional[List[Skill]]:
        """Obtiene resultado de cache."""
        if isinstance(self.cache, dict):
            return self.cache.get(key)
        else:
            return await self.cache.get(key)
