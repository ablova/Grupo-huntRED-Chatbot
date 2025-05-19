from app.com.utils.skills.base import *
from app.com.utils.skills.extraction import *
from app.com.utils.skills.classification import *
from app.com.utils.skills.analysis import *
from app.com.utils.skills.validation import *
from app.com.utils.skills.learning import *
from app.com.utils.skills.context import *
from app.com.utils.skills.prediction import *
from app.com.utils.skills.feedback import *
from app.com.utils.skills.recommendation import *
from app.com.utils.skills.role_mapping import *
from app.com.utils.skills.impact_analysis import *

__all__ = [
    # Base
    'BaseSkillExtractor',
    'BaseSkillClassifier',
    'BaseSkillAnalyzer',
    'Skill',
    'Competency',
    'SkillSource',
    'SkillContext',
    'SkillCategory',
    'CompetencyLevel',
    
    # Extractors
    'SpacySkillExtractor',
    'TabiyaSkillExtractor',
    
    # Classifiers
    'ExecutiveSkillClassifier',
    
    # Analyzers
    'ExecutiveSkillAnalyzer',
    
    # Other components
    'SkillValidator',
    'SkillEnricher',
    'ContextManager',
    'TrendPredictor',
    'FeedbackSystem',
    'ResourceRecommender',
    'RoleMapper',
    'ImpactAnalyzer'
]

def create_skill_processor(business_unit: str, language: str = 'es', mode: str = 'executive') -> BaseSkillAnalyzer:
    """
    Crea un procesador de habilidades configurado para el modo especificado.
    
    Args:
        business_unit: Unidad de negocio
        language: Idioma del procesamiento
        mode: Modo de procesamiento ('executive', 'technical', 'general')
        
    Returns:
        Un procesador de habilidades configurado
    """
    if mode == 'executive':
        extractor = TabiyaSkillExtractor(business_unit, language)
        classifier = ExecutiveSkillClassifier(business_unit)
        analyzer = ExecutiveSkillAnalyzer(business_unit)
    else:
        extractor = SpacySkillExtractor(business_unit, language)
        classifier = BaseSkillClassifier(business_unit)
        analyzer = BaseSkillAnalyzer(business_unit)
        
    return analyzer
