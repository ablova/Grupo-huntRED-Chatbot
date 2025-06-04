# /home/pablo/app/ml/__init__.py

# This file makes the ml directory a Python package

"""
Módulo principal de Machine Learning para Grupo huntRED®.
"""
from app.ml.core.models.base import (
    BaseMLModel,
    MatchmakingModel,
    TransitionModel,
    MarketAnalysisModel
)

# Importar analizadores individualmente para evitar problemas de importación circular
from app.ml.analyzers.personality_analyzer import PersonalityAnalyzer
from app.ml.analyzers.cultural_analyzer import CulturalAnalyzer
from app.ml.analyzers.professional_analyzer import ProfessionalAnalyzer
from app.ml.analyzers.integrated_analyzer import IntegratedAnalyzer
from app.ml.analyzers.talent_analyzer import TalentAnalyzer
from app.ml.analyzers.salary_analyzer import SalaryAnalyzer

__all__ = [
    'BaseMLModel',
    'MatchmakingModel',
    'TransitionModel',
    'MarketAnalysisModel',
    'PersonalityAnalyzer',
    'CulturalAnalyzer',
    'ProfessionalAnalyzer',
    'IntegratedAnalyzer',
    'TalentAnalyzer',
    'SalaryAnalyzer'
]
