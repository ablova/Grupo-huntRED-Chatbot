# app/ml/aura/models/__init__.py
"""
Modelos de Machine Learning para AURA - Inicializador del paquete
"""

# Importar y exponer las clases principales
from app.ml.aura.models.gnn_models import (
    ProfessionalNetworkGNN,
    CommunityDetectionGNN,
    InfluenceAnalysisGNN,
    GNNTrainer,
    GNNAnalyzer,
    GNNModels
)

# Exportar las clases para que estén disponibles al importar desde app.ml.aura.models
__all__ = [
    'ProfessionalNetworkGNN',
    'CommunityDetectionGNN',
    'InfluenceAnalysisGNN',
    'GNNTrainer',
    'GNNAnalyzer',
    'GNNModels'
]
