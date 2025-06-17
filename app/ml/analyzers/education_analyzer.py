"""
Analyzer para evaluación de educación y prestigio académico.
"""
from typing import Dict, List, Optional, Any
import logging
import numpy as np
from datetime import datetime

from app.ml.core.models.education.university import UniversityModel
from app.ml.core.models.education.program import ProgramModel
from app.ml.core.utils.matchmaking import _get_ml_utils

logger = logging.getLogger(__name__)

class EducationAnalyzer:
    """Analyzer para evaluar la educación y prestigio académico."""
    
    def __init__(self):
        """Inicializa el analyzer de educación."""
        self.university_model = UniversityModel()
        self.program_model = ProgramModel()
        self.ml_utils = _get_ml_utils()
        
    def analyze_education(self, 
                         education_data: List[Dict[str, Any]],
                         weights: Optional[Dict[str, float]] = None) -> float:
        """
        Analiza la educación del candidato.
        
        Args:
            education_data: Lista de diccionarios con datos educativos
            weights: Pesos para cada nivel educativo
            
        Returns:
            Score final de educación (0-1)
        """
        if not education_data:
            return 0.0
            
        weights = weights or {
            'undergraduate': 0.4,
            'graduate': 0.4,
            'phd': 0.2
        }
        
        scores = []
        for edu in education_data:
            # Obtener scores base
            university_score = self.university_model.get_final_score(
                edu['university']
            )
            program_score = self.program_model.get_final_score(
                edu['university'],
                edu['program']
            )
            
            # Combinar scores
            level_weight = weights.get(edu['level'], 0.0)
            combined_score = (university_score * 0.4 + program_score * 0.6) * level_weight
            
            scores.append(combined_score)
            
        # Promedio ponderado
        return sum(scores) / len(scores) if scores else 0.0
        
    def update_models(self, 
                     historical_data: List[Dict[str, Any]]) -> None:
        """
        Actualiza los modelos con datos históricos.
        
        Args:
            historical_data: Lista de diccionarios con datos históricos
        """
        for data in historical_data:
            # Actualizar modelo de universidad
            self.university_model.update_weights(
                university=data['university'],
                success_rate=data['success_rate'],
                confidence=data['confidence']
            )
            
            # Actualizar modelo de programa
            self.program_model.update_weights(
                university=data['university'],
                program=data['program'],
                success_rate=data['success_rate'],
                confidence=data['confidence']
            )
            
    def get_education_features(self, 
                             education_data: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extrae features para ML de los datos educativos.
        
        Args:
            education_data: Lista de diccionarios con datos educativos
            
        Returns:
            Array de features
        """
        features = []
        for edu in education_data:
            # Features básicas
            edu_features = [
                self.university_model.get_final_score(edu['university']),
                self.program_model.get_final_score(edu['university'], edu['program']),
                1.0 if edu['level'] == 'phd' else 0.0,
                1.0 if edu['level'] == 'graduate' else 0.0,
                1.0 if edu['level'] == 'undergraduate' else 0.0
            ]
            features.extend(edu_features)
            
        return np.array(features) 