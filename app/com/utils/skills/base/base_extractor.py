from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from app.com.utils.skills.base_models.base_models import Skill, SkillSource, SkillContext
import logging

logger = logging.getLogger(__name__)

class BaseSkillExtractor(ABC):
    """Clase base para extractores de habilidades."""

    def __init__(self, business_unit: str, language: str = 'es'):
        """
        Inicializa el extractor de habilidades.
        
        Args:
            business_unit: Unidad de negocio
            language: Idioma del procesamiento
        """
        self.business_unit = business_unit
        self.language = language
        self.cache = self._initialize_cache()
        self.patterns = self._load_patterns()
        
    @abstractmethod
    async def extract_skills(self, text: str) -> List[Skill]:
        """Extrae habilidades del texto."""
        pass
        
    def _initialize_cache(self):
        """Inicializa el sistema de cache."""
        try:
            from app.com.utils.redis_cache import RedisCache
            return RedisCache()
        except ImportError:
            logger.warning("RedisCache no disponible, usando cache en memoria")
            return {}
            
    def _load_patterns(self) -> Dict:
        """Carga patrones específicos por BU."""
        try:
            from app.com.utils.patterns import load_patterns
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
