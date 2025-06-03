"""
Modelo de Machine Learning para análisis de competencias profesionales.

Este módulo implementa un modelo de ML que evalúa las competencias y habilidades
profesionales basado en diferentes dimensiones de evaluación.
"""
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from typing import Dict, List, Any, Optional

class ProfessionalModel:
    """
    Modelo de ML para evaluación de competencias profesionales.
    
    Utiliza un Random Forest Regressor para evaluar las competencias y habilidades
    profesionales basado en diferentes dimensiones de evaluación.
    """
    
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Entrena el modelo con datos históricos.
        
        Args:
            X: Características (evaluaciones por competencia)
            y: Etiquetas (nivel de competencia)
        """
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
    def predict(self, X: np.ndarray) -> Dict[str, Dict[str, float]]:
        """
        Realiza predicciones de competencias profesionales.
        
        Args:
            X: Características a predecir
            
        Returns:
            Diccionario con las competencias y sus niveles
        """
        if not self.is_trained:
            return self._default_predictions()
            
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        competencies = {
            'technical_skills': {
                'level': float(predictions[0]),
                'confidence': float(self.model.predict_proba(X_scaled)[0][0])
            },
            'soft_skills': {
                'level': float(predictions[1]),
                'confidence': float(self.model.predict_proba(X_scaled)[1][0])
            },
            'leadership': {
                'level': float(predictions[2]),
                'confidence': float(self.model.predict_proba(X_scaled)[2][0])
            },
            'innovation': {
                'level': float(predictions[3]),
                'confidence': float(self.model.predict_proba(X_scaled)[3][0])
            }
        }
        
        return competencies
    
    def _default_predictions(self) -> Dict[str, Dict[str, float]]:
        """Retorna predicciones por defecto cuando el modelo no está entrenado."""
        return {
            'technical_skills': {'level': 0.5, 'confidence': 0.0},
            'soft_skills': {'level': 0.5, 'confidence': 0.0},
            'leadership': {'level': 0.5, 'confidence': 0.0},
            'innovation': {'level': 0.5, 'confidence': 0.0}
        }
    
    def save(self, path: str) -> None:
        """
        Guarda el modelo entrenado.
        
        Args:
            path: Ruta donde guardar el modelo
        """
        if not self.is_trained:
            raise ValueError("No se puede guardar un modelo no entrenado")
            
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler
        }
        joblib.dump(model_data, path)
        
    def load(self, path: str) -> None:
        """
        Carga un modelo guardado.
        
        Args:
            path: Ruta del modelo a cargar
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"No se encontró el modelo en {path}")
            
        model_data = joblib.load(path)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.is_trained = True
        
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Obtiene la importancia de cada característica.
        
        Returns:
            Diccionario con la importancia de cada dimensión
        """
        if not self.is_trained:
            return {}
            
        feature_names = [
            'technical_knowledge',
            'problem_solving',
            'communication',
            'teamwork',
            'leadership_potential',
            'innovation_capacity',
            'adaptability',
            'project_management'
        ]
        
        importance = self.model.feature_importances_
        return dict(zip(feature_names, importance))
        
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Evalúa el rendimiento del modelo.
        
        Args:
            X: Características de prueba
            y: Etiquetas reales
            
        Returns:
            Métricas de evaluación
        """
        if not self.is_trained:
            return {
                'error': 'Modelo no entrenado'
            }
            
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        mse = np.mean((y - predictions) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(y - predictions))
        
        return {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae)
        }
        
    def update(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Actualiza el modelo con nuevos datos.
        
        Args:
            X: Nuevas características
            y: Nuevas etiquetas
        """
        if not self.is_trained:
            self.train(X, y)
            return
            
        X_scaled = self.scaler.transform(X)
        self.model.fit(X_scaled, y, xgb_model=self.model.get_booster())
        
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre el modelo.
        
        Returns:
            Diccionario con información del modelo
        """
        return {
            'is_trained': self.is_trained,
            'n_estimators': self.model.n_estimators,
            'max_depth': self.model.max_depth,
            'feature_importance': self.get_feature_importance() if self.is_trained else {}
        } 