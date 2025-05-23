# /home/pablo/app/ml/ml_utils.py
"""
Bridge module to provide backward compatibility for ml functions.
Implementa un sistema flexible de matchmaking para diferentes business units.
"""

from typing import List, Dict, Any, Optional, Union
from app.ml.utils.utils import MLUtils
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Cache global para instancias de MLUtils por business_unit_id
_ml_utils_instances = {}

def _get_ml_utils(business_unit_id=None):
    """
    Obtiene o crea una instancia de MLUtils para una business unit específica.
    Usa cache para evitar crear múltiples instancias.
    
    Args:
        business_unit_id: ID de la unidad de negocio. Si es None, se usa una predeterminada.
        
    Returns:
        Instancia de MLUtils configurada para la business unit especificada.
    """
    global _ml_utils_instances
    
    # Convertir a string para uso como clave
    cache_key = str(business_unit_id) if business_unit_id else "default"
    
    if cache_key not in _ml_utils_instances:
        _ml_utils_instances[cache_key] = MLUtils(business_unit_id)
        
    return _ml_utils_instances[cache_key]


def calculate_match_percentage(candidate_skills: List[str], 
                             required_skills: List[str], 
                             business_unit_id: Optional[int] = None,
                             use_classification: bool = True) -> float:
    """
    Calcula el porcentaje de coincidencia entre habilidades usando múltiples sistemas.
    
    Args:
        candidate_skills: Lista de habilidades del candidato
        required_skills: Lista de habilidades requeridas
        use_classification: Si usar el sistema de clasificación de habilidades
        
    Returns:
        float: Porcentaje de coincidencia (0-100)
    """
    ml_utils = _get_ml_utils(business_unit_id)
    return ml_utils.calculate_skill_match(
        candidate_skills=candidate_skills,
        required_skills=required_skills,
        use_classification=use_classification
    )

def calculate_alignment_percentage(candidate_data, vacancy_data, business_unit_id=None, weights=None):
    """
    Calcula el porcentaje de alineación entre un candidato y una vacante.
    
    Args:
        candidate_data: Datos del candidato
        vacancy_data: Datos de la vacante
        business_unit_id: ID de la unidad de negocio para contextualizar el análisis
        weights: Pesos para diferentes criterios de alineación
        
    Returns:
        float: Porcentaje de alineación (0-100)
    """
    # Obtener la instancia de MLUtils para la business unit especificada
    ml_utils = _get_ml_utils(business_unit_id)
    
    # Use MLUtils if it has the method
    if hasattr(ml_utils, 'calculate_alignment'):
        return ml_utils.calculate_alignment(candidate_data, vacancy_data, weights)
    
    # Basic fallback implementation
    # This is a simplified version - ideally this should be implemented in MLUtils
    import logging
    logging.getLogger(__name__).warning(
        "Using fallback calculate_alignment_percentage implementation. "
        "Consider updating MLUtils class with this method."
    )
    
    # Default weights if none provided
    if weights is None:
        weights = {
            'skills': 0.4,
            'experience': 0.3,
            'education': 0.2,
            'location': 0.1
        }
    
    # Calculate weighted score (basic implementation)
    total_score = 0.0
    total_weight = sum(weights.values())
    
    # Normalize weights
    normalized_weights = {k: v/total_weight for k, v in weights.items()}
    
    # Calculate weighted scores for each criterion
    if 'skills' in normalized_weights and 'skills' in candidate_data and 'skills' in vacancy_data:
        skill_match = ml_utils.calculate_skill_match(
            candidate_data['skills'], 
            vacancy_data['skills']
        )
        total_score += skill_match * normalized_weights['skills']
    
    # Implementar lógica específica de BU basado en business_unit_id
    # Por ejemplo, para huntRED podríamos evaluar experiencia gerencial
    # Para huntU podríamos evaluar nivel académico, etc.
    
    return min(max(total_score, 0), 100)
