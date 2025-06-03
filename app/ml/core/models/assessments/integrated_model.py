"""
Modelo de Machine Learning integrado para análisis completo.

Este módulo implementa un modelo de ML que integra los resultados de los diferentes
modelos (personalidad, cultural y profesional) para proporcionar un análisis completo.
"""
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from typing import Dict, List, Any, Optional

from app.ml.core.models.assessments.personality_model import PersonalityModel
from app.ml.core.models.assessments.cultural_fit_model import CulturalFitModel
from app.ml.core.models.assessments.professional_model import ProfessionalModel

class IntegratedModel:
    """
    Modelo de ML para análisis integrado.
    
    Integra los resultados de los modelos de personalidad, cultural y profesional
    para proporcionar un análisis completo y recomendaciones.
    """
    
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Inicializar modelos base
        self.personality_model = PersonalityModel()
        self.cultural_model = CulturalFitModel()
        self.professional_model = ProfessionalModel()
        
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Entrena el modelo con datos históricos.
        
        Args:
            X: Características combinadas de todos los modelos
            y: Etiquetas (puntuaciones de éxito)
        """
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
    def predict(self, personality_data: np.ndarray, 
                cultural_data: np.ndarray,
                professional_data: np.ndarray) -> Dict[str, Any]:
        """
        Realiza predicciones integradas.
        
        Args:
            personality_data: Datos de personalidad
            cultural_data: Datos de compatibilidad cultural
            professional_data: Datos profesionales
            
        Returns:
            Diccionario con análisis integrado y recomendaciones
        """
        # Obtener predicciones de modelos base
        personality_results = self.personality_model.predict(personality_data)
        cultural_results = self.cultural_model.predict(cultural_data)
        professional_results = self.professional_model.predict(professional_data)
        
        # Combinar resultados
        combined_features = self._combine_features(
            personality_results,
            cultural_results,
            professional_results
        )
        
        if not self.is_trained:
            return self._default_predictions(
                personality_results,
                cultural_results,
                professional_results
            )
            
        # Realizar predicción integrada
        X_scaled = self.scaler.transform(combined_features.reshape(1, -1))
        overall_score = float(self.model.predict(X_scaled)[0])
        
        return {
            'overall_score': overall_score,
            'personality_analysis': personality_results,
            'cultural_fit': cultural_results,
            'professional_competencies': professional_results,
            'recommendations': self._generate_recommendations(
                personality_results,
                cultural_results,
                professional_results,
                overall_score
            )
        }
    
    def _combine_features(self, personality: Dict[str, float],
                         cultural: np.ndarray,
                         professional: Dict[str, Dict[str, float]]) -> np.ndarray:
        """Combina las características de los diferentes modelos."""
        features = []
        
        # Añadir características de personalidad
        features.extend(personality.values())
        
        # Añadir características culturales
        features.extend(cultural)
        
        # Añadir características profesionales
        for comp in professional.values():
            features.extend([comp['level'], comp['confidence']])
            
        return np.array(features)
    
    def _default_predictions(self, personality: Dict[str, float],
                           cultural: np.ndarray,
                           professional: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Retorna predicciones por defecto cuando el modelo no está entrenado."""
        return {
            'overall_score': 0.5,
            'personality_analysis': personality,
            'cultural_fit': cultural,
            'professional_competencies': professional,
            'recommendations': {
                'development_areas': [],
                'strengths': [],
                'next_steps': []
            }
        }
    
    def _generate_recommendations(self, personality: Dict[str, float],
                                cultural: np.ndarray,
                                professional: Dict[str, Dict[str, float]],
                                overall_score: float) -> Dict[str, List[str]]:
        """Genera recomendaciones basadas en los resultados."""
        recommendations = {
            'development_areas': [],
            'strengths': [],
            'next_steps': []
        }
        
        # Analizar personalidad
        for trait, score in personality.items():
            if score < 0.4:
                recommendations['development_areas'].append(
                    f"Desarrollar {trait} mediante coaching y práctica"
                )
            elif score > 0.7:
                recommendations['strengths'].append(
                    f"Fuerte en {trait}, aprovechar en roles que lo requieran"
                )
        
        # Analizar compatibilidad cultural
        if np.mean(cultural) < 0.5:
            recommendations['development_areas'].append(
                "Trabajar en la adaptación cultural"
            )
        
        # Analizar competencias profesionales
        for comp, data in professional.items():
            if data['level'] < 0.4:
                recommendations['development_areas'].append(
                    f"Mejorar {comp} mediante capacitación específica"
                )
            elif data['level'] > 0.7:
                recommendations['strengths'].append(
                    f"Experto en {comp}, considerar roles de liderazgo"
                )
        
        # Generar próximos pasos
        if overall_score > 0.7:
            recommendations['next_steps'].append(
                "Considerar roles de mayor responsabilidad"
            )
        elif overall_score < 0.4:
            recommendations['next_steps'].append(
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
            
        feature_names = (
            [f'personality_{trait}' for trait in ['extraversion', 'agreeableness', 
                                                'conscientiousness', 'emotional_stability', 
                                                'openness']] +
            [f'cultural_{i}' for i in range(8)] +
            [f'professional_{comp}_{metric}' 
             for comp in ['technical_skills', 'soft_skills', 'leadership', 'innovation']
             for metric in ['level', 'confidence']]
        )
        
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