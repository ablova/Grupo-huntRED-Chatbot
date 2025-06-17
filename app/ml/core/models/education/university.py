"""
Modelo para el análisis y evaluación de universidades.
"""
from typing import Dict, List, Optional, Any
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from .qs_ranking import QSRankingModel
from .program_ranking import ProgramRankingModel
from .data_loader import EducationDataLoader

class UniversityModel(BaseEstimator, TransformerMixin):
    """Modelo para evaluar el prestigio y calidad de universidades."""
    
    def __init__(self, 
                 data_loader: Optional[EducationDataLoader] = None,
                 ml_weights: Optional[Dict[str, float]] = None,
                 cost_multipliers: Optional[Dict[str, float]] = None,
                 ranking_weights: Optional[Dict[str, float]] = None):
        """
        Inicializa el modelo de universidades.
        
        Args:
            data_loader: Cargador de datos
            ml_weights: Pesos para ajustes ML por universidad
            cost_multipliers: Multiplicadores por nivel de costo
            ranking_weights: Pesos por ranking
        """
        self.data_loader = data_loader or EducationDataLoader()
        self.ml_weights = ml_weights or {}
        self.cost_multipliers = cost_multipliers or {
            '$': 1.0,      # Públicas
            '$$': 1.1,     # Privadas económicas
            '$$$': 1.2,    # Privadas medias
            '$$$$': 1.3    # Privadas premium/internacionales
        }
        self.ranking_weights = ranking_weights or {
            'top_10': 1.0,
            'top_25': 0.9,
            'top_50': 0.8,
            'top_100': 0.7,
            'top_500': 0.6,
            'others': 0.5
        }
        self.confidence_scores = {}
        self.qs_model = QSRankingModel()
        self.program_model = ProgramRankingModel()
        
    def load_data(self, file_path: str) -> None:
        """
        Carga datos desde Excel.
        
        Args:
            file_path: Ruta al archivo Excel
        """
        self.data_loader.load_university_data(file_path)
        self.data_loader.load_program_data(file_path)
        
        # Actualizar modelos con datos cargados
        self.program_model.program_rankings = self.data_loader.get_program_data()
        
    def _get_ranking_weight(self, ranking: int) -> float:
        """Obtiene el peso según el ranking de la universidad."""
        if ranking <= 10:
            return self.ranking_weights['top_10']
        elif ranking <= 25:
            return self.ranking_weights['top_25']
        elif ranking <= 50:
            return self.ranking_weights['top_50']
        elif ranking <= 100:
            return self.ranking_weights['top_100']
        elif ranking <= 500:
            return self.ranking_weights['top_500']
        return self.ranking_weights['others']
        
    def _get_cost_multiplier(self, cost: str) -> float:
        """Obtiene el multiplicador según el costo."""
        return self.cost_multipliers.get(cost, 1.0)
        
    def _is_specialty(self, university: str, program: str) -> bool:
        """Verifica si el programa es especialidad de la universidad."""
        metrics = self.data_loader.get_university_metrics(university)
        if not metrics:
            return False
        return program in metrics.get('specialties', [])
        
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'UniversityModel':
        """
        Entrena el modelo con datos históricos.
        
        Args:
            X: Features de universidades
            y: Target (éxito de candidatos)
        """
        # Implementar lógica de entrenamiento
        return self
        
    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transforma los datos de entrada.
        
        Args:
            X: Features de universidades
            
        Returns:
            Array con scores transformados
        """
        # Implementar lógica de transformación
        return X
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predice el score de prestigio.
        
        Args:
            X: Features de universidades
            
        Returns:
            Array con scores predichos
        """
        # Implementar lógica de predicción
        return np.zeros(len(X))
        
    def update_weights(self, 
                      university: str, 
                      success_rate: float, 
                      confidence: float) -> None:
        """
        Actualiza los pesos ML para una universidad.
        
        Args:
            university: Nombre de la universidad
            success_rate: Tasa de éxito de candidatos
            confidence: Nivel de confianza en la actualización
        """
        if university not in self.ml_weights:
            self.ml_weights[university] = 0.0
            self.confidence_scores[university] = 0.0
            
        # Actualizar peso con factor de confianza
        self.ml_weights[university] = (
            self.ml_weights[university] * (1 - confidence) +
            success_rate * confidence
        )
        self.confidence_scores[university] = confidence
        
    def get_final_score(self, 
                       university: str, 
                       program: Optional[str] = None) -> float:
        """
        Obtiene el score final combinando base y ML.
        
        Args:
            university: Nombre de la universidad
            program: Nombre del programa (opcional)
            
        Returns:
            Score final (0-1)
        """
        # Obtener métricas de la universidad
        metrics = self.data_loader.get_university_metrics(university)
        if not metrics:
            return 0.5  # Score neutral por defecto
            
        # Obtener datos base
        base_score = metrics['score']
        ranking = metrics['ranking']
        cost = metrics['cost']
        
        # Obtener datos QS si están disponibles
        qs_rank = metrics['qs_rank']
        qs_score = metrics['qs_score']
        
        # Calcular multiplicadores
        ranking_weight = self._get_ranking_weight(ranking)
        cost_multiplier = self._get_cost_multiplier(cost)
        
        # Bonus por especialidad
        specialty_bonus = 0.1 if program and self._is_specialty(university, program) else 0.0
        
        # Bonus por internacional
        international_bonus = 0.1 if metrics.get('is_international', False) else 0.0
        
        # Bonus por ranking QS
        qs_bonus = 0.0
        if qs_rank is not None and qs_score is not None:
            qs_bonus = (qs_score / 100.0) * 0.2  # Hasta 20% extra por ranking QS
        
        # Combinar scores base
        ml_weight = self.ml_weights.get(university, 0.0)
        confidence = self.confidence_scores.get(university, 0.0)
        
        base_final_score = (
            base_score * (1 - confidence) + 
            ml_weight * confidence
        ) * ranking_weight * cost_multiplier + specialty_bonus + international_bonus + qs_bonus
        
        # Si hay programa específico, ajustar score
        if program:
            program_score = self.program_model.get_program_score(
                program=program,
                university=university,
                base_score=base_final_score
            )
            return program_score
            
        return min(1.0, max(0.0, base_final_score))
        
    def get_university_metrics(self, 
                             university: str, 
                             program: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene métricas detalladas de una universidad.
        
        Args:
            university: Nombre de la universidad
            program: Nombre del programa (opcional)
            
        Returns:
            Diccionario con métricas detalladas
        """
        metrics = {
            'base_score': 0.0,
            'qs_score': 0.0,
            'program_score': 0.0,
            'final_score': 0.0,
            'rankings': {},
            'bonuses': {}
        }
        
        # Obtener métricas base
        university_metrics = self.data_loader.get_university_metrics(university)
        if university_metrics:
            metrics['base_score'] = university_metrics['score']
            metrics['rankings']['national'] = university_metrics['ranking']
            
            # Obtener score QS
            qs_rank = university_metrics['qs_rank']
            qs_score = university_metrics['qs_score']
            if qs_rank is not None and qs_score is not None:
                metrics['qs_score'] = qs_score / 100.0
                metrics['rankings']['qs'] = qs_rank
                
        # Obtener score de programa
        if program:
            program_metrics = self.data_loader.get_program_metrics(program, university)
            if program_metrics:
                metrics['program_score'] = program_metrics['ranking']
                metrics['rankings']['program'] = program_metrics['ranking']
                
        # Calcular score final
        metrics['final_score'] = self.get_final_score(university, program)
        
        # Agregar bonuses
        if university_metrics:
            metrics['bonuses'] = {
                'specialty': 0.1 if program and self._is_specialty(university, program) else 0.0,
                'international': 0.1 if university_metrics.get('is_international', False) else 0.0,
                'qs': metrics['qs_score'] * 0.2 if metrics['qs_score'] > 0 else 0.0
            }
            
        return metrics 