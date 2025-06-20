# app/ml/aura/__init__.py
"""
Sistema Aura - Motor de Inteligencia Artificial Avanzada para Grupo huntRED®

Este módulo implementa el sistema Aura, un motor de IA que analiza la "aura" 
o compatibilidad holística entre candidatos y empresas, proporcionando 
recomendaciones inteligentes basadas en múltiples dimensiones de análisis.
"""

from .core import AuraEngine
from .compatibility_engine import CompatibilityEngine
from .recommendation_engine import RecommendationEngine
from .energy_analyzer import EnergyAnalyzer
from .vibrational_matcher import VibrationalMatcher
from .holistic_assessor import HolisticAssessor
from .aura_metrics import AuraMetrics

__all__ = [
    'AuraEngine',
    'CompatibilityEngine', 
    'RecommendationEngine',
    'EnergyAnalyzer',
    'VibrationalMatcher',
    'HolisticAssessor',
    'AuraMetrics'
]

__version__ = '1.0.0'
__author__ = 'Grupo huntRED® AI Team' 