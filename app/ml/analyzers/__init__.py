# /home/pablo/app/ml/analyzers/__init__.py
"""
Módulo principal de análisis para Grupo huntRED®.
"""

# Importaciones directas para evitar problemas de importación circular
try:
    from app.ml.analyzers.personality_analyzer import PersonalityAnalyzer
except ImportError as e:
    print(f"Warning: PersonalityAnalyzer no disponible: {e}")
    PersonalityAnalyzer = None

try:
    from app.ml.analyzers.professional_analyzer import ProfessionalAnalyzer
except ImportError as e:
    print(f"Warning: ProfessionalAnalyzer no disponible: {e}")
    ProfessionalAnalyzer = None

try:
    from app.ml.analyzers.integrated_analyzer import IntegratedAnalyzer
except ImportError as e:
    print(f"Warning: IntegratedAnalyzer no disponible: {e}")
    IntegratedAnalyzer = None

try:
    from app.ml.analyzers.cultural_analyzer import CulturalAnalyzer
except ImportError as e:
    print(f"Warning: CulturalAnalyzer no disponible: {e}")
    CulturalAnalyzer = None

try:
    from app.ml.analyzers.talent_analyzer import TalentAnalyzer
except ImportError as e:
    print(f"Warning: TalentAnalyzer no disponible: {e}")
    TalentAnalyzer = None

try:
    from app.ml.analyzers.salary_analyzer import SalaryAnalyzer
except ImportError as e:
    print(f"Warning: SalaryAnalyzer no disponible: {e}")
    SalaryAnalyzer = None

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
