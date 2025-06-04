# /home/pablo/app/ml/analyzers/__init__.py
"""
Módulo principal de análisis para Grupo huntRED®.
"""
from app.ml.analyzers.personality_analyzer import PersonalityAnalyzer
from app.ml.analyzers.professional_analyzer import ProfessionalAnalyzer
from app.ml.analyzers.integrated_analyzer import IntegratedAnalyzer
from app.ml.analyzers.cultural_analyzer import CulturalAnalyzer
from app.ml.analyzers.talent_analyzer import TalentAnalyzer
from app.ml.analyzers.salary_analyzer import SalaryAnalyzer

__all__ = [
    'PersonalityAnalyzer',
    'ProfessionalAnalyzer',
    'IntegratedAnalyzer',
    'CulturalAnalyzer',
    'TalentAnalyzer',
    'SalaryAnalyzer'
]
