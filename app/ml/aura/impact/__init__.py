"""
AURA - Impact Analysis Module
Módulo especializado en análisis de impacto social y sostenibilidad.
"""

from .impact_analyzer import ImpactAnalyzer
from .sustainability_calculator import SustainabilityCalculator
import logging

logger = logging.getLogger(__name__)

__all__ = [
    'ImpactAnalyzer',
    'SustainabilityCalculator'
]
