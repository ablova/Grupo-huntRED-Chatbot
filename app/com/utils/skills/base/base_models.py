from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum
import json

@dataclass
class SkillSource:
    """Origen de la habilidad."""
    type: str  # 'cv', 'linkedin', 'manual'
    confidence: float
    timestamp: str
    evidence: Optional[List[str]] = None

@dataclass
class SkillContext:
    """Contexto de la habilidad."""
    business_unit: Optional[str] = None
    industry: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    team: Optional[str] = None
    project: Optional[str] = None
    duration: Optional[str] = None

@dataclass
class Skill:
    """Modelo de habilidad."""
    name: str
    category: str
    level: Optional[str] = None
    years_experience: Optional[int] = None
    source: SkillSource = None
    context: SkillContext = None
    relevance: Optional[float] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'category': self.category,
            'level': self.level,
            'years_experience': self.years_experience,
            'source': self.source,
            'context': self.context,
            'relevance': self.relevance,
            'metadata': self.metadata
        }

@dataclass
class Competency:
    """Modelo de competencia."""
    name: str
    category: str
    level: Optional[str] = None
    importance: Optional[float] = None
    source: Optional[str] = None
    evidence: Optional[List[str]] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'category': self.category,
            'level': self.level,
            'importance': self.importance,
            'source': self.source,
            'evidence': self.evidence,
            'metadata': self.metadata
        }

class SkillCategory(Enum):
    """Categorías de habilidades."""
    TECHNICAL = 'technical'
    SOFT = 'soft'
    LEADERSHIP = 'leadership'
    BEHAVIORAL = 'behavioral'
    CULTURAL = 'cultural'
    STRATEGIC = 'strategic'
    EXECUTIVE = 'executive'

    @classmethod
    def from_string(cls, value: str) -> 'SkillCategory':
        try:
            return cls[value.upper()]
        except KeyError:
            return cls.TECHNICAL

class CompetencyLevel(Enum):
    """Niveles de competencia."""
    BASIC = 'basic'
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
            return cls.BASIC
