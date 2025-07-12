"""
Módulo de Matchmaking - Sistema de emparejamiento inteligente.

Este módulo implementa el sistema de matchmaking con separación clara de responsabilidades:

- factors.py: Configuración y estructura de factores
- factors_model.py: Modelos de machine learning
- matchmaking.py: Lógica principal de matchmaking

Estructura recomendada:
├── factors.py          # Configuración y pesos de factores
├── factors_model.py    # Modelos ML (requiere PyTorch)
├── matchmaking.py      # Lógica principal
└── __init__.py         # Este archivo
"""

# Importaciones de configuración (siempre disponibles)
from .factors import (
    Factor,
    FactorCategory,
    MatchmakingFactors
)

# Importaciones condicionales de ML
try:
    from .factors_model import (
        FactorsMatchmakingModel,
        FactorsEmbedder,
        FactorsEvaluator
    )
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    # Placeholder classes para cuando ML no está disponible
    class FactorsMatchmakingModel:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch no está disponible. Instala torch para usar modelos ML.")
    
    class FactorsEmbedder:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch no está disponible. Instala torch para usar embedders.")
    
    class FactorsEvaluator:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch no está disponible. Instala torch para usar evaluators.")

# Importaciones principales
try:
    from .matchmaking import MatchmakingModel, MatchmakingEmbedder
except ImportError:
    # Placeholder si matchmaking.py no existe
    class MatchmakingModel:
        pass
    
    class MatchmakingEmbedder:
        pass

__all__ = [
    # Configuración
    'Factor',
    'FactorCategory', 
    'MatchmakingFactors',
    
    # Modelos ML (condicionales)
    'FactorsMatchmakingModel',
    'FactorsEmbedder',
    'FactorsEvaluator',
    
    # Lógica principal
    'MatchmakingModel',
    'MatchmakingEmbedder',
    
    # Estado
    'ML_AVAILABLE'
] 