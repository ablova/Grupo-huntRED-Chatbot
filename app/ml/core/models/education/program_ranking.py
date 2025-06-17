"""
Modelo para manejar rankings específicos por programa/carrera.
"""
from typing import Dict, List, Optional, Any, Union
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pandas as pd

class ProgramRankingModel:
    """Modelo para evaluar programas/carreras específicas."""
    
    def __init__(self):
        """Inicializa el modelo de rankings por programa."""
        self.program_rankings: Dict[str, Dict[str, Any]] = {}
        self.program_categories = {
            'engineering': [
                'Computer Science', 'Software Engineering', 'Data Science',
                'Mechanical Engineering', 'Electrical Engineering',
                'Civil Engineering', 'Industrial Engineering'
            ],
            'business': [
                'Business Administration', 'Finance', 'Marketing',
                'International Business', 'Economics'
            ],
            'health': [
                'Medicine', 'Nursing', 'Pharmacy',
                'Public Health', 'Biomedical Sciences'
            ],
            'arts': [
                'Architecture', 'Design', 'Fine Arts',
                'Music', 'Theater'
            ],
            'sciences': [
                'Physics', 'Chemistry', 'Biology',
                'Mathematics', 'Statistics'
            ]
        }
        
        # Pesos por categoría de programa
        self.category_weights = {
            'engineering': 1.0,
            'business': 0.9,
            'health': 0.95,
            'arts': 0.85,
            'sciences': 0.9
        }
        
        # Modelo ML
        self.ml_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def add_program_ranking(self, 
                          program: str,
                          university: str,
                          ranking: int,
                          category: str,
                          metrics: Dict[str, float]) -> None:
        """
        Agrega un ranking para un programa específico.
        
        Args:
            program: Nombre del programa
            university: Nombre de la universidad
            ranking: Ranking del programa
            category: Categoría del programa
            metrics: Métricas específicas del programa
        """
        if program not in self.program_rankings:
            self.program_rankings[program] = {}
            
        self.program_rankings[program][university] = {
            'ranking': ranking,
            'category': category,
            'metrics': metrics
        }
        
    def get_program_category(self, program: str) -> Optional[str]:
        """
        Obtiene la categoría de un programa.
        
        Args:
            program: Nombre del programa
            
        Returns:
            Categoría del programa o None si no se encuentra
        """
        for category, programs in self.program_categories.items():
            if program in programs:
                return category
        return None
        
    def get_program_ranking(self, 
                          program: str, 
                          university: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el ranking de un programa en una universidad.
        
        Args:
            program: Nombre del programa
            university: Nombre de la universidad
            
        Returns:
            Diccionario con información del ranking o None si no se encuentra
        """
        return self.program_rankings.get(program, {}).get(university)
        
    def get_program_score(self, 
                         program: str, 
                         university: str,
                         base_score: float) -> float:
        """
        Calcula el score de un programa considerando su categoría y métricas.
        
        Args:
            program: Nombre del programa
            university: Nombre de la universidad
            base_score: Score base de la universidad
            
        Returns:
            Score ajustado del programa (0-1)
        """
        # Obtener ranking del programa
        program_data = self.get_program_ranking(program, university)
        if program_data:
            ranking = program_data['ranking']
            category = program_data['category']
            metrics = program_data['metrics']
        else:
            # Si no hay ranking específico, usar la categoría
            category = self.get_program_category(program)
            if not category:
                return base_score  # Si no hay categoría, usar score base
            metrics = {}
                
        # Obtener peso de la categoría
        category_weight = self.category_weights.get(category, 0.8)
        
        # Ajustar score base según categoría
        adjusted_score = base_score * category_weight
        
        # Si hay ranking específico, ajustar más
        if program_data:
            # Normalizar ranking a score (1-100)
            ranking_score = max(0, 100 - (ranking - 1))
            
            # Calcular score de métricas
            metrics_score = self._calculate_metrics_score(metrics)
            
            # Combinar scores con pesos
            final_score = (
                adjusted_score * 0.4 +  # Score base ajustado
                (ranking_score / 100) * 0.3 +  # Ranking
                metrics_score * 0.3  # Métricas
            )
        else:
            final_score = adjusted_score
            
        return min(1.0, max(0.0, final_score))
        
    def _calculate_metrics_score(self, metrics: Dict[str, float]) -> float:
        """
        Calcula el score basado en métricas.
        
        Args:
            metrics: Diccionario con métricas
            
        Returns:
            Score de métricas (0-1)
        """
        if not metrics:
            return 0.5  # Score neutral por defecto
            
        # Pesos para cada métrica
        weights = {
            'quality': 0.3,
            'demand': 0.3,
            'salary': 0.2,
            'employability': 0.2
        }
        
        # Calcular score ponderado
        score = 0.0
        total_weight = 0.0
        
        for metric, value in metrics.items():
            if metric in weights:
                score += value * weights[metric]
                total_weight += weights[metric]
                
        if total_weight == 0:
            return 0.5
            
        return score / total_weight
        
    def get_top_programs(self, 
                        program: str, 
                        n: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las top N universidades para un programa.
        
        Args:
            program: Nombre del programa
            n: Número de universidades a retornar
            
        Returns:
            Lista de diccionarios con información de las universidades
        """
        if program not in self.program_rankings:
            return []
            
        # Ordenar universidades por ranking
        sorted_universities = sorted(
            self.program_rankings[program].items(),
            key=lambda x: x[1]['ranking']
        )[:n]
        
        return [
            {
                'university': name,
                'ranking': data['ranking'],
                'category': data['category'],
                'metrics': data['metrics']
            }
            for name, data in sorted_universities
        ]
        
    def train_ml_model(self, 
                      historical_data: pd.DataFrame,
                      target_column: str) -> None:
        """
        Entrena el modelo ML con datos históricos.
        
        Args:
            historical_data: DataFrame con datos históricos
            target_column: Columna objetivo
        """
        # Preparar features
        features = [
            'ranking', 'quality', 'demand', 'salary',
            'employability', 'faculty_student_ratio',
            'research_output', 'industry_connections'
        ]
        
        X = historical_data[features]
        y = historical_data[target_column]
        
        # Escalar features
        X_scaled = self.scaler.fit_transform(X)
        
        # Entrenar modelo
        self.ml_model.fit(X_scaled, y)
        self.is_trained = True
        
    def predict_score(self, 
                     program_data: Dict[str, float]) -> float:
        """
        Predice el score usando el modelo ML.
        
        Args:
            program_data: Diccionario con datos del programa
            
        Returns:
            Score predicho (0-1)
        """
        if not self.is_trained:
            return 0.5  # Score neutral por defecto
            
        # Preparar features
        features = [
            'ranking', 'quality', 'demand', 'salary',
            'employability', 'faculty_student_ratio',
            'research_output', 'industry_connections'
        ]
        
        X = np.array([[program_data.get(f, 0.0) for f in features]])
        X_scaled = self.scaler.transform(X)
        
        # Predecir
        score = self.ml_model.predict(X_scaled)[0]
        return min(1.0, max(0.0, score)) 