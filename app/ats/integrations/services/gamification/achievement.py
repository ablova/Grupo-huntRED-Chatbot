# app/ats/integrations/services/gamification/achievement.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class Achievement:
    id: str
    name: str
    description: str
    points: int
    icon: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = field(default_factory=dict)
    rewards: Optional[Dict[str, Any]] = field(default_factory=dict)
    rarity: Optional[str] = None
    unlocked_at: Optional[datetime] = None
    is_hidden: bool = False
    category: str = "general"
    type: Any = None  # Añadido para compatibilidad con AchievementType enum
    created_at: datetime = field(default_factory=datetime.now) 