"""
Modelo de Machine Learning para análisis de compatibilidad cultural.

Este módulo implementa un modelo de ML que predice la compatibilidad
cultural basado en las puntuaciones de diferentes dimensiones culturales.
"""
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from typing import Dict, List, Any, Optional

class CulturalFitModel:
    """
    Modelo de ML para predecir compatibilidad cultural.
    
    Utiliza un Random Forest Regressor para predecir la compatibilidad
    cultural basado en las puntuaciones de diferentes dimensiones.
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
            X: Características (puntuaciones por dimensión)
            y: Etiquetas (puntuaciones de compatibilidad)
        """
        # Escalar características
        X_scaled = self.scaler.fit_transform(X)
        
        # Entrenar modelo
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Realiza predicciones de compatibilidad cultural.
        
        Args:
            X: Características a predecir
            
        Returns:
            Predicciones de compatibilidad
        """
        if not self.is_trained:
            # Si el modelo no está entrenado, usar regla simple
            return np.mean(X, axis=1)
            
        # Escalar características
        X_scaled = self.scaler.transform(X)
        
        # Realizar predicción
        predictions = self.model.predict(X_scaled)
        
        # Asegurar que las predicciones estén en el rango [0, 1]
        predictions = np.clip(predictions, 0, 1)
        
        return predictions
    
    def save(self, path: str) -> None:
        """
        Guarda el modelo entrenado.
        
        Args:
            path: Ruta donde guardar el modelo
        """
        if not self.is_trained:
            raise ValueError("No se puede guardar un modelo no entrenado")
            
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Guardar modelo y scaler
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
            
        # Cargar modelo y scaler
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
            
        # Obtener nombres de características
        feature_names = [
            'innovation',
            'collaboration',
            'adaptability',
            'results_orientation',
            'customer_focus',
            'integrity',
            'diversity',
            'learning'
        ]
        
        # Obtener importancia de características
        importance = self.model.feature_importances_
        
        # Crear diccionario
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
            
        # Realizar predicciones
        predictions = self.predict(X)
        
        # Calcular métricas
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
            
        # Escalar características
        X_scaled = self.scaler.transform(X)
        
        # Actualizar modelo
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