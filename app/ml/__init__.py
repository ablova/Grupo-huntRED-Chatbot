# /home/pablo/app/ml/__init__.py

"""
🚀 Sistema de Machine Learning Revolucionario para Grupo huntRED®

Módulo principal con importaciones optimizadas y sistema de carga lazy
para mejor rendimiento y mantenibilidad.

Versión: 2.0.0 - Optimizada
"""

import logging
from typing import Optional, Dict, Any

# Configurar logging básico
logger = logging.getLogger(__name__)

# ============================================================================
# LAZY IMPORTS - Para mejor rendimiento de startup
# ============================================================================

def _lazy_import_aura():
    """Importación lazy del motor AURA"""
    try:
        from app.ml.aura.aura import AuraEngine
        return AuraEngine
    except ImportError as e:
        logger.warning(f"AURA Engine no disponible: {e}")
        return None

def _lazy_import_analyzers():
    """Importación lazy de analizadores"""
    analyzers = {}
    try:
        from app.ml.analyzers.personality_analyzer import PersonalityAnalyzer
        from app.ml.analyzers.cultural_analyzer import CulturalAnalyzer
        from app.ml.analyzers.professional_analyzer import ProfessionalAnalyzer
        from app.ml.analyzers.integrated_analyzer import IntegratedAnalyzer
        from app.ml.analyzers.talent_analyzer import TalentAnalyzer
        from app.ml.analyzers.salary_analyzer import SalaryAnalyzer
        
        analyzers.update({
            'PersonalityAnalyzer': PersonalityAnalyzer,
            'CulturalAnalyzer': CulturalAnalyzer,
            'ProfessionalAnalyzer': ProfessionalAnalyzer,
            'IntegratedAnalyzer': IntegratedAnalyzer,
            'TalentAnalyzer': TalentAnalyzer,
            'SalaryAnalyzer': SalaryAnalyzer,
        })
    except ImportError as e:
        logger.warning(f"Algunos analizadores no disponibles: {e}")
    
    return analyzers

def _lazy_import_core():
    """Importación lazy de componentes core"""
    core = {}
    try:
        from app.ml.core.unified_config import get_config
        from app.ml.core.exceptions import MLBaseException
        from app.ml.core.validation import validate_input
        
        core.update({
            'get_config': get_config,
            'MLBaseException': MLBaseException,
            'validate_input': validate_input,
        })
    except ImportError as e:
        logger.warning(f"Componentes core no disponibles: {e}")
    
    return core

def _lazy_import_processors():
    """Importación lazy de procesadores"""
    processors = {}
    try:
        from app.ml.onboarding_processor import OnboardingProcessor
        from app.ml.sentiment_analyzer import SentimentAnalyzer
        from app.ml.communication_optimizer import CommunicationOptimizer
        
        processors.update({
            'OnboardingProcessor': OnboardingProcessor,
            'SentimentAnalyzer': SentimentAnalyzer,
            'CommunicationOptimizer': CommunicationOptimizer,
        })
    except ImportError as e:
        logger.warning(f"Algunos procesadores no disponibles: {e}")
    
    return processors

# ============================================================================
# SYSTEM FACTORY - Para creación optimizada de componentes
# ============================================================================

class MLComponentFactory:
    """Factory para crear componentes ML de forma optimizada"""
    
    def __init__(self):
        self._analyzers_cache = {}
        self._processors_cache = {}
        self._core_cache = {}
    
    def get_analyzer(self, analyzer_type: str):
        """Obtiene analizador con cache"""
        if analyzer_type not in self._analyzers_cache:
            analyzers = _lazy_import_analyzers()
            if analyzer_type in analyzers:
                self._analyzers_cache[analyzer_type] = analyzers[analyzer_type]()
            else:
                raise ValueError(f"Analizador {analyzer_type} no disponible")
        
        return self._analyzers_cache[analyzer_type]
    
    def get_processor(self, processor_type: str):
        """Obtiene procesador con cache"""
        if processor_type not in self._processors_cache:
            processors = _lazy_import_processors()
            if processor_type in processors:
                self._processors_cache[processor_type] = processors[processor_type]()
            else:
                raise ValueError(f"Procesador {processor_type} no disponible")
        
        return self._processors_cache[processor_type]
    
    def get_aura_engine(self):
        """Obtiene motor AURA"""
        AuraEngine = _lazy_import_aura()
        if AuraEngine:
            return AuraEngine()
        else:
            raise RuntimeError("AURA Engine no disponible")

# ============================================================================
# GLOBAL FACTORY INSTANCE
# ============================================================================

_factory: Optional[MLComponentFactory] = None

def get_ml_factory() -> MLComponentFactory:
    """Obtiene instancia global del factory (Singleton)"""
    global _factory
    if _factory is None:
        _factory = MLComponentFactory()
    return _factory

# ============================================================================
# CONVENIENCE FUNCTIONS - Para compatibilidad hacia atrás
# ============================================================================

def get_sentiment_analyzer():
    """Obtiene analizador de sentimientos"""
    return get_ml_factory().get_processor('SentimentAnalyzer')

def get_onboarding_processor():
    """Obtiene procesador de onboarding"""
    return get_ml_factory().get_processor('OnboardingProcessor')

def get_personality_analyzer():
    """Obtiene analizador de personalidad"""
    return get_ml_factory().get_analyzer('PersonalityAnalyzer')

def get_aura_engine():
    """Obtiene motor AURA"""
    return get_ml_factory().get_aura_engine()

# ============================================================================
# SYSTEM STATUS
# ============================================================================

def get_system_status() -> Dict[str, Any]:
    """Obtiene estado del sistema ML"""
    status = {
        'version': '2.0.0',
        'status': 'OPTIMIZED',
        'components': {
            'aura': False,
            'analyzers': False,
            'processors': False,
            'core': False
        },
        'performance': {
            'lazy_loading': True,
            'caching': True,
            'factory_pattern': True
        }
    }
    
    # Verificar disponibilidad de componentes
    try:
        _lazy_import_aura()
        status['components']['aura'] = True
    except:
        pass
    
    try:
        _lazy_import_analyzers()
        status['components']['analyzers'] = True
    except:
        pass
    
    try:
        _lazy_import_processors()
        status['components']['processors'] = True
    except:
        pass
    
    try:
        _lazy_import_core()
        status['components']['core'] = True
    except:
        pass
    
    return status

# ============================================================================
# EXPORTS OPTIMIZADOS
# ============================================================================

__all__ = [
    # Factory
    'MLComponentFactory',
    'get_ml_factory',
    
    # Convenience functions
    'get_sentiment_analyzer',
    'get_onboarding_processor', 
    'get_personality_analyzer',
    'get_aura_engine',
    
    # System
    'get_system_status',
]

# ============================================================================
# VERSION & METADATA
# ============================================================================

__version__ = '2.0.0'
__author__ = 'Grupo huntRED® AI Team'
__description__ = 'Sistema de ML Optimizado con Lazy Loading'

logger.info(f"🚀 ML System {__version__} inicializado con lazy loading")

# Mostrar estado del sistema al importar
system_status = get_system_status()
logger.info(f"📊 Componentes disponibles: {sum(system_status['components'].values())}/4")
