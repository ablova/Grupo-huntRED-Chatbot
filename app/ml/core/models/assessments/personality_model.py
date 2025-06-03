"""
Modelo de Machine Learning para análisis de personalidad TIPI.

Este módulo implementa un modelo de ML que analiza los rasgos de personalidad
basado en el inventario de personalidad TIPI (Ten-Item Personality Inventory).
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os
from typing import Dict, List, Any, Optional

class PersonalityModel:
    """
    Modelo de ML para análisis de personalidad TIPI.
    
    Utiliza un Random Forest Classifier para clasificar los rasgos de personalidad
    basado en las respuestas al cuestionario TIPI.
    """
    
    def __init__(self):
        self.model = RandomForestClassifier(
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
            X: Características (respuestas al TIPI)
            y: Etiquetas (rasgos de personalidad)
        """
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
    def predict(self, X: np.ndarray) -> Dict[str, float]:
        """
        Realiza predicciones de rasgos de personalidad.
        
        Args:
            X: Características a predecir
            
        Returns:
            Diccionario con los rasgos de personalidad y sus puntuaciones
        """
        if not self.is_trained:
            return self._default_predictions()
            
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict_proba(X_scaled)
        
        traits = ['extraversion', 'agreeableness', 'conscientiousness', 
                 'emotional_stability', 'openness']
        
        return dict(zip(traits, predictions[0]))
    
    def _default_predictions(self) -> Dict[str, float]:
        """Retorna predicciones por defecto cuando el modelo no está entrenado."""
        return {
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'conscientiousness': 0.5,
            'emotional_stability': 0.5,
            'openness': 0.5
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
            Diccionario con la importancia de cada pregunta TIPI
        """
        if not self.is_trained:
            return {}
            
        feature_names = [f'tipi_q{i+1}' for i in range(10)]
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
        
        accuracy = np.mean(predictions == y)
        
        return {
            'accuracy': float(accuracy)
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