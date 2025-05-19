from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class SkillContext:
    """Contexto de una habilidad."""
    source: str  # Fuente de la habilidad (experiencia, educación, etc.)
    confidence: float  # Nivel de confianza en la detección
    context: str  # Texto donde se encontró la habilidad
    timestamp: datetime  # Cuándo se detectó
    metadata: Dict[str, Any]  # Metadatos adicionales

@dataclass
class SkillSource:
    """Fuente de una habilidad."""
    type: str  # Tipo de fuente (experiencia, educación, etc.)
    id: str  # Identificador único de la fuente
    name: str  # Nombre de la fuente
    description: Optional[str] = None  # Descripción opcional
    start_date: Optional[datetime] = None  # Fecha de inicio
    end_date: Optional[datetime] = None  # Fecha de fin

@dataclass
class Skill:
    """Representación de una habilidad."""
    name: str  # Nombre de la habilidad
    category: str  # Categoría (técnica, blanda, etc.)
    level: float  # Nivel de dominio (0-1)
    sources: List[SkillSource]  # Fuentes de la habilidad
    contexts: List[SkillContext]  # Contextos donde aparece
    metadata: Dict[str, Any]  # Metadatos adicionales
    
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
            'sources': [
                {
                    'type': s.type,
                    'id': s.id,
                    'name': s.name,
                    'description': s.description,
                    'start_date': s.start_date.isoformat() if s.start_date else None,
                    'end_date': s.end_date.isoformat() if s.end_date else None
                }
                for s in self.sources
            ],
            'contexts': [
                {
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
            level=data['level'],
            sources=[
                SkillSource(
                    type=s['type'],
                    id=s['id'],
                    name=s['name'],
                    description=s.get('description'),
                    start_date=datetime.fromisoformat(s['start_date']) if s.get('start_date') else None,
                    end_date=datetime.fromisoformat(s['end_date']) if s.get('end_date') else None
                )
                for s in data['sources']
            ],
            contexts=[
                SkillContext(
                    source=c['source'],
                    confidence=c['confidence'],
                    context=c['context'],
                    timestamp=datetime.fromisoformat(c['timestamp']),
                    metadata=c['metadata']
                )
                for c in data['contexts']
            ],
            metadata=data['metadata']
        ) 