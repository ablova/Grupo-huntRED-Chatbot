"""
Succession Analyzer - Módulo de análisis para planes de sucesión.

Este módulo proporciona capacidades de análisis predictivo para evaluar
la preparación de los candidatos en los planes de sucesión.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
import joblib

from ....models import Employee, Position, Assessment
from ..base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class SuccessionReadiness:
    """Resultado del análisis de preparación para sucesión."""
    readiness_score: float  # 0-100
    readiness_level: str     # 'Ready Now', '1-2 Years', '3-5 Years', 'Not Feasible'
    critical_gaps: List[str]
    development_areas: Dict[str, str]  # area: recomendación
    predicted_performance: Optional[float] = None  # Predicción de rendimiento 0-1
    risk_factors: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class SuccessionAnalyzer(BaseAnalyzer):
    """Analizador para planes de sucesión."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Inicializa el analizador de sucesión.
        
        Args:
            model_path: Ruta al modelo pre-entrenado (opcional)
        """
        super().__init__()
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'years_experience',
            'performance_rating',
            'potential_rating',
            'leadership_skills',
            'technical_skills',
            'strategic_thinking',
            'business_acumen',
            'change_management',
            'team_development',
            'communication_skills',
            'results_orientation'
        ]
        self.target_names = ['Not Feasible', '3-5 Years', '1-2 Years', 'Ready Now']
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def train(
        self, 
        X: np.ndarray, 
        y: np.ndarray,
        model_type: str = 'random_forest',
        **kwargs
    ) -> Dict[str, float]:
        """
        Entrena un modelo de clasificación para predecir la preparación.
        
        Args:
            X: Matriz de características
            y: Vector de etiquetas
            model_type: Tipo de modelo a utilizar ('random_forest' o 'gradient_boosting')
            **kwargs: Parámetros adicionales para el modelo
            
        Returns:
            Dict con métricas de rendimiento
        """
        try:
            # Validar entradas
            if X.shape[0] != y.shape[0]:
                raise ValueError("X e y deben tener el mismo número de muestras")
                
            # Escalar características
            X_scaled = self.scaler.fit_transform(X)
            
            # Seleccionar y entrenar modelo
            if model_type == 'random_forest':
                model = RandomForestClassifier(
                    n_estimators=kwargs.get('n_estimators', 100),
                    max_depth=kwargs.get('max_depth', None),
                    random_state=kwargs.get('random_state', 42)
                )
            elif model_type == 'gradient_boosting':
                model = GradientBoostingClassifier(
                    n_estimators=kwargs.get('n_estimators', 100),
                    learning_rate=kwargs.get('learning_rate', 0.1),
                    max_depth=kwargs.get('max_depth', 3),
                    random_state=kwargs.get('random_state', 42)
                )
            else:
                raise ValueError(f"Tipo de modelo no soportado: {model_type}")
            
            # Entrenar modelo
            model.fit(X_scaled, y)
            self.model = model
            
            # Evaluar modelo
            y_pred = model.predict(X_scaled)
            accuracy = accuracy_score(y, y_pred)
            report = classification_report(y, y_pred, target_names=self.target_names, output_dict=True)
            
            return {
                'accuracy': accuracy,
                'report': report,
                'model_type': model_type,
                'feature_importance': dict(zip(self.feature_names, model.feature_importances_))
            }
            
        except Exception as e:
            logger.error(f"Error en entrenamiento del modelo: {str(e)}", exc_info=True)
            raise
    
    def predict_readiness(
        self, 
        candidate_features: Dict[str, float],
        position_requirements: Dict[str, float]
    ) -> Tuple[str, float]:
        """
        Predice el nivel de preparación de un candidato.
        
        Args:
            candidate_features: Características del candidato
            position_requirements: Requisitos del puesto
            
        Returns:
            Tupla con (nivel_preparacion, probabilidad)
        """
        if self.model is None:
            raise ValueError("El modelo no ha sido entrenado o cargado")
        
        try:
            # Preparar características
            X = self._prepare_features(candidate_features, position_requirements)
            
            # Escalar características
            X_scaled = self.scaler.transform(X.reshape(1, -1))
            
            # Predecir
            prediction = self.model.predict(X_scaled)[0]
            probas = self.model.predict_proba(X_scaled)[0]
            
            # Obtener nivel de preparación y probabilidad
            readiness_level = self.target_names[prediction]
            confidence = probas[prediction]
            
            return readiness_level, confidence
            
        except Exception as e:
            logger.error(f"Error en predicción de preparación: {str(e)}", exc_info=True)
            return "Not Feasible", 0.0
    
    def analyze_succession_readiness(
        self,
        candidate_id: str,
        position_id: str,
        assessment_data: Dict[str, Any],
        org_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analiza la preparación de un candidato para un puesto objetivo.
        
        Args:
            candidate_id: ID del candidato
            position_id: ID del puesto objetivo
            assessment_data: Datos del assessment
            org_context: Contexto organizacional opcional
            
        Returns:
            Dict con el análisis de preparación
        """
        try:
            # Obtener características del candidato (simulado)
            candidate_features = self._extract_candidate_features(candidate_id, assessment_data)
            
            # Obtener requisitos del puesto (simulado)
            position_requirements = self._extract_position_requirements(position_id)
            
            # Predecir nivel de preparación
            readiness_level, confidence = self.predict_readiness(
                candidate_features, 
                position_requirements
            )
            
            # Calcular brechas críticas
            critical_gaps = self._identify_critical_gaps(
                candidate_features, 
                position_requirements
            )
            
            # Generar áreas de desarrollo
            development_areas = self._generate_development_areas(
                candidate_features,
                position_requirements,
                critical_gaps
            )
            
            # Calcular puntuación de preparación (0-100)
            readiness_score = self._calculate_readiness_score(
                readiness_level, 
                confidence,
                len(critical_gaps)
            )
            
            # Identificar factores de riesgo
            risk_factors = self._identify_risk_factors(
                candidate_features,
                position_requirements,
                org_context or {}
            )
            
            # Crear resultado
            result = SuccessionReadiness(
                readiness_score=readiness_score,
                readiness_level=readiness_level,
                critical_gaps=critical_gaps,
                development_areas=development_areas,
                predicted_performance=confidence,
                risk_factors=risk_factors
            )
            
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Error en análisis de preparación: {str(e)}", exc_info=True)
            # Retornar un resultado por defecto en caso de error
            return SuccessionReadiness(
                readiness_score=0,
                readiness_level='Not Feasible',
                critical_gaps=["Error en el análisis"],
                development_areas={"error": "No se pudo completar el análisis"},
                risk_factors=["Error técnico"]
            ).to_dict()
    
    def _prepare_features(
        self, 
        candidate_features: Dict[str, float],
        position_requirements: Dict[str, float]
    ) -> np.ndarray:
        """
        Prepara las características para el modelo.
        
        Args:
            candidate_features: Características del candidato
            position_requirements: Requisitos del puesto
            
        Returns:
            Matriz de características
        """
        # Combinar características y requisitos
        features = []
        
        for feat in self.feature_names:
            # Normalizar valor entre 0 y 1 basado en requisitos
            if feat in position_requirements and position_requirements[feat] > 0:
                norm_value = min(candidate_features.get(feat, 0) / position_requirements[feat], 1.0)
            else:
                norm_value = candidate_features.get(feat, 0) / 5.0  # Asumir escala 0-5
                
            features.append(norm_value)
        
        return np.array(features)
    
    def _extract_candidate_features(
        self, 
        candidate_id: str, 
        assessment_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Extrae características del candidato a partir de los datos del assessment.
        
        Args:
            candidate_id: ID del candidato
            assessment_data: Datos del assessment
            
        Returns:
            Dict con las características del candidato
        """
        # En una implementación real, esto extraería datos de la base de datos
        # y procesaría los resultados del assessment
        
        # Ejemplo simplificado
        return {
            'years_experience': assessment_data.get('years_experience', 3),
            'performance_rating': assessment_data.get('performance_rating', 3.5),
            'potential_rating': assessment_data.get('potential_rating', 3.0),
            'leadership_skills': assessment_data.get('leadership_skills', 3.0),
            'technical_skills': assessment_data.get('technical_skills', 3.5),
            'strategic_thinking': assessment_data.get('strategic_thinking', 2.5),
            'business_acumen': assessment_data.get('business_acumen', 3.0),
            'change_management': assessment_data.get('change_management', 2.5),
            'team_development': assessment_data.get('team_development', 3.0),
            'communication_skills': assessment_data.get('communication_skills', 3.5),
            'results_orientation': assessment_data.get('results_orientation', 3.5)
        }
    
    def _extract_position_requirements(self, position_id: str) -> Dict[str, float]:
        """
        Extrae los requisitos del puesto.
        
        Args:
            position_id: ID del puesto
            
        Returns:
            Dict con los requisitos del puesto
        """
        # En una implementación real, esto consultaría la base de datos
        # Para este ejemplo, usamos valores predeterminados basados en el nivel del puesto
        
        # Determinar nivel del puesto basado en el ID (simplificado)
        position_level = "manager"  # Por defecto
        if "dir" in position_id.lower():
            position_level = "director"
        elif "c_level" in position_id.lower() or "vp" in position_id.lower() or "chief" in position_id.lower():
            position_level = "c_level"
        
        # Requisitos por nivel (ejemplo simplificado)
        requirements = {
            'manager': {
                'leadership_skills': 4.0,
                'technical_skills': 4.5,
                'strategic_thinking': 3.0,
                'business_acumen': 3.5,
                'change_management': 3.0,
                'team_development': 4.0,
                'communication_skills': 4.0,
                'results_orientation': 4.5
            },
            'director': {
                'leadership_skills': 4.5,
                'technical_skills': 4.0,
                'strategic_thinking': 4.5,
                'business_acumen': 4.5,
                'change_management': 4.0,
                'team_development': 4.0,
                'communication_skills': 4.5,
                'results_orientation': 4.5
            },
            'c_level': {
                'leadership_skills': 5.0,
                'technical_skills': 3.5,
                'strategic_thinking': 5.0,
                'business_acumen': 5.0,
                'change_management': 4.5,
                'team_development': 4.5,
                'communication_skills': 5.0,
                'results_orientation': 5.0
            }
        }
        
        return requirements.get(position_level, requirements['manager'])
    
    def _identify_critical_gaps(
        self, 
        candidate_features: Dict[str, float],
        position_requirements: Dict[str, float],
        threshold: float = 0.7
    ) -> List[str]:
        """
        Identifica brechas críticas entre las habilidades del candidato y los requisitos.
        
        Args:
            candidate_features: Características del candidato
            position_requirements: Requisitos del puesto
            threshold: Umbral para considerar una brecha como crítica (0-1)
            
        Returns:
            Lista de brechas críticas
        """
        critical_gaps = []
        
        for skill, req_level in position_requirements.items():
            candidate_level = candidate_features.get(skill, 0)
            
            # Calcular brecha normalizada (0-1)
            gap = max(0, (req_level - candidate_level) / 5.0)  # Asumir escala 0-5
            
            if gap >= threshold:
                critical_gaps.append(skill)
        
        return critical_gaps
    
    def _generate_development_areas(
        self,
        candidate_features: Dict[str, float],
        position_requirements: Dict[str, float],
        critical_gaps: List[str]
    ) -> Dict[str, str]:
        """
        Genera recomendaciones de desarrollo basadas en las brechas identificadas.
        
        Args:
            candidate_features: Características del candidato
            position_requirements: Requisitos del puesto
            critical_gaps: Lista de brechas críticas
            
        Returns:
            Dict con áreas de desarrollo y recomendaciones
        """
        development_areas = {}
        
        # Mapeo de habilidades a recomendaciones
        recommendations = {
            'leadership_skills': [
                "Participar en el programa de liderazgo de la empresa",
                "Tomar un curso de liderazgo situacional",
                "Buscar un mentor en un puesto de liderazgo senior"
            ],
            'technical_skills': [
                "Completar certificaciones técnicas relevantes",
                "Participar en proyectos que requieran estas habilidades",
                "Tomar cursos en línea de actualización técnica"
            ],
            'strategic_thinking': [
                "Participar en la planificación estratégica del departamento",
                "Tomar un curso de pensamiento estratégico",
                "Leer libros sobre estrategia empresarial"
            ],
            'business_acumen': [
                "Tomar un curso de fundamentos de negocios",
                "Participar en reuniones de revisión de negocio",
                "Leer informes financieros y de la industria"
            ],
            'change_management': [
                "Tomar una certificación en gestión del cambio",
                "Participar en iniciativas de transformación",
                "Aprender metodologías ágiles"
            ],
            'team_development': [
                "Tomar un curso de desarrollo de equipos",
                "Participar en programas de mentoría",
                "Aprender técnicas de coaching"
            ],
            'communication_skills': [
                "Tomar un curso de comunicación efectiva",
                "Practicar presentaciones ejecutivas",
                "Recibir entrenamiento en comunicación asertiva"
            ],
            'results_orientation': [
                "Establecer objetivos SMART personales",
                "Tomar un curso de gestión por resultados",
                "Aprender técnicas de priorización"
            ]
        }
        
        # Generar recomendaciones para cada brecha crítica
        for gap in critical_gaps:
            if gap in recommendations:
                development_areas[gap] = {
                    'current_level': candidate_features.get(gap, 0),
                    'required_level': position_requirements.get(gap, 0),
                    'recommendations': recommendations[gap],
                    'priority': 'Alta'
                }
        
        return development_areas
    
    def _calculate_readiness_score(
        self,
        readiness_level: str,
        confidence: float,
        gap_count: int,
        max_gaps: int = 5
    ) -> float:
        """
        Calcula una puntuación de preparación (0-100).
        
        Args:
            readiness_level: Nivel de preparación
            confidence: Nivel de confianza de la predicción (0-1)
            gap_count: Número de brechas críticas
            max_gaps: Número máximo de brechas para normalizar
            
        Returns:
            Puntuación de preparación (0-100)
        """
        # Peso base según el nivel de preparación
        level_weights = {
            'Ready Now': 1.0,
            '1-2 Years': 0.75,
            '3-5 Years': 0.5,
            'Not Feasible': 0.25
        }
        
        # Calcular puntuación base
        base_score = level_weights.get(readiness_level, 0) * 100
        
        # Ajustar por confianza
        adjusted_score = base_score * confidence
        
        # Penalizar por brechas (máximo 30% de penalización)
        gap_penalty = min(gap_count / max_gaps, 1.0) * 30
        final_score = max(0, adjusted_score - gap_penalty)
        
        return round(final_score, 2)
    
    def _identify_risk_factors(
        self,
        candidate_features: Dict[str, float],
        position_requirements: Dict[str, float],
        org_context: Dict[str, Any]
    ) -> List[str]:
        """
        Identifica factores de riesgo para la sucesión.
        
        Args:
            candidate_features: Características del candidato
            position_requirements: Requisitos del puesto
            org_context: Contexto organizacional
            
        Returns:
            Lista de factores de riesgo
        """
        risk_factors = []
        
        # Riesgo por brechas significativas
        for skill, req_level in position_requirements.items():
            candidate_level = candidate_features.get(skill, 0)
            if req_level - candidate_level >= 2:  # Brecha significativa
                risk_factors.append(f"Brecha significativa en {skill}")
        
        # Riesgo por falta de experiencia
        if candidate_features.get('years_experience', 0) < 3:
            risk_factors.append("Experiencia limitada en el rol")
            
        # Riesgo por falta de preparación para el siguiente nivel
        if candidate_features.get('readiness_level') in ['3-5 Years', 'Not Feasible']:
            risk_factors.append("Tiempo prolongado de preparación requerido")
            
        # Riesgos del contexto organizacional
        if org_context.get('high_turnover', False):
            risk_factors.append("Alta rotación en el departamento")
            
        if org_context.get('recent_restructuring', False):
            risk_factors.append("Reestructuración organizacional reciente")
            
        # Si no hay factores de riesgo, agregar uno genérico
        if not risk_factors:
            risk_factors.append("Sin riesgos significativos identificados")
            
        return risk_factors
    
    def load_model(self, model_path: str) -> None:
        """
        Carga un modelo pre-entrenado desde disco.
        
        Args:
            model_path: Ruta al archivo del modelo
        """
        try:
            # Cargar el modelo y el escalador
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            logger.info(f"Modelo cargado exitosamente desde {model_path}")
        except Exception as e:
            logger.error(f"Error al cargar el modelo: {str(e)}", exc_info=True)
            raise
    
    def save_model(self, model_path: str) -> None:
        """
        Guarda el modelo actual en disco.
        
        Args:
            model_path: Ruta donde guardar el modelo
        """
        if self.model is None:
            raise ValueError("No hay modelo entrenado para guardar")
            
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'target_names': self.target_names
            }
            joblib.dump(model_data, model_path)
            logger.info(f"Modelo guardado exitosamente en {model_path}")
        except Exception as e:
            logger.error(f"Error al guardar el modelo: {str(e)}", exc_info=True)
            raise
