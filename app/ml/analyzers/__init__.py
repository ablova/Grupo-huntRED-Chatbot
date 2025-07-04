# /home/pablo/app/ml/analyzers/__init__.py
"""
Módulo principal de análisis para Grupo huntRED®.
"""
# Importaciones lazy para evitar problemas de importación circular
def _import_analyzers():
    """Importa los analizadores de forma lazy."""
    from app.ml.analyzers.personality_analyzer import PersonalityAnalyzer
    from app.ml.analyzers.professional_analyzer import ProfessionalAnalyzer
    from app.ml.analyzers.integrated_analyzer import IntegratedAnalyzer
    from app.ml.analyzers.cultural_analyzer import CulturalAnalyzer
    from app.ml.analyzers.talent_analyzer import TalentAnalyzer
    from app.ml.analyzers.salary_analyzer import SalaryAnalyzer
    
    return {
        'PersonalityAnalyzer': PersonalityAnalyzer,
        'ProfessionalAnalyzer': ProfessionalAnalyzer,
        'IntegratedAnalyzer': IntegratedAnalyzer,
        'CulturalAnalyzer': CulturalAnalyzer,
        'TalentAnalyzer': TalentAnalyzer,
        'SalaryAnalyzer': SalaryAnalyzer,
    }

# Importar LinkedInProfileAnalyzer de forma separada para evitar dependencias circulares
try:
    from app.ml.analyzers.linkedin_profile_analyzer import LinkedInProfileAnalyzer
    _LINKEDIN_AVAILABLE = True
except ImportError as e:
    print(f"Warning: LinkedInProfileAnalyzer no disponible: {e}")
    _LINKEDIN_AVAILABLE = False
    LinkedInProfileAnalyzer = None

__all__ = [
    'PersonalityAnalyzer',
    'ProfessionalAnalyzer',
    'IntegratedAnalyzer',
    'CulturalAnalyzer',
    'TalentAnalyzer',
    'SalaryAnalyzer',
    'LinkedInProfileAnalyzer'
]
