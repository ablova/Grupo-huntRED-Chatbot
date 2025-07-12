# app/ats/feedback/__init__.py
"""
Módulo de feedback para el sistema ATS de Grupo huntRED®.

Este módulo maneja la recopilación, procesamiento y análisis de retroalimentación
de clientes en diferentes etapas del ciclo de servicio.
"""

from .feedback_models import (
    ServiceFeedback, OngoingServiceFeedback, CompletedServiceFeedback,
    ServiceImprovementSuggestion
)

from .ongoing_tracker import get_ongoing_service_tracker
from .completion_tracker import get_service_completion_tracker

# Constantes para etapas de feedback
FEEDBACK_STAGES = [
    ('proposal', 'Propuesta'),
    ('ongoing', 'Servicio en Curso'),
    ('completed', 'Servicio Completado'),
    ('skills', 'Análisis de Skills')
]

# Tipos de servicio
SERVICE_TYPES = [
    ('recruitment', 'Reclutamiento'),
    ('assessment', 'Evaluación'),
    ('consulting', 'Consultoría'),
    ('training', 'Capacitación'),
    ('verification', 'Verificación'),
    ('analysis', 'Análisis'),
    ('other', 'Otro')
]

def get_feedback_tracker(stage):
    """
    Obtiene el tracker apropiado según la etapa de feedback.
    
    Args:
        stage (str): Etapa del feedback ('ongoing', 'completed', 'proposal')
        
    Returns:
        Tracker: Instancia del tracker correspondiente
    """
    if stage == 'ongoing':
        return get_ongoing_service_tracker()
    elif stage == 'completed':
        return get_service_completion_tracker()
    elif stage == 'proposal':
        from .proposal_tracker import get_proposal_tracker
        return get_proposal_tracker()
    else:
        raise ValueError(f"Etapa de feedback no válida: {stage}")

# Importar señales para que se conecten automáticamente
from . import signals 