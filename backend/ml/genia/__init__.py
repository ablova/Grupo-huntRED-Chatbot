"""
🤖 GenIA v2.0 - Generative Intelligence Analyzer
Advanced ML system for candidate analysis and matching
"""

from .analyzer import GenIAAnalyzer
from .sentiment import SentimentAnalyzer
from .personality import PersonalityAnalyzer
from .skills import SkillsExtractor
from .matching import MatchingEngine

__version__ = "2.0.0"

__all__ = [
    'GenIAAnalyzer',
    'SentimentAnalyzer', 
    'PersonalityAnalyzer',
    'SkillsExtractor',
    'MatchingEngine',
]

# GenIA Module - ML for Job Matching and Skills Analysis