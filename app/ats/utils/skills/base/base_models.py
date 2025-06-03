# /home/pablo/app/com/utils/skills/base/base_models.py
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Dict, Any, Set
from datetime import datetime

@dataclass
class SkillContext:
    """Contexto de una habilidad."""
    business_unit: Optional[str] = None
    industry: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    team: Optional[str] = None
    project: Optional[str] = None
    duration: Optional[str] = None
    source: str = ""  # Fuente de la habilidad (experiencia, educación, etc.)
    confidence: float = 0.0  # Nivel de confianza en la detección
    context: str = ""  # Texto donde se encontró la habilidad
    timestamp: datetime = field(default_factory=datetime.now)  # Cuándo se detectó
    metadata: Dict[str, Any] = field(default_factory=dict)  # Metadatos adicionales

@dataclass
class SkillSource:
    """Fuente de una habilidad."""
    type: str  # Tipo de fuente (experiencia, educación, etc.)
    id: str  # Identificador único de la fuente
    name: str  # Nombre de la fuente
    description: Optional[str] = None  # Descripción opcional
    start_date: Optional[datetime] = None  # Fecha de inicio
    end_date: Optional[datetime] = None  # Fecha de fin
    confidence: float = 0.0  # Nivel de confianza
    evidence: Optional[List[str]] = None  # Evidencia de la habilidad

@dataclass
class Skill:
    """Representación de una habilidad."""
    name: str  # Nombre de la habilidad
    category: str  # Categoría (técnica, blanda, etc.)
    level: float = 0.0  # Nivel de dominio (0-1)
    years_experience: Optional[int] = None  # Años de experiencia
    sources: List[SkillSource] = field(default_factory=list)  # Fuentes de la habilidad
    contexts: List[SkillContext] = field(default_factory=list)  # Contextos donde aparece
    relevance: Optional[float] = None  # Relevancia de la habilidad
    metadata: Dict[str, Any] = field(default_factory=dict)  # Metadatos adicionales
    
    def add_context(self, context: SkillContext) -> None:
        """Añade un nuevo contexto a la habilidad."""
        self.contexts.append(context)
        
    def add_source(self, source: SkillSource) -> None:
        """Añade una nueva fuente a la habilidad."""
        self.sources.append(source)
        
    def update_level(self, new_level: float) -> None:
        """Actualiza el nivel de dominio."""
        self.level = max(0.0, min(1.0, new_level))
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la habilidad a un diccionario."""
        return {
            'name': self.name,
            'category': self.category,
            'level': self.level,
            'years_experience': self.years_experience,
            'relevance': self.relevance,
            'sources': [
                {
                    'type': s.type,
                    'id': s.id,
                    'name': s.name,
                    'description': s.description,
                    'start_date': s.start_date.isoformat() if s.start_date else None,
                    'end_date': s.end_date.isoformat() if s.end_date else None,
                    'confidence': s.confidence,
                    'evidence': s.evidence
                }
                for s in self.sources
            ],
            'contexts': [
                {
                    'business_unit': c.business_unit,
                    'industry': c.industry,
                    'company': c.company,
                    'role': c.role,
                    'team': c.team,
                    'project': c.project,
                    'duration': c.duration,
                    'source': c.source,
                    'confidence': c.confidence,
                    'context': c.context,
                    'timestamp': c.timestamp.isoformat(),
                    'metadata': c.metadata
                }
                for c in self.contexts
            ],
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Skill':
        """Crea una habilidad desde un diccionario."""
        return cls(
            name=data['name'],
            category=data['category'],
            level=data.get('level', 0.0),
            years_experience=data.get('years_experience'),
            relevance=data.get('relevance'),
            sources=[
                SkillSource(
                    type=s['type'],
                    id=s['id'],
                    name=s['name'],
                    description=s.get('description'),
                    start_date=datetime.fromisoformat(s['start_date']) if s.get('start_date') else None,
                    end_date=datetime.fromisoformat(s['end_date']) if s.get('end_date') else None,
                    confidence=s.get('confidence', 0.0),
                    evidence=s.get('evidence')
                )
                for s in data.get('sources', [])
            ],
            contexts=[
                SkillContext(
                    business_unit=c.get('business_unit'),
                    industry=c.get('industry'),
                    company=c.get('company'),
                    role=c.get('role'),
                    team=c.get('team'),
                    project=c.get('project'),
                    duration=c.get('duration'),
                    source=c.get('source', ''),
                    confidence=c.get('confidence', 0.0),
                    context=c.get('context', ''),
                    timestamp=datetime.fromisoformat(c['timestamp']) if c.get('timestamp') else datetime.now(),
                    metadata=c.get('metadata', {})
                )
                for c in data.get('contexts', [])
            ],
            metadata=data.get('metadata', {})
        )

class CompetencyLevel(Enum):
    """Niveles de competencia."""
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    EXPERT = 'expert'
    LEADERSHIP = 'leadership'
    EXECUTIVE = 'executive'

    @classmethod
    def from_string(cls, value: str) -> 'CompetencyLevel':
        try:
            return cls[value.upper()]
        except KeyError:
            return cls.BEGINNER

class SkillCategory(Enum):
    """Categorías de habilidades."""
    TECHNICAL = 'technical'
    SOFT = 'soft'
    LANGUAGE = 'language'
    CERTIFICATION = 'certification'

    @classmethod
    def from_string(cls, value: str) -> 'SkillCategory':
        try:
            return cls[value.upper()]
        except KeyError:
            return cls.TECHNICAL

@dataclass
class Competency:
    """Representa una competencia con sus habilidades asociadas."""
    name: str  # Nombre de la competencia
    description: str  # Descripción detallada
    category: SkillCategory  # Categoría de la competencia
    level: CompetencyLevel  # Nivel de competencia
    importance: Optional[float] = None  # Importancia de la competencia
    source: Optional[str] = None  # Fuente de la competencia
    evidence: Optional[List[str]] = None  # Evidencia de la competencia
    skills: Set[str] = field(default_factory=set)  # Habilidades relacionadas
    metadata: Dict[str, Any] = field(default_factory=dict)  # Metadatos adicionales
    
    def add_skill(self, skill_name: str) -> None:
        """Añade una habilidad a la competencia."""
        self.skills.add(skill_name)
        
    def remove_skill(self, skill_name: str) -> bool:
        """Elimina una habilidad de la competencia."""
        if skill_name in self.skills:
            self.skills.remove(skill_name)
            return True
        return False
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la competencia a un diccionario."""
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'level': self.level.value,
            'importance': self.importance,
            'source': self.source,
            'evidence': self.evidence,
            'skills': list(self.skills),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Competency':
        """Crea una competencia desde un diccionario."""
        return cls(
            name=data['name'],
            description=data['description'],
            category=SkillCategory.from_string(data['category']),
            level=CompetencyLevel.from_string(data['level']),
            importance=data.get('importance'),
            source=data.get('source'),
            evidence=data.get('evidence'),
            skills=set(data.get('skills', [])),
            metadata=data.get('metadata', {})
        )
