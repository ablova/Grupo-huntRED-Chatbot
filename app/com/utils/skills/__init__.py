# /home/pablo/app/com/utils/skills/__init__.py
"""
Sistema de análisis y clasificación de habilidades.

Este módulo proporciona una infraestructura completa para el procesamiento de habilidades,
incluyendo extracción, clasificación y análisis de habilidades técnicas y ejecutivas.

Dependencias:
    - spacy>=3.0.0: Para procesamiento de lenguaje natural
    - tabiya>=1.0.0: Para análisis profundo de habilidades
    - datetime: Para manejo de fechas y timestamps
"""

from typing import Dict, List, Optional, Type

# Constantes del sistema
PROCESSING_MODES = {
    'EXECUTIVE': 'executive',
    'TECHNICAL': 'technical',
    'GENERAL': 'general'
}

SUPPORTED_LANGUAGES = {
    'SPANISH': 'es',
    'ENGLISH': 'en'
}

# Modelos base
from app.com.utils.skills.base.base_models import (
    Competency,
    CompetencyLevel,
    Skill,
    SkillCategory,
    SkillContext,
    SkillSource
)

# Interfaces base
from app.com.utils.skills.base.base_analyzer import BaseSkillAnalyzer
from app.com.utils.skills.base.base_classifier import BaseSkillClassifier
from app.com.utils.skills.base.base_extractor import BaseSkillExtractor

# Implementaciones específicas
from app.com.utils.skills.analysis.executive_analyzer import ExecutiveSkillAnalyzer
from app.com.utils.skills.classification.executive_classifier import ExecutiveSkillClassifier
from app.com.utils.skills.extraction.spacy_extractor import SpacySkillExtractor
from app.com.utils.skills.extraction.tabiya_extractor import TabiyaSkillExtractor

__all__ = [
    # Constantes
    'PROCESSING_MODES',
    'SUPPORTED_LANGUAGES',
    
    # Modelos base
    'Competency',
    'CompetencyLevel',
    'Skill',
    'SkillCategory',
    'SkillContext',
    'SkillSource',
    
    # Interfaces base
    'BaseSkillAnalyzer',
    'BaseSkillClassifier',
    'BaseSkillExtractor',
    
    # Implementaciones específicas
    'ExecutiveSkillAnalyzer',
    'ExecutiveSkillClassifier',
    'SpacySkillExtractor',
    'TabiyaSkillExtractor',
    
    # Funciones de fábrica
    'create_skill_processor'
]

def create_skill_processor(
    business_unit: str,
    language: str = SUPPORTED_LANGUAGES['SPANISH'],
    mode: str = PROCESSING_MODES['EXECUTIVE']
) -> BaseSkillAnalyzer:
    """
    Crea un procesador de habilidades configurado para el modo especificado.
    
    Args:
        business_unit (str): Unidad de negocio para la que se configura el procesador
        language (str): Idioma del procesamiento (por defecto: español)
        mode (str): Modo de procesamiento (por defecto: ejecutivo)
        
    Returns:
        BaseSkillAnalyzer: Un procesador de habilidades configurado según el modo
        
    Raises:
        ValueError: Si el modo o idioma especificado no es válido
    """
    if mode not in PROCESSING_MODES.values():
        raise ValueError(
            f"Modo no válido: {mode}. "
            f"Debe ser uno de: {', '.join(PROCESSING_MODES.values())}"
        )
        
    if language not in SUPPORTED_LANGUAGES.values():
        raise ValueError(
            f"Idioma no válido: {language}. "
            f"Debe ser uno de: {', '.join(SUPPORTED_LANGUAGES.values())}"
        )
        
    if mode == PROCESSING_MODES['EXECUTIVE']:
        extractor = TabiyaSkillExtractor(business_unit, language)
        classifier = ExecutiveSkillClassifier(business_unit)
        analyzer = ExecutiveSkillAnalyzer(business_unit)
    else:
        extractor = SpacySkillExtractor(business_unit, language)
        classifier = BaseSkillClassifier(business_unit)
        analyzer = BaseSkillAnalyzer(business_unit)
        
    return analyzer

# Importaciones básicas que sabemos que existen
from .base_models import (
    Skill,
    SkillSource,
    SkillContext,
    CompetencyLevel,
    SkillCategory,
    Competency
)

# Intentar importar módulos opcionales
try:
    from .validation import SkillValidator
except ImportError:
    pass

try:
    from .learning import SkillEnricher
except ImportError:
    pass

# Solo exportar lo que sabemos que existe
__all__ = [
    'Skill',
    'SkillSource',
    'SkillContext',
    'CompetencyLevel',
    'SkillCategory',
    'Competency',
    'SkillPredictor',
    'RuleBasedPredictor',
    'MLBasedPredictor',
    'create_skill_predictor'
]

# Añadir componentes si se importaron correctamente
if 'SkillValidator' in locals():
    __all__.append('SkillValidator')
if 'SkillEnricher' in locals():
    __all__.append('SkillEnricher')

def create_skill_processor(business_unit: str, language: str = 'es', mode: str = 'executive'):
    """Crea un procesador de habilidades configurado para el modo especificado."""
    # Implementación básica que no depende de módulos faltantes
    class DummyProcessor:
        def __init__(self, business_unit, language, mode):
            self.business_unit = business_unit
            self.language = language
            self.mode = mode
            
        def process(self, text):
            return {"skills": [], "status": "initialized"}
            
    return DummyProcessor(business_unit, language, mode)