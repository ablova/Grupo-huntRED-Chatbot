"""
Modelo de Machine Learning para análisis de talento.

Este módulo implementa un modelo de ML que evalúa el potencial y desarrollo
profesional basado en múltiples dimensiones de talento.
"""
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from typing import Dict, List, Any, Optional

class TalentModel:
    """
    Modelo de ML para análisis de talento.
    
    Utiliza un Random Forest Regressor para evaluar el potencial y desarrollo
    profesional basado en múltiples dimensiones de talento.
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
            X: Características (evaluaciones por dimensión)
            y: Etiquetas (puntuaciones de potencial)
        """
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
    def predict(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Realiza predicciones de potencial y desarrollo.
        
        Args:
            X: Características a predecir
            
        Returns:
            Diccionario con análisis de talento y plan de desarrollo
        """
        if not self.is_trained:
            return self._default_predictions()
            
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        # Calcular dimensiones de talento
        talent_dimensions = {
            'learning_agility': float(predictions[0]),
            'leadership_potential': float(predictions[1]),
            'innovation_capacity': float(predictions[2]),
            'strategic_thinking': float(predictions[3]),
            'execution_excellence': float(predictions[4])
        }
        
        # Calcular puntuación general
        overall_score = float(np.mean(list(talent_dimensions.values())))
        
        return {
            'overall_potential': overall_score,
            'talent_dimensions': talent_dimensions,
            'development_plan': self._generate_development_plan(talent_dimensions),
            'career_recommendations': self._generate_career_recommendations(
                talent_dimensions,
                overall_score
            )
        }
    
    def _default_predictions(self) -> Dict[str, Any]:
        """Retorna predicciones por defecto cuando el modelo no está entrenado."""
        return {
            'overall_potential': 0.5,
            'talent_dimensions': {
                'learning_agility': 0.5,
                'leadership_potential': 0.5,
                'innovation_capacity': 0.5,
                'strategic_thinking': 0.5,
                'execution_excellence': 0.5
            },
            'development_plan': {
                'short_term': [],
                'medium_term': [],
                'long_term': []
            },
            'career_recommendations': []
        }
    
    def _generate_development_plan(self, dimensions: Dict[str, float]) -> Dict[str, List[str]]:
        """Genera un plan de desarrollo basado en las dimensiones de talento."""
        plan = {
            'short_term': [],
            'medium_term': [],
            'long_term': []
        }
        
        # Plan a corto plazo (3-6 meses)
        for dim, score in dimensions.items():
            if score < 0.4:
                plan['short_term'].append(
                    f"Capacitación básica en {dim.replace('_', ' ')}"
                )
            elif score > 0.7:
                plan['short_term'].append(
                    f"Mentoría en {dim.replace('_', ' ')} para otros"
                )
        
        # Plan a medio plazo (6-12 meses)
        if np.mean(list(dimensions.values())) < 0.5:
            plan['medium_term'].append(
                "Programa de desarrollo acelerado"
            )
        else:
            plan['medium_term'].append(
                "Proyectos de alto impacto"
            )
        
        # Plan a largo plazo (1-2 años)
        if dimensions['leadership_potential'] > 0.7:
            plan['long_term'].append(
                "Programa de liderazgo ejecutivo"
            )
        if dimensions['strategic_thinking'] > 0.7:
            plan['long_term'].append(
                "Roles estratégicos en la organización"
            )
        
        return plan
    
    def _generate_career_recommendations(self, dimensions: Dict[str, float],
                                       overall_score: float) -> List[str]:
        """Genera recomendaciones de carrera basadas en el perfil de talento."""
        recommendations = []
        
        # Recomendaciones basadas en dimensiones específicas
        if dimensions['innovation_capacity'] > 0.7:
            recommendations.append(
                "Considerar roles en innovación y desarrollo de productos"
            )
        if dimensions['execution_excellence'] > 0.7:
            recommendations.append(
                "Roles en gestión de proyectos y operaciones"
            )
        
        # Recomendaciones basadas en puntuación general
        if overall_score > 0.7:
            recommendations.append(
                "Considerar programa de alto potencial"
            )
        elif overall_score < 0.4:
            recommendations.append(
                "Enfocarse en desarrollo de competencias básicas"
            )
        
        return recommendations
    
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
            'technical_expertise',
            'problem_solving',
            'communication',
            'teamwork',
            'leadership',
            'innovation',
            'adaptability',
            'strategic_vision',
            'execution',
            'learning_capacity'
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