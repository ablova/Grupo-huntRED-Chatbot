# /home/pablo/app/com/utils/skills/validation/__init__.py
"""
Validation module for skills processing.

This module provides functionality for validating skills data.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from app.com.utils.skills.base.base_models import Skill, Competency

class SkillValidator:
    """Validates skill data and ensures data integrity."""
    
    def __init__(self, min_confidence: float = 0.5):
        """Initialize the validator with minimum confidence threshold."""
        self.min_confidence = min_confidence
    
    def validate_skill(self, skill: Skill) -> bool:
        """Validate a single skill."""
        if not skill.name or not isinstance(skill.name, str):
            return False
            
        if not 0 <= skill.level <= 1:
            return False
            
        # Add more validation rules as needed
        return True
    
    def validate_competency(self, competency: Competency) -> bool:
        """Validate a competency with its associated skills."""
        if not competency.name or not isinstance(competency.name, str):
            return False
            
        if not competency.skills:
            return False
            
        return all(self.validate_skill(skill) for skill in competency.skills)

# Export the validator class
__all__ = ['SkillValidator']
