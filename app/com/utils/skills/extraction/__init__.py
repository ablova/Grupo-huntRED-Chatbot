"""Módulo de extracción de habilidades."""

from app.com.utils.skills.extraction.tabiya_extractor import TabiyaSkillExtractor
from app.com.utils.skills.extraction.spacy_extractor import SpacySkillExtractor

__all__ = [
    'TabiyaSkillExtractor',
    'SpacySkillExtractor'
] 