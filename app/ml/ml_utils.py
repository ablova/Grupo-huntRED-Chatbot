# app/ml/ml_utils.py
"""
Utilidades para cálculos y algoritmos de Machine Learning.

Este módulo contiene funciones auxiliares utilizadas por varios componentes 
del sistema de machine learning, especialmente para análisis de matchmaking.
"""

import logging
from typing import Dict, Any, List, Union, Optional, Tuple
import math

logger = logging.getLogger(__name__)

def calculate_match_percentage(
    required_skills: List[str], 
    candidate_skills: List[str], 
    required_weight: float = 1.5, 
    bonus_weight: float = 0.5
) -> float:
    """
    Calcula el porcentaje de coincidencia entre habilidades requeridas y habilidades del candidato.
    
    Args:
        required_skills: Lista de habilidades requeridas
        candidate_skills: Lista de habilidades del candidato
        required_weight: Peso para las habilidades requeridas (por defecto 1.5)
        bonus_weight: Peso para habilidades adicionales del candidato (por defecto 0.5)
        
    Returns:
        Porcentaje de coincidencia (0-100)
    """
    if not required_skills:
        return 100.0  # Si no hay habilidades requeridas, coincidencia perfecta
        
    # Normalizar las habilidades (convertir a minúsculas para comparación)
    required_skills_norm = [s.lower().strip() for s in required_skills if s]
    candidate_skills_norm = [s.lower().strip() for s in candidate_skills if s]
    
    if not required_skills_norm:
        return 100.0
        
    # Contar coincidencias
    matches = sum(1 for skill in required_skills_norm if skill in candidate_skills_norm)
    
    # Calcular porcentaje base basado en habilidades requeridas
    base_percentage = (matches / len(required_skills_norm)) * 100 * required_weight
    
    # Calcular bonus por habilidades adicionales relevantes
    bonus = 0
    if candidate_skills_norm and required_skills_norm:
        additional_skills = [s for s in candidate_skills_norm if s not in required_skills_norm]
        bonus = min(25, (len(additional_skills) / len(required_skills_norm)) * 100 * bonus_weight)
    
    # Combinar y limitar a 100%
    total_percentage = min(100, base_percentage + bonus)
    
    return round(total_percentage, 2)

def calculate_alignment_percentage(
    expected_value: Union[float, int], 
    actual_value: Union[float, int], 
    tolerance: float = 0.2, 
    max_diff: float = 0.5
) -> float:
    """
    Calcula el porcentaje de alineación entre dos valores numéricos (ej. salarios).
    
    Args:
        expected_value: Valor esperado o ideal
        actual_value: Valor real o propuesto
        tolerance: Tolerancia para considerar alineación perfecta (por defecto 0.2 o 20%)
        max_diff: Diferencia máxima para calcular alineación parcial (por defecto 0.5 o 50%)
        
    Returns:
        Porcentaje de alineación (0-100)
    """
    if expected_value == 0:
        if actual_value == 0:
            return 100.0
        return 0.0
        
    # Calcular diferencia relativa
    diff = abs(expected_value - actual_value) / expected_value
    
    # Si está dentro de la tolerancia, consideramos alineación perfecta
    if diff <= tolerance:
        return 100.0
        
    # Si excede la diferencia máxima, no hay alineación
    if diff >= max_diff:
        return 0.0
        
    # Calcular alineación parcial de forma lineal entre tolerance y max_diff
    alignment = 100 * (1 - ((diff - tolerance) / (max_diff - tolerance)))
    
    return round(max(0, min(100, alignment)), 2)

def calculate_culture_fit(
    company_values: List[str], 
    candidate_values: List[str]
) -> float:
    """
    Calcula la compatibilidad cultural entre los valores de la empresa y del candidato.
    
    Args:
        company_values: Lista de valores o principios de la empresa
        candidate_values: Lista de valores o principios del candidato
        
    Returns:
        Puntuación de compatibilidad cultural (0-100)
    """
    if not company_values or not candidate_values:
        return 50.0  # Valor neutral si no hay información suficiente
    
    # Normalizar valores
    company_values_norm = [v.lower().strip() for v in company_values if v]
    candidate_values_norm = [v.lower().strip() for v in candidate_values if v]
    
    if not company_values_norm or not candidate_values_norm:
        return 50.0
    
    # Calcular coincidencias directas
    direct_matches = sum(1 for v in company_values_norm if v in candidate_values_norm)
    
    # Factor de coincidencia directa (60% del total)
    direct_score = (direct_matches / len(company_values_norm)) * 60
    
    # Calcular factor de diversidad (40% del total)
    # Más valores únicos del candidato dan una mayor puntuación
    unique_values = len(set(candidate_values_norm))
    diversity_score = min(40, (unique_values / max(1, len(company_values_norm))) * 40)
    
    total_score = direct_score + diversity_score
    
    return round(min(100, total_score), 2)
