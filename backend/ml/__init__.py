"""
🚀 GhuntRED-v2 ML Module
Machine Learning System with GenIA and AURA
"""

from .core.factory import MLFactory
from .core.exceptions import MLException, ModelNotFound, ValidationError

__version__ = "2.0.0"
__all__ = ["MLFactory", "MLException", "ModelNotFound", "ValidationError"]

# Initialize ML Factory
ml_factory = MLFactory()

def get_analyzer(analyzer_type: str):
    """Get analyzer instance"""
    return ml_factory.get_analyzer(analyzer_type)

def analyze_candidate(candidate_data: dict, analysis_type: str = "full"):
    """Convenience function for candidate analysis"""
    return ml_factory.analyze_candidate(candidate_data, analysis_type)